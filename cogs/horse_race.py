# horse_race.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class HorseRaceCog(commands.Cog):
    """Cog that contains the horse race detection"""
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
        if message.embeds: return
        message_content = message.content
        search_strings = [
            'the next race is in', #English
            'la siguiente carrera es en', #Spanish
            'próxima corrida é em', #Portuguese
        ]
        if any(search_string in message_content.lower() for search_string in search_strings):
            search_strings_registered = [
                'you are registered already', #English
                'ya estás en registro', #Spanish
                'você já está em registro', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings_registered):
                already_registered = True
            else:
                already_registered = False
            user_name = user_command_message = None
            user = await functions.get_interaction_user(message)
            if user is None:
                if message.mentions:
                    user = message.mentions[0]
                else:
                    user_name_match = re.search(r"^\*\*(.+?)\*\*,", message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HORSE_RACE,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in horse race message.', message)
                        return
                    user = user_command_message.author
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.alert_horse_race.enabled: return
            search_patterns = [
                r'next race is in \*\*(.+?)\*\*', #English
                r'la siguiente carrera es en \*\*(.+?)\*\*', #Spanish
                r'próxima corrida é em \*\*(.+?)\*\*', #Portuguese
            ]
            timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
            if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in horse race message.', message)
                    return
            timestring = timestring_match.group(1)
            time_left = await functions.calculate_time_left_from_timestring(message, timestring)
            if time_left < timedelta(0): return
            reminder_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, 'horse-race', time_left,
                                                    message.channel.id, reminder_message)
            )
            await functions.add_reminder_reaction(message, reminder, user_settings)
            if reminder.record_exists and user_settings.alert_horse_breed.enabled and not already_registered:
                command_breed = await functions.get_slash_command(user_settings, 'horse breeding')
                command_race = await functions.get_slash_command(user_settings, 'horse race')
                user_command = f"{command_breed} or {command_race}"
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'horse')
                reminder_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'horse', time_left,
                                                         message.channel.id, reminder_message)
                )
            if user_settings.auto_ready_enabled:
                await functions.call_ready_command(self.bot, message, user)


# Initialization
def setup(bot):
    bot.add_cog(HorseRaceCog(bot))