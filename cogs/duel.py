# duel.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class DuelCog(commands.Cog):
    """Cog that contains the duel detection commands"""
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
            message_author = message_title = icon_url = message_description = message_field0_name = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)
            if embed.description: message_description = embed.description
            if embed.fields:
                message_field0_name = embed.fields[0].name

            # Duel cooldown
            search_strings = [
                'you have been in a duel recently', #English
                'estuviste en un duelo recientemente', #Spanish
                'você estava em um duelo recentemente', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_DUEL)
                    )
                    if user_command_message is None: return
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
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in duel cooldown message.', message)
                        return
                if interaction_user not in embed_users: return
                if not user_settings.bot_enabled or not user_settings.alert_duel.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'duel')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in duel cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_duel.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'duel', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Duel
            search_strings_author = [
                 "— duel", #All languages
            ]
            search_strings_field = [
                 "** won!", #English
                 "** ganó!", #Spanish
                 "** ganhou!", #Portugiesisch
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings_author)
                and any(search_string in message_field0_name.lower() for search_string in search_strings_field)):
                user_id = user_name = user_command_message = duel_user = None
                created_reminder = False
                time_left = None
                duel_users = []
                interaction_user = await functions.get_interaction_user(message)
                duelled_users = message_description.split('\n')
                if interaction_user is None:
                    interaction_user_name_match = re.search(r'\*\*(.+?)\*\* ~-~', duelled_users[0])
                    interaction_user_name = interaction_user_name_match.group(1)
                    interaction_users = await functions.get_guild_member_by_name(message.guild, interaction_user_name)
                    if len(interaction_users) > 1:
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_DUEL,
                                                    user_name=interaction_user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Interaction user not found for duel message.', message)
                        return
                    interaction_user = user_command_message.author
                    for user in user_command_message.mentions:
                        if user.id != settings.EPIC_RPG_ID:
                            duel_user = user
                            break
                try:
                    interaction_user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    interaction_user_settings = None
                if interaction_user_settings is not None:
                    time_left = await functions.calculate_time_left_from_cooldown(message, interaction_user_settings,
                                                                                  'duel')
                    if time_left < timedelta(0): return
                    if interaction_user_settings.bot_enabled and interaction_user_settings.alert_duel.enabled:
                        user_command = await functions.get_slash_command(interaction_user_settings, 'duel')
                        reminder_message = interaction_user_settings.alert_duel.message.replace('{command}', user_command)
                        reminder: reminders.Reminder = (
                            await reminders.insert_user_reminder(interaction_user.id, 'duel', time_left,
                                                                 message.channel.id, reminder_message)
                            )
                        await functions.add_reminder_reaction(message, reminder, interaction_user_settings)
                        created_reminder = True
                if duel_user is None:
                    duel_user_name_match = re.search(r'\*\*(.+?)\*\* ~-~', duelled_users[1])
                    if duel_user_name_match:
                        duel_user_name = duel_user_name_match.group(1)
                        duel_users = await functions.get_guild_member_by_name(message.guild, duel_user_name)
                        if len(duel_users) > 1:
                            return
                    if not duel_user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Duelled user not found in duel message.', message)
                        return
                    if not duel_users: return
                    duel_user = duel_users[0]
                try:
                    duel_user_settings: users.User = await users.get_user(duel_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if duel_user_settings.bot_enabled and duel_user_settings.alert_duel.enabled:
                    time_left = await functions.calculate_time_left_from_cooldown(message, duel_user_settings,
                                                                                    'duel')
                    if time_left < timedelta(0): return
                    user_command = await functions.get_slash_command(duel_user_settings, 'duel')
                    reminder_message = duel_user_settings.alert_duel.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(duel_user.id, 'duel', time_left,
                                                             message.channel.id, reminder_message)
                    )
                    if not created_reminder:
                        await functions.add_reminder_reaction(message, reminder, duel_user_settings)


# Initialization
def setup(bot):
    bot.add_cog(DuelCog(bot))