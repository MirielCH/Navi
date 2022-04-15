# horse-race.py

from datetime import datetime
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class HorseRaceCog(commands.Cog):
    """Cog that contains the horse race detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content
        if 'the next race is in' in message_content.lower():
            user_name = None
            user = await functions.get_interaction_user(message)
            if user is None:
                if message.mentions:
                    user = message.mentions[0]
                else:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\*,", message_content).group(1)
                        user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    except Exception as error:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error(f'User not found in horse race message: {message_content}')
                        return
                    for member in message.guild.members:
                        member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        if member_name == user_name:
                            user = member
                            break
            if user is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in horse race message: {message_content}')
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.alert_horse_race.enabled: return
            timestring = re.search("next race is in \*\*(.+?)\*\*", message_content).group(1)
            time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
            bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
            current_time = datetime.utcnow().replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            time_left = time_left - time_elapsed
            reminder_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, 'horse-race', time_left,
                                                    message.channel.id, reminder_message)
            )
            if reminder.record_exists:
                await message.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)


# Initialization
def setup(bot):
    bot.add_cog(HorseRaceCog(bot))