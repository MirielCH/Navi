# lottery.py

import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class LotteryCog(commands.Cog):
    """Cog that contains the lottery detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_description = message_field = ''
            if embed.description: message_description = embed.description
            if embed.fields: message_field = embed.fields[0].value

            # Lottery event check
            if 'join with `rpg lottery' in message_description.lower():
                user = await functions.get_interaction_user(message)
                user_command = 'rpg buy lottery ticket' if user is None else '/lottery amount: [1-10]'
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ') and 'lottery' in msg.content.lower()
                                and not msg.author.bot):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the lottery event message.',
                            message
                        )
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lottery.enabled: return
                timestring = re.search("Next draw\*\*: (.+?)$", message_field).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lottery', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Buy lottery ticket
            if "lottery ticket successfully bought" in message_content.lower():
                user = await functions.get_interaction_user(message)
                user_command = 'rpg buy lottery ticket' if user is None else '/lottery amount: [1-10]'
                if user is None:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\*,", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in lottery ticket message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in buy lottery ticket message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_lottery.enabled: return
                timestring = re.search("the winner in \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'lottery', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(LotteryCog(bot))