# arena.py

from datetime import timedelta
import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class ArenaCog(commands.Cog):
    """Cog that contains the arena detection commands"""
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
        if not message.embeds: return
        embed: discord.Embed = message.embeds[0]
        message_author = message_title = icon_url = ''
        if embed.author is not None:
            message_author = str(embed.author.name)
            icon_url = embed.author.icon_url
        if embed.title is not None: message_title = str(embed.title)

        # Arena cooldown
        search_strings = [
            'you have started an arena recently', #English
            'empezaste una arena recientemente', #Spanish
            'você recentemente iniciou uma arena', #Portuguese
        ]
        if any(search_string in message_title.lower() for search_string in search_strings):
            user_id = user_name = user_command_message = None
            embed_users = []
            interaction_user = await functions.get_interaction_user(message)
            if interaction_user is None:
                user_command_message = (
                    await messages.find_message(message.channel.id, regex.COMMAND_ARENA)
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
                    embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                if not user_name_match or not embed_users:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Embed user not found for arena cooldown message.', message)
                    return
            if interaction_user not in embed_users: return
            if not user_settings.bot_enabled or not user_settings.alert_arena.enabled: return
            if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
            user_command = await functions.get_slash_command(user_settings, 'arena')
            timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                       message_title)
            if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in arena cooldown message.', message)
                    return
            timestring = timestring_match.group(1)
            time_left = await functions.calculate_time_left_from_timestring(message, timestring)
            if time_left < timedelta(0): return
            reminder_message = user_settings.alert_arena.message.replace('{command}', user_command)
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(interaction_user.id, 'arena', time_left,
                                                     message.channel.id, reminder_message)
            )
            await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(ArenaCog(bot))