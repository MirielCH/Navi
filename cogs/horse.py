# horse.py

from datetime import timedelta
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, logs, regex, settings


class HorseCog(commands.Cog):
    """Cog that contains the horse detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
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
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = str((embed.author.icon_url))
            if embed.title is not None: message_title = str(embed.title)

            # Horse cooldown
            search_strings = [
                'you have used this command recently', #English
                'usaste este comando recientemente', #Spanish
                'você usou este comando recentementesh', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HORSE)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Interaction user not found in horse cooldown message.', message)
                        return
                    interaction_user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in horse cooldown message.', message)
                        return
                if interaction_user not in embed_users: return
                if not user_settings.bot_enabled or not user_settings.alert_horse_breed.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                command_breed = await functions.get_slash_command(user_settings, 'horse breeding')
                command_race = await functions.get_slash_command(user_settings, 'horse race')
                user_command = f"{command_breed} or {command_race}"
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                        message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in horse cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'horse', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Horse breeding
            search_strings_author = [
               " — horse breeding", # All languages
            ]
            search_strings_title = [
                f'breeding request accepted!', # English
                f'petición de horse breeding aceptada!', # Spanish
                f'pedido de horse breeding aceito!', # Portuguese
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings_author) and
                any(search_string in message_title.lower() for search_string in search_strings_title)):
                user_id = user_name = user_command_message = None
                breeding_users = []
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else True
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HORSE_BREEDING,
                                                        user_name=user_name)
                        )
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in horse breeding message.', message)
                        return
                    if user is None:
                        user = user_command_message.author
                breeding_users.append(user)
                if not slash_command:
                    for mentioned_user in user_command_message.mentions:
                        if mentioned_user == message.author: continue
                        breeding_users.append(mentioned_user)
                if slash_command:
                    breeding_partner_line = embed.description.split('\n')[1]
                    breeding_partner_name_match = re.search(r'^\*\*(.+?)\*\* ', breeding_partner_line)
                    breeding_partner_name = breeding_partner_name_match.group(1)
                    guild_members = await functions.get_member_by_name(self.bot, message.guild, breeding_partner_name)
                    breeding_users.append(guild_members[0])
                for breeding_user in breeding_users:
                    try:
                        user_settings: users.User = await users.get_user(breeding_user.id)
                    except exceptions.FirstTimeUserError:
                        continue
                    if not user_settings.bot_enabled or not user_settings.alert_horse_breed.enabled: continue
                    user_command = await functions.get_slash_command(user_settings, 'horse breeding')
                    time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'horse')
                    if time_left < timedelta(0): continue
                    reminder_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                       await reminders.insert_user_reminder(breeding_user.id, 'horse', time_left,
                                                            message.channel.id, reminder_message)
                    )           
                    if not message.reactions:
                        await functions.add_reminder_reaction(message, reminder, user_settings)


        if not message.embeds:
            message_content = message.content
            
            # Omega horse token
            search_strings = [
                'horse cooldown got reset', #English
                'cooldown de horse reiniciado', #Spanish
                'cooldown do horse foi reiniciado', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r"^\*\*(.+?)\*\*,", message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_OMEGA_HORSE_TOKEN,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User name not found in omega horse token message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_horse_breed.enabled: return
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'horse')
                except exceptions.NoDataFoundError:
                    return
                await reminder.delete()
                if reminder.record_exists:
                    logs.logger.error(f'{utils.utcnow()}: Had an error deleting the horse reminder.')
                else:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(HorseCog(bot))