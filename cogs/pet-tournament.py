# pet-tournament.py

from datetime import datetime
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class PetTournamentCog(commands.Cog):
    """Cog that contains the horse race detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content
        if 'pet successfully sent to the pet tournament!' in message_content.lower():
            message_history = await message.channel.history(limit=50).flatten()
            user_command_message = None
            for msg in message_history:
                if msg.content is not None:
                    if (msg.content.lower().startswith('rpg pet') and ' tournament ' in msg.content.lower()
                        and not msg.author.bot):
                        user_command_message = msg
                        break
            if user_command_message is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error('Couldn\'t find a command for the pet tournament message.')
                return
            user = user_command_message.author
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.alert_pet_tournament.enabled: return
            timestring = re.search("next pet tournament is in \*\*(.+?)\*\*", message_content).group(1)
            time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
            bot_answer_time = message.created_at.replace(microsecond=0)
            current_time = datetime.utcnow().replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            time_left = time_left - time_elapsed
            reminder_message = user_settings.alert_pet_tournament.message.format(event='pet tournament')
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                     message.channel.id, reminder_message)
            )
            if reminder.record_exists:
                await message.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)


# Initialization
def setup(bot):
    bot.add_cog(PetTournamentCog(bot))