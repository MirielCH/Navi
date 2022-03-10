# training-helper.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, functions, settings


class TrainingHelperCog(commands.Cog):
    """Cog that contains the training helper detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content
        # Training helper
        if '** is training in the' in message_content.lower() and not 'in the mine!' in message_content.lower():
            user_name = user = None
            try:
                user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in training helper message: {message}')
                return
            for member in message.guild.members:
                member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                if member_name == user_name:
                    user = member
                    break
            if user is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in training helper message: {message}')
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.training_helper_enabled: return
            answer = functions.get_training_answer(message_content.lower())
            await message.reply(f'`{answer}`')


# Initialization
def setup(bot):
    bot.add_cog(TrainingHelperCog(bot))