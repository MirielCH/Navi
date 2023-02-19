# adventure.py

import asyncio
from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, tracking, users
from resources import emojis, exceptions, functions, regex, settings, strings


class AdventureCog(commands.Cog):
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
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Adventure cooldown
            search_strings = [
                'you have already been in an adventure', #English
                'ya has estado en una aventura', #Spanish
                'você já esteve em uma aventura', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the adventure cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ADVENTURE, user=user,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the adventure cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_adventure.enabled: return
                if not slash_command:
                    last_adventure_mode = None
                    user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                    if 'hardmode' in user_command_message_content: last_adventure_mode = 'hardmode'
                    await user_settings.update(last_adventure_mode=last_adventure_mode)
                user_command = await functions.get_slash_command(user_settings, 'adventure')
                if user_settings.last_adventure_mode != '':
                    if user_settings.slash_mentions_enabled:
                        user_command = f"{user_command} `mode: {user_settings.last_adventure_mode}`"
                    else:
                        user_command = f"{user_command} `{user_settings.last_adventure_mode}`".replace('` `', ' ')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in adventure cooldown message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'adventure', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Adventure
            search_strings = [
                'found a', #English
                'encontr', #Spanish, Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(f'{monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
            ):
                user = await functions.get_interaction_user(message)
                search_strings_hardmode = [
                    '(but stronger)', #English
                    '(pero más fuerte)', #Spanish
                    '(só que mais forte)', #Portuguese
                ]
                last_adventure_mode = user_command_message = None
                slash_command = True if user is not None else False
                if user is None:
                    search_patterns = [
                        r"^\*\*(.+?)\*\* found a", #English
                        r"^\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_ADVENTURE, user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in adventure message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                user_command = await functions.get_slash_command(user_settings, 'adventure')
                if any(search_string in message_content.lower() for search_string in search_strings_hardmode):
                    last_adventure_mode = 'hardmode'
                    if user_settings.slash_mentions_enabled:
                        user_command = f"{user_command} `mode: {last_adventure_mode}`"
                    else:
                        user_command = f"{user_command} `{last_adventure_mode}`".replace('` `', ' ')
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'adventure', current_time)
                if not user_settings.alert_adventure.enabled: return
                await user_settings.update(last_adventure_mode=last_adventure_mode)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'adventure')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'adventure', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'OMEGA lootbox': emojis.PANDA_SURPRISE,
                        'GODLY lootbox': emojis.PANDA_SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if stuff_name in message_content:
                            await message.add_reaction(stuff_emoji)
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)
                # Add an F if the user died
                search_strings = [
                    'but lost fighting', #English
                    'pero perdió luchando', #Spanish
                    'mas perdeu a luta', #Portuguese
                ]
                if any(search_string in message_content for search_string in search_strings):
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.RIP)


# Initialization
def setup(bot):
    bot.add_cog(AdventureCog(bot))