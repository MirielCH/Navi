# maintenance.py

from datetime import timedelta
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from database import reminders, users
from resources import exceptions, functions, settings


class MaintenanceCog(commands.Cog):
    """Cog that contains the celebration event detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before: dict[str, str] = await functions.parse_embed(message_before)
        embed_data_after: dict[str, str] = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        row: discord.ActionRow
        for row in message_after.components:
            component: discord.Button | discord.SelectMenu
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if not message.embeds:
 
            # Cel Multiply cooldown
            search_strings: tuple[str, ...] = (
                'the bot is under maintenance!', #English
                'the bot is under maintenance!', #TODO: Spanish
                'the bot is under maintenance!', #TODO: Portuguese
            )
            if any(search_string in message.content.lower() for search_string in search_strings):
                user: discord.User | discord.Member = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_maintenance.enabled: return
                timestring_match: re.Match[str] | None = re.search(r"in \*\*(.+?)\*\*", message.content.lower())
                time_left: timedelta = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                if time_left < timedelta(0): return
                time_left = time_left + timedelta(seconds=random.randint(0, 5))
                reminder_message: str = user_settings.alert_maintenance.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'maintenance', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(MaintenanceCog(bot))