# party_popper.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings


class BoostsCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
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
            embed_author = embed_title = icon_url = embed_description = ''
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: embed_title = str(embed.title)
            if embed.description: embed_description = str(embed.description)
            embed_potion_fields = ''
            if embed.fields:
                embed_potion_fields = embed.fields[0].value
                if len(embed.fields) > 1:
                    if embed.fields[1].name == '':
                        embed_potion_fields = f'{embed_potion_fields}\n{embed.fields[1].value}'

            # Boosts cooldowns
            search_strings = [
                'these are your active boosts', #English
                'these are your active boosts', #Spanish, MISSING
                'these are your active boosts', #Portuguese, MISSING
            ]
            search_strings_excluded = [
                'none', #English
                'none', #Spanish, MISSING
                'none', #Portuguese, MISSING
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)
                and all(search_string not in embed_potion_fields.lower() for search_string in search_strings_excluded)):
                user_id = user_name = user_command_message = None
                potion_dragon_breath_active = False
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the boosts message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_BOOSTS, user=user,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the boosts message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                for line in embed_potion_fields.lower().split('\n'):
                    active_item_match = re.search(r' \*\*(.+?)\*\*: (.+?)$', line)
                    if not active_item_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Active item not found in boosts message.', message)
                        return
                    active_item = active_item_match.group(1)
                    active_item_emoji = emojis.BOOST_ITEMS_EMOJIS.get(active_item, '')
                    time_string = active_item_match.group(2)
                    time_left = await functions.calculate_time_left_from_timestring(message, time_string)
                    if time_left < timedelta(0): return
                    reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', active_item_emoji)
                        .replace('{boost_item}', active_item)
                        .replace('  ', ' ')
                    )
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, active_item.replace(' ', '-'), time_left,
                                                             message.channel.id, reminder_message)
                    )
                    if active_item == 'dragon breath potion': potion_dragon_breath_active = True
                if user_settings.potion_dragon_breath_active != potion_dragon_breath_active:
                    await user_settings.update(potion_dragon_breath_active=potion_dragon_breath_active)
                if user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

        if not message.embeds:
            message_content = message.content

            # Party popper
            search_strings = [
                'uses the <:partypopper', #English
                'uses the <:partypopper', #Spanish, MISSING
                'uses the <:partypopper', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for party popper message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_PARTY_POPPER,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the party popper message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                timestring_match = re.search(r'for \*\*(.+?)\*\*:', message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.PARTY_POPPER)
                        .replace('{boost_item}', 'party popper')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'party-popper', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Alchemy potions
            search_strings = [
                '**, you\'ve received the following boosts for', #English
                '**, you\'ve received the following boosts for', #Spanish
                '**, you\'ve received the following boosts for', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ALCHEMY)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the alchemy message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                item_name_match = re.search(r'a (.+?) \*\*(.+?)\*\*, ', message_content.lower())
                timestring_match = re.search(r'for \*\*(.+?)\*\*:', message_content.lower())
                if not item_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find the item name in the alchemy message.',
                                            message)
                    return
                item_name = item_name_match.group(2)
                item_emoji = emojis.BOOST_ITEMS_EMOJIS.get(item_name, '')
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', item_emoji)
                        .replace('{boost_item}', item_name)
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, item_name.replace(' ','-'), time_left,
                                                         message.channel.id, reminder_message)
                )
                if item_name == 'dragon breath potion':
                    await user_settings.update(potion_dragon_breath_active=True)
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Valentine boost
            search_strings = [
                '`valentine boost` successfully bought', #English
                '`valentine boost` comprado(s)', #Spanish & Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOVE_BUY_VALENTINE_BOOST)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the valentine boost message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                time_left = timedelta(hours=1)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', '❤️')
                        .replace('{boost_item}', 'valentine boost')
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'valentine-boost', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(BoostsCog(bot))