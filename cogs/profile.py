# profile.py

from math import floor
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class ProfileCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
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
            embed_author = embed_field0_value = embed_footer = icon_url = embed_field_values = ''
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                embed_field0_value = str(embed.fields[0].value)
            for field in embed.fields:
                embed_field_values = f'{embed_field_values}\n{field.value}'.strip()
            if embed.footer:
                embed_footer = embed.footer.text

            # Update settings from profile
            search_strings = [
                "— profile", #All languages
                "— progress", #All languages
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and not 'epic npc' in embed_author.lower()):
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_PROGRESS)
                    )
                    interaction_user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return    
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    try:
                        embed_users.append(message.guild.get_member(user_id))
                    except discord.NotFound:
                        pass
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in profile message.', message)
                        return
                if interaction_user not in embed_users: return
                
                kwargs = {}
                # Update time travel count
                time_travel_count = -1
                if len(embed_field0_value.split('\n')) < 4:
                    time_travel_count = 0
                else:
                    search_patterns = [
                        r'time travels\*\*: (.+?)(?:$|\n)', #English
                        r'el tiempo\*\*: (.+?)(?:$|\n)', #Spanish
                        r'no tempo\*\*: (.+?)(?:$|\n)', #Portuguese
                    ]
                    tt_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                    if not tt_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time travel count not found in profile or progress message.', message)
                    else:
                        time_travel_count = int(tt_match.group(1))
                if time_travel_count > -1:
                    if time_travel_count != user_settings.time_travel_count:
                        kwargs['time_travel_count'] = time_travel_count
                    trade_daily_total = floor(100 * (time_travel_count + 1) ** 1.35)
                    if trade_daily_total != user_settings.trade_daily_total:
                        kwargs['trade_daily_total'] = trade_daily_total

                # Update current area
                area_match = re.search(r'rea\*\*: (.+?) \(', embed_field0_value.lower())
                if not area_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Area not found in current area profile or progress message.', message)
                else:
                    new_area = area_match.group(1)
                    if new_area == 'top':
                        new_area = 21
                    else:
                        new_area = int(new_area)
                    if user_settings.current_area != new_area:
                        kwargs['current_area'] = new_area

                # Remove partner name if not married
                partner_match = re.search(r'married to (.+?)$', embed_footer.lower())
                partner_name = partner_match.group(1) if partner_match else None
                if partner_name != user_settings.partner_name:
                    kwargs['partner_name'] = partner_name

                if kwargs:
                    await user_settings.update(**kwargs)


            # Update settings from eternal profile
            search_strings = [
                "— eternal", #All languages
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and not 'enchant' in embed_author.lower()):
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_PROGRESS)
                    )
                    interaction_user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return    
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    try:
                        embed_users.append(message.guild.get_member(user_id))
                    except discord.NotFound:
                        pass
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in eternal profile message.', message)
                        return
                if interaction_user not in embed_users: return
                
                kwargs = {}
                
                # Update eternal boosts tier
                gear_tier_matches = re.findall(r'\|\sT(\d+)\sL', embed_field_values)
                kwargs['eternal_boosts_tier'] = int(min(gear_tier_matches))

                if kwargs:
                    await user_settings.update(**kwargs)

                timestring_match = re.search(r'for\s(.+?)$', embed_footer)
                if timestring_match:
                    time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                    bot_answer_time = message.edited_at if message.edited_at else message.created_at
                    current_time = utils.utcnow()
                    time_elapsed = current_time - bot_answer_time
                    time_left -= time_elapsed
                    reminder_message = user_settings.alert_eternity_sealing.message
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(interaction_user.id, 'eternity-sealing', time_left,
                                                             message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)
                else:
                    try:
                        reminder = await reminders.get_user_reminder(user_settings.user_id, 'eternity-sealing')
                        await reminder.delete()
                    except exceptions.NoDataFoundError:
                        pass
                    

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(ProfileCog(bot))