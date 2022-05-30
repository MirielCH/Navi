# events.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class EventsCog(commands.Cog):
    """Cog that contains the Event detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""

        if not message.embeds:
            message_content = message.content
            if message_content.lower().replace(' ','').startswith('rpgcel') and message_content.lower().endswith('dailyquest'):
                user = message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                midnight_today = datetime.utcnow().replace(hour=0, minute=2, microsecond=0)
                midnight_tomorrow = midnight_today + timedelta(days=1)
                time_to_midnight = midnight_tomorrow - current_time
                reminder_message = 'Hey! It\'s time for `rpg cel dailyquest`!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-daily', time_to_midnight,
                                                            message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if message.author.id != settings.EPIC_RPG_ID: return
        if not message.embeds:
            message_content = message.content
            # Cel Multiply
            if 'you feel 5% more rich' in message_content.lower():
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if (msg.content.lower().replace(' ','').startswith('rpgcel')
                            and msg.content.lower().endswith('multiply')
                            and not msg.author.bot):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a command for the cel multiply message.',
                        message
                    )
                    return
                user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(hours=12) - time_elapsed
                reminder_message = 'Hey! It\'s time for `rpg cel multiply`!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-multiply', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            if 'you cannot multiply your celebration coins' in message_content.lower() and message.mentions:
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                timestring = re.search("another \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
                reminder_message = 'Hey! It\'s time for `rpg cel multiply`!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-multiply', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            """
            if 'you already completed the quest of today!' in message_content.lower() and message.mentions:
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                timestring = re.search("in \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
                reminder_message = 'Hey! It\'s time for `rpg cel dailyquest`!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-daily', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)
            """

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_field_name = message_field_value = ''
            if len(embed.fields) > 1:
                message_field_name = embed.fields[1].name
                message_field_value = embed.fields[1].value

            if not message_field_name.lower() == 'normal events': return

            user = await functions.get_interaction_user(message)
            if user is None:
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if msg.content.lower().replace(' ','').startswith('rpgevent') and not msg.author.bot:
                            user_command_message = msg
                            break
                if user_command_message is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a command for the events message.',
                        message
                    )
                    return
                user = user_command_message.author
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled: return
            cooldowns = []
            if user_settings.alert_big_arena.enabled:
                try:
                    big_arena_search = re.search("Big arena\*\*: (.+?)\\n", message_field_value)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Big arena cooldown not found in event message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if big_arena_search is not None:
                    big_arena_timestring = big_arena_search.group(1)
                    big_arena_message = user_settings.alert_big_arena.message.replace('{event}', 'big arena')
                    cooldowns.append(['big-arena', big_arena_timestring.lower(), big_arena_message])
            if user_settings.alert_lottery.enabled:
                try:
                    lottery_search = re.search("Lottery\*\*: (.+?)\\n", message_field_value)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Lottery cooldown not found in event message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if lottery_search is not None:
                    lottery_timestring = lottery_search.group(1)
                    lottery_message = user_settings.alert_lottery.message.replace('{command}', 'rpg buy lottery ticket')
                    cooldowns.append(['lottery', lottery_timestring.lower(), lottery_message])
            if user_settings.alert_pet_tournament.enabled:
                try:
                    pet_search = re.search("tournament\*\*: (.+?)\\n", message_field_value)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Pet tournament cooldown not found in event message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if pet_search is not None:
                    pet_timestring = pet_search.group(1)
                    pet_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                    cooldowns.append(['pet-tournament', pet_timestring.lower(), pet_message])
            if user_settings.alert_horse_race.enabled:
                try:
                    horse_search = re.search("race\*\*: (.+?)\\n", message_field_value)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Horse race cooldown not found in event message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if horse_search is not None:
                    horse_timestring = horse_search.group(1)
                    horse_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
                    cooldowns.append(['horse-race', horse_timestring.lower(), horse_message])
            current_time = datetime.utcnow().replace(microsecond=0)
            updated_reminder = False
            for cooldown in cooldowns:
                cd_activity = cooldown[0]
                cd_timestring = cooldown[1]
                cd_message = cooldown[2]
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, cd_activity)
                except exceptions.NoDataFoundError:
                    continue
                updated_reminder = True
                time_left = await functions.parse_timestring_to_timedelta(cd_timestring)
                if cd_activity == 'pet-tournament': time_left += timedelta(minutes=1)
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                if time_left.total_seconds() > 0:
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, cd_activity, time_left,
                                                            message.channel.id, cd_message, overwrite_message=False)
                    )
                    if not reminder.record_exists:
                        await message.channel.send(strings.MSG_ERROR)
                        return
            if updated_reminder and user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(EventsCog(bot))