# valentine.py

import asyncio
from datetime import timedelta
from math import floor
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import cooldowns, errors, reminders, users
from resources import exceptions, functions, regex, settings, strings


class ValentineCog(commands.Cog):
    """Cog that contains the valentine detection commands"""
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
            embed_author = message_title = icon_url = ''
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: message_title = str(embed.title)
            
            # Love share cooldown
            search_strings = [
                'you have shared a life potion recently', #English
                'you have shared a life potion recently', #TODO: Spanish
                'you have shared a life potion recently', #TODO: Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOVE_SHARE)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        return
                    interaction_user = user_command_message.author
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                if not embed_users:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find embed user for the love share cooldown message.', message)
                        return
                if interaction_user not in embed_users: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_love_share.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                user_command = await functions.get_slash_command(user_settings, 'love share')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in love share cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_love_share.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'love-share', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            
            # Love share
            search_strings = [
                " life potion with **", #English
                " life potion with **", #TODO: Spanish
                " life potion with **", #TODO: Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for love share message.',
                                                message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOVE_SHARE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the love share message.',
                                                message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_love_share.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'love share')
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = utils.utcnow() - bot_answer_time
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                time_left_seconds = (actual_cooldown
                                     * (settings.DONOR_COOLDOWNS[user_donor_tier] - (1 - user_settings.user_pocket_watch_multiplier))
                                     - floor(time_elapsed.total_seconds()))
                if user_settings.chocolate_box_unlocked:
                    time_left_seconds *= settings.CHOCOLATE_BOX_MULTIPLIER # Unclear if accurate
                time_left = timedelta(seconds=time_left_seconds)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_love_share.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'love-share', time_left,
                                                        message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'love-share'))
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(ValentineCog(bot))