# time_cookie.py

import asyncio
from datetime import timedelta

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


class TimeCookieCog(commands.Cog):
    """Cog that contains the time cookie detection commands"""
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
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content

        # Time cookie
        search_strings = [
            'has traveled to the future!', #English
            'ha viajado al futuro!', #Spanish
            'viajou para o futuro!', #Portuguese
        ]
        if any(search_string in message_content.lower() for search_string in search_strings):
            user_name = user = user_command_message = None
            user = await functions.get_interaction_user(message)
            slash_command = True if user is not None else False
            if user is None:
                search_patterns = [
                    r'^\*\*(.+?)\*\* eats', #English
                    r'^\*\*(.+?)\*\* come', #Spanish, Portuguese
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if user_name_match:
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_USE_TIME_COOKIE,
                            user_name=user_name
                        )
                    )
                if not user_name_match or user_command_message is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found for time cookie message.', message)
                    return
                user = user_command_message.author
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled: return
            search_patterns = [
                r'! (.+?) minut[eo]s', #English, Spanish, Portuguese
            ]
            time_match = await functions.get_match_from_patterns(search_patterns, message_content)
            if not time_match:
                await functions.add_warning_reaction(message)
                await errors.log_error('Time not found in time cookie message.', message)
                return
            minutes = int(time_match.group(1))
            await reminders.reduce_reminder_time(user.id, timedelta(minutes=minutes), strings.TIME_COOKIE_AFFECTED_ACTIVITIES)
            if user_settings.auto_ready_enabled:
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(TimeCookieCog(bot))