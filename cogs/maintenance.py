# maintenance.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from database import reminders, users
from resources import exceptions, functions, settings


class MaintenanceCog(commands.Cog):
    """Cog that contains the celebration event detection commands"""
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
        if not message.embeds:
            message_content = message.content
 
            # Cel Multiply cooldown
            search_strings = [
                'the bot is under maintenance!', #English
                'the bot is under maintenance!', #Spanish, MISSING
                'the bot is under maintenance!', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_maintenance.enabled: return
                timestring_match = re.search(r"in \*\*(.+?)\*\*", message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_maintenance.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'maintenance', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(MaintenanceCog(bot))