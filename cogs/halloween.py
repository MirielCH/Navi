# halloween.py

import asyncio
from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class HalloweenCog(commands.Cog):
    """Cog that contains the halloween detection"""
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
            embed_description = embed_title = embed_field0_name = embed_field0_value = embed_autor = icon_url = ''
            if embed.description: embed_description = embed.description
            if embed.title: embed_title = embed.title
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
            if embed.author:
                embed_author = embed.author.name
                icon_url = embed.author.icon_url

            # Hal boo cooldown
            search_strings = [
                'you have scared someone recently', #English
                'ya asustaste recientemente', #Spanish
                'você se assustou recentemente', #Portuguese
            ]
            if any(search_string in embed_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the hal boo cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HAL_BOO,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the hal boo cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boo.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'hal boo')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           embed_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in hal boo cooldown message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_boo.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'boo', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Scroll boss helper
            search_strings = [
                "**the pumpkin bat** is attacking", #English
            ]
            if any(search_string in embed_field0_value.lower() for search_string in search_strings):
                user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r'\*\*(.+?)\*\* hits \*\*(.+?)\*\*',
                        r'\*\*(.+?)\*\* has summoned \*\*(.+?)\*\*',
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                    if not user_name_match:
                        user_name_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        if user_name.lower() == 'the pumpkin bat': user_name = user_name_match.group(2)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HAL_CRAFT_SPOOKY_SCROLL,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        user = None # Helper will still work if no user is found.
                    else:
                        user = user_command_message.author
                if user is not None:
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.halloween_helper_enabled: return
                search_patterns = [
                    r'(?:attacking you) (?:from )?(?:the )?(\w.+)!', #English
                ]
                attack_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not attack_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('No attack found in scroll boss helper', message)
                    return
                attack = attack_match.group(1).lower()
                attacks_answers = {
                    'left': 'pumpkin',
                    'right': 'attack',
                    'ahead': 'bazooka',
                    'behind': 'dodge',
                }
                answer = f'`{attacks_answers[attack].upper()}`'
                if user is not None:
                    if not user_settings.dnd_mode_enabled:
                        if user_settings.ping_after_message:
                            await message.reply(f'{answer} {user.mention}')
                        else:
                            await message.reply(f'{user.mention} {answer}')
                    else:
                        await message.reply(answer)
                else:
                    await message.reply(answer)

        if not message.embeds:
            message_content = message.content
            # Boo
            search_strings = [
                '** scared **', #English
                '** asustó a **', #Spanish
                '** assustou a **', #Portuguese
                '** failed to scare **', #English, failed
                '** got so much scared by **', #English, failed
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    search_patterns = [
                        r" \*\*(.+?)\*\* scared", #English
                        r" \*\*(.+?)\*\* failed", #English
                        r" scared by \*\*(.+?)\*\*", #English
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HAL_BOO,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in hal boo message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boo.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'hal boo')
                time_left = timedelta(hours=2)
                reminder_message = user_settings.alert_boo.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'boo', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)

# Initialization
def setup(bot):
    bot.add_cog(HalloweenCog(bot))