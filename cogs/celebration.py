# celebration.py

import asyncio
from datetime import datetime, timedelta
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, settings


class CelebrationCog(commands.Cog):
    """Cog that contains the celebration event detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_field0_value = embed_field0_name = ''
            if embed.description is not None: embed_description = str(embed.description)
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value

            # Cel dailyquest
            search_strings = [
                'come back tomorrow and i will give you another quest!', #English
                'why? idk, i have too many', #English 2
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)
                or 'daily quest' in embed_field0_name.lower()):
                user_command = user_command_message = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id,
                                                    r"(?:cel\b|celebration\b)\s+dailyquest\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the cel dailyquest message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_dailyquest.enabled: return
                
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=2, microsecond=0)
                end_time = midnight_today + timedelta(days=1, minutes=2, seconds=random.randint(60, 300))
                time_to_midnight = end_time - current_time
                user_command = await functions.get_slash_command(user_settings, 'cel dailyquest')
                reminder_message = user_settings.alert_cel_dailyquest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-dailyquest', time_to_midnight,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            
            # Cel Multiply
            search_strings_1 = [
                'you feel', #English
            ]
            search_strings_2 = [
                '% more rich', #English
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings_1)
                and any(search_string in message_content.lower() for search_string in search_strings_2)):
                user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id,
                                                    r"(?:cel\b|celebration\b)\s+multiply\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the cel multiply message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_multiply.enabled: return
                current_time = utils.utcnow()
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(hours=12) - time_elapsed
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'cel multiply')
                reminder_message = user_settings.alert_cel_multiply.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-multiply', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'cel-multiply'))
                await functions.add_reminder_reaction(message, reminder, user_settings)
            message_content = message.content
            
            # Cel sacrifice
            search_strings = [
                'sacrificed', #English
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and 'celebrationcoin' in message_content.lower()):
                user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'^\*\*(.+?)\*\* ', message_content)
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await messages.find_message(message.channel.id,
                                                    r"(?:cel\b|celebration\b)\s+sacrifice\b",
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the cel sacrifice message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_sacrifice.enabled: return
                current_time = utils.utcnow()
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(hours=12) - time_elapsed
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'cel sacrifice')
                reminder_message = user_settings.alert_cel_multiply.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-sacrifice', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'cel-sacrifice'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Cel Multiply cooldown
            search_strings = [
                'you cannot multiply your celebration coins', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_multiply.enabled: return
                timestring_match = re.search(r"another \*\*(.+?)\*\*", message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'cel multiply')
                reminder_message = user_settings.alert_cel_multiply.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-multiply', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Cel daily quest cooldown
            search_strings = [
                'you already completed the quest of today!', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings) and message.mentions:
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_dailyquest.enabled: return
                timestring_match = re.search(r"in \*\*(.+?)\*\*", message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                user_command = await functions.get_slash_command(user_settings, 'cel dailyquest')
                reminder_message = user_settings.alert_cel_dailyquest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-dailyquest', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Cel sacrifice cooldown
            search_strings = [
                'you cannot sacrifice your celebration coins', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_cel_sacrifice.enabled: return
                timestring_match = re.search(r"another \*\*(.+?)\*\*", message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'cel sacrifice')
                reminder_message = user_settings.alert_cel_sacrifice.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'cel-sacrifice', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(CelebrationCog(bot))