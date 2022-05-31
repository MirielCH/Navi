# daily.py

import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class DailyCog(commands.Cog):
    """Cog that contains the daily detection commands"""
    def __init__(self, bot):
        self.bot = bot

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

            # Daily cooldown
            if 'you have claimed your daily rewards already' in message_title.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                user_command = 'rpg daily' if user is None else '/daily'
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in daily cooldown message: {message.embeds[0].fields}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in daily cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_daily.enabled: return
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_daily.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'daily', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Daily
            if "'s daily reward" in message_author.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                user_command = 'rpg daily' if user is None else '/daily'
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s daily reward", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in daily message: {message_author}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in daily message: {message_author}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_daily.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'daily')
                reminder_message = user_settings.alert_daily.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'daily', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(DailyCog(bot))