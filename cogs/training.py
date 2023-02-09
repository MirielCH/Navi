# training.py

import asyncio
from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, tracking, users
from resources import emojis, exceptions, functions, regex, settings, strings


class TrainingCog(commands.Cog):

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
            message_author = message_title = message_description = message_field1_value = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)
            if embed.description: message_description = str(embed.description)
            if len(embed.fields) > 1: message_field1_value = embed.fields[1].value

            # Training cooldown
            search_strings = [
                'you have trained already', #English
                'ya entrenaste', #Spanish
                'você já treinou', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User name not found in training cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRAINING_ULTRAINING,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for training cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_training.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    last_training_command = 'ultraining' if interaction.name.startswith('ultraining') else 'training'
                else:
                    user_command_message_content = re.sub(r'\btr\b', 'training', user_command_message.content.lower())
                    user_command_message_content = re.sub(r'\bultr\b', 'ultraining', user_command_message_content)
                    last_training_command = 'ultraining' if 'ultraining' in user_command_message_content else 'training'
                user_command = await functions.get_slash_command(user_settings, last_training_command)
                await user_settings.update(last_training_command=last_training_command)
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in training cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                '**: well done, **', #English
                '**: bien hecho, **', #Spanish
                '**: muito bem, **', #Portuguese
            ]
            if (any(search_string in message_description.lower() for search_string in search_strings)
                and any(search_string.lower() in message_description.lower() for search_string in strings.EPIC_NPC_NAMES)):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_name_match = re.search(r", \*\*(.+?)\*\*!", message_description)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_ULTRAINING,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in ultraining message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'ultraining', current_time)
                if not user_settings.alert_training.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'ultraining')
                await user_settings.update(last_training_command='ultraining')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'training')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)
                search_strings = [
                    'better luck next time', #English
                    'próxima vez', #Spanish, Portuguese
                ]
                if any(search_string in message_field1_value.lower() for search_string in search_strings):
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.PEEPO_NOOB)

        if not message.embeds:
            message_content = message.content
            # Training
            search_strings = [
                'well done, **', #English success
                'better luck next time, **', #English fail
                'bien hecho, **', #Spanish success
                'próxima vez, **', #Spanish, Portuguese fail
                'muito bem, **', #Portuguese success
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_name_match = re.search(r", \*\*(.+?)\*\*", message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in training message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                user_command = await functions.get_slash_command(user_settings, 'training')
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'training', current_time)
                if not user_settings.alert_training.enabled: return
                await user_settings.update(last_training_command='training')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'training')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Training VOID event
            search_strings = [
                'attempts to fly', #English butterfly
                'runs the area command', #English keyboard
                'it seems like a mysterious player saved', #English cry
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_name_match = re.search(r"\*\*(.+?)\*\*", message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in training event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            # Training reset from ultraining shop
            search_strings = [
                'training reset` successfully bought', #English
                'training reset` comprado(s)', #Spanish, Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ULTRAINING_BUY_TRAINING_RESET)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for training reset message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'training')
                except exceptions.NoDataFoundError:
                    return
                await reminder.delete()
                if reminder.record_exists:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(f'Had an error deleting the training reminder in training reset.', message)
                    return
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(TrainingCog(bot))