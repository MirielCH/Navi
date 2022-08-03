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
                user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel,
                            r"^rpg\s+(?:cel\b|celebration\b)\s+multiply\b"
                        )
                    )
                if user_command_message is None:
                    await functions.add_warning_reaction(message)
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
                timestring_match = re.search(r"another \*\*(.+?)\*\*", message_content)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in cel multiply message', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
                reminder_message = 'Hey! It\'s time for `rpg cel multiply`!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-multiply', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'you have not reached the end of this stage', #English
                'aún no has llegado al final de esta etapa', #Spanish
                'você ainda não chegou ao fim desta etapa', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                slash_command = False
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '`/hf megarace`'
                    slash_command = True
                else:
                    user_command = '`rpg hf megarace`'
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace start message.', message)
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                search_patterns = [
                    r'be there in \*\*(.+?)\*\*', #English
                    r'allí en \*\*(.+?)\*\*', #Spanish
                    r'lá em \*\*(.+?)\*\*', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace start message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left.total_seconds() == 0: return
                reminder_message = f'Hey! It\'s time for {user_command}!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
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
                timestring = re.search(r"in \*\*(.+?)\*\*", message_content).group(1)
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
            message_field0_name = message_field1_name = message_field0_value = message_field1_value = ''
            message_description = ''
            if embed.description: message_description = str(embed.description)
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                message_field0_name = embed.fields[0].name
                message_field0_value = embed.fields[0].value
            if len(embed.fields) > 1:
                message_field1_name = embed.fields[1].name
                message_field1_value = embed.fields[1].value

            search_strings = [
                'normal events', #English
                'eventos normales', #Spanish
                'eventos normais', #Portuguese
            ]
            if any(search_string in message_field1_name.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(message.channel, r"^rpg\s+events?\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the events message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                cooldowns = []
                if user_settings.alert_big_arena.enabled:
                    big_arena_match = re.search(r"big arena\*\*: (.+?)\n", message_field1_value.lower())
                    if big_arena_match:
                        big_arena_timestring = big_arena_match.group(1)
                        big_arena_message = user_settings.alert_big_arena.message.replace('{event}', 'big arena')
                        cooldowns.append(['big-arena', big_arena_timestring.lower(), big_arena_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Big arena cooldown not found in event message.', message)
                        return
                if user_settings.alert_lottery.enabled:
                    lottery_match = re.search(r"lottery\*\*: (.+?)\n", message_field1_value.lower())
                    if lottery_match:
                        lottery_timestring = lottery_match.group(1)
                        if slash_command:
                            user_command = f"{strings.SLASH_COMMANDS['lottery']} `amount: [1-10]`"
                        else:
                            user_command = f'`rpg buy lottery ticket`'
                        lottery_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                        cooldowns.append(['lottery', lottery_timestring.lower(), lottery_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Lottery cooldown not found in event message.', message)
                        return
                if user_settings.alert_pet_tournament.enabled:
                    pet_match = re.search(r"tournament\*\*: (.+?)\n", message_field1_value.lower())
                    if pet_match:
                        pet_timestring = pet_match.group(1)
                        pet_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                        cooldowns.append(['pet-tournament', pet_timestring.lower(), pet_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Pet tournament cooldown not found in event message.', message)
                        return
                if user_settings.alert_horse_race.enabled:
                    horse_match = re.search(r"race\*\*: (.+?)\n", message_field1_value.lower())
                    if horse_match:
                        horse_timestring = horse_match.group(1)
                        horse_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
                        cooldowns.append(['horse-race', horse_timestring.lower(), horse_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Horse race cooldown not found in event message.', message)
                        return
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

            # Horse festival megarace
            search_strings = [
                'total time', #English
                'tiempo total', #Spanish
                'tempo total', #Portuguese
            ]
            if (any(search_string in message_field1_name.lower() for search_string in search_strings)
                and 'megarace' in message_author.lower()):
                user_id = user_name = None
                slash_command = False
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '`/hf megarace`'
                    slash_command = True
                else:
                    user_command = '`rpg hf megarace`'
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User name not found in megarace message.', message)
                            return
                    if user_id is not None:
                        try:
                            user = await message.guild.fetch_member(user_id)
                        except:
                            pass
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in megarace message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                search_patterns = [
                    r' \*\*(.+?)\*\* ', #English, Spanish, Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field1_value.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = f'Hey! It\'s time for {user_command}!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'you can join megarace every week', #English
                'puedes entrar a la megacarrera cada semana', #Spanish
                'você pode entrar na mega corrida toda semana', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_id = user_name = None
                slash_command = False
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '`/hf megarace`'
                    slash_command = True
                else:
                    user_command = '`rpg hf megarace`'
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(message.channel, r"^rpg\s+(?:hf\b|horsefestival\b)\s+megarace\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                search_patterns = [
                    r'time remaining\*\*: (.+?)\n', #English
                    r'ti?empo restante\*\*: (.+?)\n', #Spanish, Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field0_value.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace overview message.', message)
                    return
                timestring = timestring_match.group(1)
                if timestring in ('0d 0h 0m 0s', '0h 0m 0s'): return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = f'Hey! It\'s time for {user_command}!'
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'passes through the boost', #English
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_id = user_name = None
                slash_command = False
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '`/hf megarace`'
                    slash_command = True
                else:
                    user_command = '`rpg hf megarace`'
                    user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE_START, message_field0_name)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in megarace boost message.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in megarace boost message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                search_patterns = [
                    r'(?:increased|reduced)__: \*\*(.+?)\*\*', #English
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field0_value.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace boost message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'megarace')
                except exceptions.NoDataFoundError:
                    return
                search_strings_increased = [
                    'increased', #English
                ]
                search_strings_reduced = [
                    'reduced', #English
                ]
                if any(search_string in message_field0_value.lower() for search_string in search_strings_increased):
                    new_end_time = reminder.end_time + time_left
                elif any(search_string in message_field0_value.lower() for search_string in search_strings_reduced):
                    new_end_time = reminder.end_time - time_left
                await reminder.update(end_time=new_end_time)
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(EventsCog(bot))