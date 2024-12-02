# cards.py

import asyncio
from datetime import timedelta
import re
from typing import Any

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings

processed_messages = {}

class CardsCog(commands.Cog):
    """Cog that contains the card detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before: dict[str, Any] = await functions.parse_embed(message_before)
        embed_data_after: dict[str, Any] = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        if 'reward' in embed_data_before['field0']['name'].lower() and 'reward' in embed_data_after['field0']['name'].lower():
            return
        if message_before.edited_at == message_after.edited_at: return
        """
        if message_after.channel.id == 1018269454641156147:
            await errors.log_error(
                f'Before Message ID: {message_before.id}\n'
                f'Before Message edit time: {message_before.edited_at}\n'
                f'Before Message flags: {message_before.flags}\n'
                f'Before Message embed data: {embed_data_before}\n'
                f'Before Message reference: {message_before.reference}\n'
                f'Before Message components: {message_before.components}\n'
                f'Before Message attachments: {message_before.attachments}\n'
                f'Before Message content: {message_before.content}\n'
                f'---\n'
                f'After Message ID: {message_after.id}\n'
                f'After Message edit time: {message_after.edited_at}\n'
                f'After Message flags: {message_after.flags}\n'
                f'After Message embed data: {embed_data_after}\n'
                f'After Message reference: {message_after.reference}\n'
                f'After Message components: {message_after.components}\n'
                f'After Message attachments: {message_after.attachments}\n'
                f'After Message content: {message_after.content}\n'
            )
         """
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = message_field0_value = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: message_title = str(embed.title)
            if embed.fields:
                message_field0_value = embed.fields[0].value

            # Card hand cooldown
            search_strings = [
                'you have played your cards recently', #English
                'you have played your cards recently', #TODO: Spanish
                'you have played your cards recently', #TODO: Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_CARD_HAND,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in card hand cooldown message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_card_hand.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                user_command = await functions.get_slash_command(user_settings, 'card hand')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in card hand cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                activity: str = 'card-hand'
                if user_settings.multiplier_management_mode != 0:
                    await user_settings.update_multiplier(activity, time_left)
                reminder_message = user_settings.alert_card_hand.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, activity, time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Card hand
            search_strings = [
               " — card hand", #All languages
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings)
                and '+' in message_field0_value):
                if message.id in processed_messages: return
                processed_messages[message.id] = utils.utcnow()
                for message_id, date_time in processed_messages.copy().items():
                    if date_time < (utils.utcnow() - timedelta(minutes=5)):
                        del processed_messages[message_id]
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_CARD_HAND,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in card hand message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_card_hand.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'card hand')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'card-hand')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_card_hand.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'card-hand', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'card-hand'))
                await functions.add_reminder_reaction(message, reminder, user_settings)


        if not message.embeds:
            message_content = message.content

            # Card hand timeout
            search_strings = [
                '** decided not to play lol', #English
                '** decided not to play lol', #TODO: Spanish
                '** decided not to play lol', #TODO: Portuguese
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
                        await errors.log_error('Couldn\'t find a user for card hand timeout message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_CARD_HAND,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for card hand timeout message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_card_hand.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'card hand')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'card-hand')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_card_hand.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'card-hand', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'card-hand'))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(CardsCog(bot))