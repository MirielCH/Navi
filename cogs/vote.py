# vote.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class VoteCog(commands.Cog):
    """Cog that contains the dungeon/miniboss detection commands"""
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
            if message.embeds[0].fields:
                field = message.embeds[0].fields[0]

                # Vote cooldown
                search_strings = [
                    'next vote rewards', #English
                    'recompensas del siguiente voto', #Spanish
                    'recompensas do próximo voto', #Portuguese
                ]
                if any(search_string in field.name.lower() for search_string in search_strings):
                    search_patterns = [
                        r'cooldown: \*\*(.+?)\*\*', #All languages
                    ]
                    timestring_match = await functions.get_match_from_patterns(search_patterns, field.value.lower())
                    if not timestring_match: return
                    timestring = timestring_match.group(1)
                    user = await functions.get_interaction_user(message)
                    slash_command = True
                    if user is None:
                        slash_command = False
                        user_command_message, _ = (
                            await functions.get_message_from_channel_history(message.channel, r"^rpg\s+vote\b")
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a user for the vote embed.', message)
                            return
                        user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.alert_vote.enabled: return
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'vote')
                    else:
                        user_command = '`rpg vote`'
                    time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_vote.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'vote', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(VoteCog(bot))