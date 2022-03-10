# sleepy-potion.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, settings


class SleepyPotionCog(commands.Cog):
    """Cog that contains the sleepy potion detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content
        # Sleepy Potion
        if 'has slept for a day' in message_content.lower():
            user_name = user = None
            try:
                user_name = re.search("^\*\*(.+?)\*\* drinks", message_content).group(1)
                user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in sleepy potion message: {message}')
                return
            for member in message.guild.members:
                member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                if member_name == user_name:
                    user = member
                    break
            if user is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in sleepy potion message: {message}')
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled: return
            await reminders.reduce_reminder_time(user.id, timedelta(days=1))
            await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(SleepyPotionCog(bot))