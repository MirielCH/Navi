# eternity.py

from datetime import timedelta
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


class EternityCog(commands.Cog):
    """Cog that contains the eternity detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
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
            return

        if not message.embeds:
            message_content = message.content

            # Unseal eternity
            search_strings = [
                "unsealed **the eternity**", #English
                "unsealed **the eternity**", #TODO: Spanish
                "unsealed **the eternity**", #TODO: Portuguese
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
                        await errors.log_error('Couldn\'t find a user for the eternity unseal message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_UNSEAL_ETERNITY,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the eternity unseal message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_eternity_sealing.enabled: return

                timestring_match = re.search(r'for\s\*\*(.+)\*\*\s\(', message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                reminder_message = user_settings.alert_eternity_sealing.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'eternity-sealing', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(EternityCog(bot))