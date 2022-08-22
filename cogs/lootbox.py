# lootbox.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class BuyCog(commands.Cog):
    """Cog that contains the lootbox detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

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
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                lootbox_name = '[lootbox]'
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in lootbox cooldown message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await('User not found in lootbox cooldown message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lootbox.enabled: return
                lootbox_name = '[lootbox]' if user_settings.last_lootbox == '' else f'{user_settings.last_lootbox} lootbox'
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'buy')
                    user_command = f"{user_command} `item: {lootbox_name}`"
                else:
                    user_command = f'`rpg buy {lootbox_name}`'
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
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
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and not 'guild ring' in message_content.lower()
                and not 'smol coin' in message_content.lower()
                and not 'horseshoe' in message_content.lower()):
                user = await functions.get_interaction_user(message)
                lootbox_type = None
                lootbox_name = '[lootbox]'
                lootbox_type_match = re.search(r'`(.+?) lootbox`', message_content.lower())
                slash_command = True
                if lootbox_type_match:
                    lootbox_type = lootbox_type_match.group(1)
                    lootbox_name = f'{lootbox_type} lootbox'
                if user is None:
                    slash_command = False
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+buy\s+[a-z]+\s+(?:lb\b|lootbox\b)"
                        )
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
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'buy')
                    user_command = f"{user_command} `item: {lootbox_name}`"
                else:
                    user_command = f'`rpg buy {lootbox_name}`'
                await user_settings.update(last_lootbox=lootbox_type)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'lootbox')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lootbox', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)


# Initialization
def setup(bot):
    bot.add_cog(BuyCog(bot))