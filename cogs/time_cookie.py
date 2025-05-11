# time_cookie.py

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings

if TYPE_CHECKING:
    import re


class TimeCookieCog(commands.Cog):
    """Cog that contains the time cookie detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        embed_data_before: dict[str, str] = await functions.parse_embed(message_before)
        embed_data_after: dict[str, str] = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message.embeds: return

        # Time cookie
        search_strings: list[str] = [
            'has traveled to the future!', #English
            'ha viajado al futuro!', #Spanish
            'viajou para o futuro!', #Portuguese
        ]
        if any(search_string in message.content.lower() for search_string in search_strings):
            user_name: str | None = None
            user_command_message: discord.Message | None = None
            user: discord.User | discord.Member | None = await functions.get_interaction_user(message)
            if user is None:
                search_patterns: list[str] = [
                    r'^\*\*(.+?)\*\* eats', #English
                    r'^\*\*(.+?)\*\* come', #Spanish, Portuguese
                ]
                user_name_match: re.Match[str] | None = await functions.get_match_from_patterns(search_patterns, message.content)
                if user_name_match:
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_TIME_COOKIE,
                                                    user_name=user_name)
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
            search_patterns: list[str] = [
                r'! (\d+?) minut[eo]s', #English, Spanish, Portuguese
            ]
            time_match: re.Match[str] | None = await functions.get_match_from_patterns(search_patterns, message.content)
            if not time_match:
                await functions.add_warning_reaction(message)
                await errors.log_error('Time not found in time cookie message.', message)
                return
            minutes: int = int(time_match.group(1))
            await reminders.reduce_reminder_time(user_settings, timedelta(minutes=minutes), strings.TIME_COOKIE_AFFECTED_ACTIVITIES)
            asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'time-cookie'))
            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(TimeCookieCog(bot))