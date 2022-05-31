# horse-race.py

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
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in horse race message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
            if user is None:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in horse race message: {message_content}',
                    message
                )
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.alert_horse_race.enabled: return
            timestring = re.search("next race is in \*\*(.+?)\*\*", message_content).group(1)
            time_left = await functions.calculate_time_left_from_timestring(message, timestring)
            reminder_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, 'horse-race', time_left,
                                                    message.channel.id, reminder_message)
            )
            await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(HorseRaceCog(bot))