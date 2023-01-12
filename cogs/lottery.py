# lottery.py

import asyncio
from datetime import datetime, timedelta
import random
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class LotteryCog(commands.Cog):
    """Cog that contains the lottery detection commands"""
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

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_description = message_field = ''
            if embed.description: message_description = embed.description
            if embed.fields: message_field = embed.fields[0].value

            # Lottery event check
            search_strings = [
                'join with `lottery', #English 1
                'join with `/lottery', #English 2
                'participa con `/lottery', #Spanis
                'participe com `/lottery', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOTTERY)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the lottery event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lottery.enabled: return
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'lottery')
                except exceptions.NoDataFoundError:
                    return
                if reminder.triggered: return
                user_command = await functions.get_slash_command(user_settings, 'lottery')
                if user_settings.slash_mentions_enabled:
                    user_command = f"{user_command} `amount: [1-200]`"
                else:
                    user_command = f"{user_command} `buy [1-200]`".replace('` `', ' ')
                search_patterns = [
                    r'next draw\*\*: (.+?)$', #English
                    r'siguiente ronda\*\*: (.+?)$', #Spanish
                    r'próximo sorteio\*\*: (.+?)$', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in lottery event message.', message)
                    return
                timestring = timestring_match.group(1).strip('`')
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                time_left = time_left + timedelta(seconds=random.randint(0, 120))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lottery', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Buy lottery ticket
            search_strings = [
                'lottery ticket` successfully bought', #English
                'lottery ticket successfully bought', #English
                'lottery ticket` comprado', #Spanish, Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(r"^\*\*(.+?)\*\*,", message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_LOTTERY,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in buy lottery ticket message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lottery.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'lottery')
                if user_settings.slash_mentions_enabled:
                    user_command = f"{user_command} `amount: [1-200]`"
                else:
                    user_command = f"{user_command} `buy [1-200]`".replace('` `', ' ')
                search_patterns = [
                    r'the winner in \*\*(.+?)\*\*', #English
                    r'el ganador en \*\*(.+?)\*\*', #Spanish
                    r'o vencedor em \*\*(.+?)\*\*', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in buy lottery ticket message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                time_left = time_left + timedelta(seconds=random.randint(0, 120))
                reminder_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lottery', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'you cannot buy more than 10 tickets per lottery', #English
                'no puedes comprar más de 10 tickets por lotería', #Spanish
                'você não pode comprar mais de 10 bilhetes por loteria', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None: user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lottery.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'lottery')
                if user_settings.slash_mentions_enabled:
                    user_command = f"{user_command} `amount: [1-200]`"
                else:
                    user_command = f"{user_command} `buy [1-200]`".replace('` `', ' ')
                current_time = datetime.utcnow().replace(microsecond=0, tzinfo=None)
                today_12pm = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
                today_12am = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow_12am = today_12am + timedelta(days=1)
                if today_12am > current_time:
                    time_left = today_12am - current_time
                elif today_12pm > current_time:
                    time_left = today_12pm - current_time
                else:
                    time_left = tomorrow_12am - current_time
                time_left = time_left + timedelta(seconds=random.randint(0, 120))
                reminder_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lottery', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(LotteryCog(bot))