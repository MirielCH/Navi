# arena.py

import re

import discord
from discord.ext import commands
from datetime import datetime

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class ArenaCog(commands.Cog):
    """Cog that contains the arena detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if not message.embeds: return
        embed: discord.Embed = message.embeds[0]
        message_author = message_title = icon_url = ''
        if embed.author:
            message_author = str(embed.author.name)
            icon_url = embed.author.icon_url
        if embed.title: message_title = str(embed.title)

        # Horse breed
        if 'you have started an arena recently' in message_title.lower():
            user_id = user_name = None
            user = await functions.get_interaction_user(message)
            user_command = '/arena' if user is not None else 'rpg arena'
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
                            f'User not found in arena cooldown message: {message.embeds[0].fields}',
                            message
                        )
                        return
                if user_id is not None:
                    user = await message.guild.fetch_member(user_id)
                else:
                    for member in message.guild.members:
                        member_name = await functions.encode_text(member.name)
                        if member_name == user_name:
                            user = member
                            break
            if user is None:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in arena cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.alert_arena.enabled: return
            timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
            time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
            bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
            current_time = datetime.utcnow().replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            time_left = time_left - time_elapsed
            reminder_message = user_settings.alert_arena.message.replace('{command}', user_command)
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, 'arena', time_left,
                                                     message.channel.id, reminder_message)
            )
            if reminder.record_exists:
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)


# Initialization
def setup(bot):
    bot.add_cog(ArenaCog(bot))