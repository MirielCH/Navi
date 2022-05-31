# training.py

from datetime import datetime
import re

import discord
from discord.ext import commands

from database import errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings


class TrainingCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

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
            if 'you have trained already' in message_title.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
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
                                f'User not found in training cooldown message: {message.embeds[0].fields}',
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
                        f'User not found in training cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_training.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    user_command = f'/{interaction.name}'
                else:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ')
                                and (' tr' in msg.content.lower() or 'ultr' in msg.content.lower())
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the training cooldown message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                    if user_command.endswith(' ultr'): user_command = user_command.replace(' ultr',' ultraining')
                    if user_command.endswith(' tr'): user_command = user_command.replace(' tr',' training')
                    user_command = " ".join(user_command.split())
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            if '**epic npc**: well done, **' in message_description.lower():
                user_name = None
                user = await functions.get_interaction_user(message)
                user_command = '/ultraining' if user is not None else 'rpg ultraining'
                if user is None:
                    try:
                        user_name = re.search(", \*\*(.+?)\*\*!", message_description).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in ultraining message: {message.embeds[0].fields}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in ultraining message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'training', current_time)
                if not user_settings.alert_training.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'training')
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if 'better luck next time' in message_field1_value.lower():
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NOOB)

        if not message.embeds:
            message_content = message.content
            # Training
            if ('well done, **' in message_content.lower()
                or 'better luck next time, **' in message_content.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                user_command = '/training' if user is not None else 'rpg training'
                if user is None:
                    try:
                        user_name = re.search(", \*\*(.+?)\*\* !", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in training message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in training message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'training', current_time)
                if not user_settings.alert_training.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'training')
                reminder_message = user_settings.alert_training.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'training', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(TrainingCog(bot))