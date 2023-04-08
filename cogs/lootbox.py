# lootbox.py

import asyncio
from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class BuyCog(commands.Cog):
    """Cog that contains the lootbox detection commands"""
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
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Lootbox cooldown
            search_strings = [
                'you have already bought a lootbox', #English
                'ya compraste una lootbox', #Spanish
                'você já comprou uma lootbox', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                lootbox_name = '[lootbox]'
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_LOOTBOX,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in lootbox cooldown message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lootbox.enabled: return
                lootbox_name = '[lootbox]' if user_settings.last_lootbox == '' else f'{user_settings.last_lootbox} lootbox'
                user_command = await functions.get_slash_command(user_settings, 'buy')
                if user_settings.slash_mentions_enabled:
                    user_command = f"{user_command} `item: {lootbox_name}`"
                else:
                    user_command = f"{user_command} `{lootbox_name}`".replace('` `', ' ')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in lootbox cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lootbox', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Buy lootbox
            search_strings = [
                'lootbox` successfully bought', #English
                'lootbox` comprado(s)', #Spanish, Portuguese
            ]
            search_strings_excluded = [
                'gingerbreads', #Christmas shop
                'snowflakes', #Christmas shop
                'guild ring', #Guild shop
                'smol coin', #Returning shop
                'horseshoe', #Horse festival shop
                'coolrency', #Ultraining shop
                'pumpkins', #Halloween shop
                'spooky orbs', #Halloween shop
                'golden eggs', #Easter shop
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and all(search_string not in message_content.lower() for search_string in search_strings_excluded)):
                user = await functions.get_interaction_user(message)
                lootbox_type = user_command_message = None
                lootbox_name = '[lootbox]'
                lootbox_type_match = re.search(r'`(.+?) lootbox`', message_content.lower())
                if lootbox_type_match:
                    lootbox_type = lootbox_type_match.group(1)
                    lootbox_name = f'{lootbox_type} lootbox'
                slash_command = True if user is not None else False
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOOTBOX)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the lootbox message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lootbox.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'buy')
                if user_settings.slash_mentions_enabled:
                    user_command = f"{user_command} `item: {lootbox_name}`"
                else:
                    user_command = f"{user_command} `{lootbox_name}`".replace('` `', ' ')
                await user_settings.update(last_lootbox=lootbox_type)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'lootbox')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lootbox', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(BuyCog(bot))