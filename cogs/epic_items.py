# epic_items.py

import asyncio
from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class EpicItemsCog(commands.Cog):
    """Cog that contains the epic item detection commands"""
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

            # EPIC item cooldown
            search_strings = [
                'you have used an epic item already', #English
                'ya usaste un item épico', #Spanish
                'você já usou um item épico', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the epic item cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_EPIC_ITEM_ARENA_TOKEN,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the epic item cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_epic.enabled: return
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in epic item cooldown message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_epic.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'epic', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # EPIC seed, ULTRA bait, coin trumpet, legendary toothbrush
            search_strings_seed = [
                'planting the', #English
                'colocando la', #Spanish
                'plantando a', #Portuguese
            ]
            search_strings_bait = [
                'placing the', #English
                'colocando el', #Spanish
                'colocando a', #Portuguese
            ]
            search_strings_trumpet = [
                'summoning the', #English
                'invocando una', #Spanish
                'convocando a', #Portuguese
            ]
            search_strings_toothbrush = [
                'casts a magic spell', #English
                'casts a magic spell', #Spanish
                'casts a magic spell', #Portuguese
            ]
            if ((any(search_string in message_content.lower() for search_string in search_strings_seed)
                and 'epic seed' in message_content.lower())
                or (any(search_string in message_content.lower() for search_string in search_strings_bait)
                and 'ultra bait' in message_content.lower())
                or (any(search_string in message_content.lower() for search_string in search_strings_trumpet)
                and 'coin trumpet' in message_content.lower())
                or (any(search_string in message_content.lower() for search_string in search_strings_toothbrush)
                and 'legendary toothbrush' in message_content.lower())
            ):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_EPIC_ITEM)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for epic item use.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if not user_settings.alert_epic.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'epic')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_epic.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'epic', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Arena token
            search_strings = [
                'arena cooldown got reset!', #English
                'cooldown de arena reiniciado!', #Spanish
                'o cooldown do arena foi reiniciado!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    search_patterns = [
                        r"^\*\*(.+?)\*\*,", #All languages
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_USE_ARENA_TOKEN,
                                                    user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for arena token use.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if not user_settings.alert_epic.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'epic')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_epic.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'epic', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(EpicItemsCog(bot))