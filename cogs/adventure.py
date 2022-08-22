# adventure.py

from datetime import datetime, timedelta
import re
from typing import Optional

import discord
from discord.ext import commands

from database import errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings


class AdventureCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

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
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                slash_command = True
                if user is None:
                    slash_command = False
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the adventure cooldown message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in adventure cooldown message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_adventure.enabled: return
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'adventure')
                else:
                    user_command_message, user_command = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+(?:adv\b|adventure\b)\s*(?:h\b|hardmode\b)?", user
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the adventure cooldown message.', message)
                    user_command = re.sub(r'\badv\b', 'adventure', user_command)
                    user_command = re.sub(r'\bh\b', 'hardmode', user_command)
                    user_command = f'`{user_command}`'
                    last_adventure_mode = None
                    if 'hardmode' in user_command: last_adventure_mode = 'hardmode'
                    await user_settings.update(last_adventure_mode=last_adventure_mode)
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
                                                                       message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in adventure cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
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
                and any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)):
                user = await functions.get_interaction_user(message)
                search_strings = [
                    '(but stronger)', #English
                    '(pero más fuerte)', #Spanish
                    '(só que mais forte)', #Portuguese
                ]
                last_adventure_mode = None
                slash_command = True
                if user is None:
                    slash_command = False
                    user_command = 'rpg adventure'
                    if any(search_string in message_content.lower() for search_string in search_strings):
                        user_command = f'{user_command} hardmode'
                        last_adventure_mode = 'hardmode'
                    user_command = f'`{user_command}`'
                    user_name = None
                    search_patterns = [
                        r"^\*\*(.+?)\*\* found a", #English
                        r"^\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in adventure message.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in adventure message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'adventure')
                    if any(search_string in message_content.lower() for search_string in search_strings):
                        user_command = f'{user_command} `mode: hardmode`'
                        last_adventure_mode = 'hardmode'
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
                        'OMEGA lootbox': emojis.SURPRISE,
                        'GODLY lootbox': emojis.SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if stuff_name in message_content:
                            await message.add_reaction(stuff_emoji)
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)
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