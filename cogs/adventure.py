# adventure.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings


class AdventureCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
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

            # Adventure cooldown
            if 'you have already been in an adventure' in message_title.lower():
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/adventure'
                else:
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
                                f'User not found in adventure cooldown message: {message.embeds[0].fields}'
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
                        f'User not found in adventure cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_adventure.enabled: return
                if user_command is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ') and ' adv' in msg.content.lower()
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the adventure cooldown message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                    arguments = ''
                    for argument in user_command.split():
                        if argument in ('adv', 'adventure') and 'adventure' not in arguments:
                            arguments = f'{arguments} adventure'
                        if argument in ('h', 'hardmode') and 'hardmode' not in arguments:
                            arguments = f'{arguments} hardmode'
                    user_command = f'rpg {arguments.strip()}'
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'adventure', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Adventure
            if ('** found a' in message_content.lower()
                and any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)):
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/adventure'
                    if '(but stronger)' in message_content.lower(): user_command = f'{user_command} mode: hardmode'
                else:
                    user_command = 'rpg adventure'
                    if '(but stronger)' in message_content.lower(): user_command = f'{user_command} hardmode'
                    user_name = None
                    try:
                        user_name = re.search("^\*\*(.+?)\*\* found a", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in adventure message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in adventure message: {message_content}',
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
                    await tracking.insert_log_entry(user.id, message.guild.id, 'adventure', current_time)
                if not user_settings.alert_adventure.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'adventure')
                reminder_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'adventure', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'OMEGA lootbox': emojis.SURPRISE,
                        'GODLY lootbox': emojis.SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if stuff_name in message_content:
                            await message.add_reaction(stuff_emoji)
                await functions.add_reminder_reaction(message, reminder, user_settings)
                # Add an F if the user died
                if ((message_content.find(f'**{user.name}** lost but ') > -1)
                    or (message_content.find('but lost fighting') > -1)):
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.RIP)


# Initialization
def setup(bot):
    bot.add_cog(AdventureCog(bot))