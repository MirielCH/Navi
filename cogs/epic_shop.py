# epic_shop.py

from datetime import timedelta
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands
from datetime import timedelta

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings


class EpicShopCog(commands.Cog):
    """Cog that contains the epic shop detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_footer = message_fields = icon_url = message_description = ''
            if embed.description is not None:
                message_description = embed.description
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            for field in embed.fields:
                message_fields = f'{message_fields}\n{str(field.value)}'.strip()
            if embed.footer is not None: message_footer = str(embed.footer.text)
            
            # Epic shop
            search_strings = [
                " — epic shop", #All languages
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings)
                and 'special deal' in message_fields.lower()):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_EPIC_SHOP,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in epic shop message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_epic_shop.enabled: return
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                midnight_tomorrow = midnight_today + timedelta(days=1)
                reminder_created = False
                for field in message.embeds[0].fields:
                    shop_item_data_match = re.search(r'__\*\*(.+?)\*\*__.+`(\d+?)/(\d+?)`.+\*\*(.+?)\*\*', field.value.lower(),
                                                    re.DOTALL)
                    if not shop_item_data_match: continue
                    item_name = shop_item_data_match.group(1).strip()
                    item_amount_bought = int(shop_item_data_match.group(2))
                    item_amount_available = int(shop_item_data_match.group(3))
                    timestring = shop_item_data_match.group(4)
                    activity = item_name.replace(' ','-')
                    if item_amount_bought < item_amount_available:
                        try:
                            epic_shop_reminder = await reminders.get_user_reminder(user.id, f'epic-shop-{activity}')
                            await epic_shop_reminder.delete()
                        except:
                            pass
                        continue
                    time_left_timestring = await functions.parse_timestring_to_timedelta(timestring)
                    bot_answer_time = message.edited_at if message.edited_at else message.created_at
                    current_time = utils.utcnow()
                    time_elapsed = current_time - bot_answer_time
                    time_left_timestring -= time_elapsed
                    time_left = midnight_tomorrow - current_time + timedelta(seconds=random.randint(0, 600))
                    if time_left_timestring >= timedelta(days=1):
                        time_left = time_left + timedelta(days=time_left_timestring.days)
                    emoji = emojis.EPIC_SHOP_EMOJIS.get(activity, '')
                    user_command = await functions.get_slash_command(user_settings, 'epic shop')
                    reminder_message = (
                        user_settings.alert_epic_shop.message
                        .replace('{epic_shop_emoji}', emoji)
                        .replace('{epic_shop_item}', item_name)
                        .replace('{command}', user_command)
                    ).replace('  ', ' ')
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, f'epic-shop-{activity}', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    reminder_created = True
                if reminder_created:
                    await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            
            # Maxed purchase message, only works without slash
            search_strings = [
                'maxed the purchases', #All languages
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_command_message = None
                user = message.mentions[0]
                user_command_message = (
                    await messages.find_message(message.channel.id, regex.COMMAND_EPIC_SHOP_BUY, user=user)
                )
                if user_command_message is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for the maxed purchase message.',
                                        message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_epic_shop.enabled: return
                item_name_match = re.search(r'\bbuy\b\s+\b(.+?)$', user_command_message.content.lower())
                item_name = re.sub(r'\d+', '', item_name_match.group(1))
                timestring_match = re.search(r'🕓\s\*\*(.+?)\*\*', message.content.lower())
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                time_left += timedelta(seconds=random.randint(0, 600))
                activity = item_name.replace(' ','-')
                emoji = emojis.EPIC_SHOP_EMOJIS.get(activity, '')
                user_command = await functions.get_slash_command(user_settings, 'epic shop')
                reminder_message = (
                    user_settings.alert_epic_shop.message
                    .replace('{epic_shop_emoji}', emoji)
                    .replace('{epic_shop_item}', item_name)
                    .replace('{command}', user_command)
                )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, f'epic-shop-{activity}', time_left,
                                                            message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                    

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(EpicShopCog(bot))