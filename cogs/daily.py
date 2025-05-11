# daily.py

import asyncio
from datetime import timedelta
import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class DailyCog(commands.Cog):
    """Cog that contains the daily detection commands"""
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
            message_author = message_title = icon_url = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: message_title = str(embed.title)

            # Daily cooldown
            search_strings = [
                'you have claimed your daily rewards already', #English
                'ya reclamaste tu recompensa diaria', #Spanish
                'você já reivindicou sua recompensa diária', #Portuguese
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
                                await messages.find_message(message.channel.id, regex.COMMAND_DAILY,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in daily cooldown message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_daily.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                user_command = await functions.get_slash_command(user_settings, 'daily')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in daily cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                activity: str = 'daily'
                if user_settings.multiplier_management_enabled:
                    await user_settings.update_multiplier(activity, time_left)
                reminder_message = user_settings.alert_daily.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, activity, time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Daily
            search_strings = [
               " — daily", #All languages
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
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
                                await messages.find_message(message.channel.id, regex.COMMAND_DAILY,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in daily message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_daily.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'daily')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'daily')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_daily.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'daily', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'daily'))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(DailyCog(bot))