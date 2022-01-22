# heal-warning.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, settings


class HealWarningCog(commands.Cog):
    """Cog that contains the heal warning detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content

        if '** found and killed' in message_content.lower() or 'are hunting together' in message_content.lower():
            user_name = user = None
            try:
                user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                user_name_encoded = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(error)
                return
            for member in message.guild.members:
                member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                if member_name == user_name_encoded:
                    user = member
                    break
            if user is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in training/adventure message: {message}')
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.heal_warning_enabled: return
            if 'found and killed' in message_content.lower():
                health_search = re.search('Lost (.+?) HP, remaining HP is (.+?)/', message_content)
            else:
                health_search = re.search(f'\*\*{user_name}\*\* lost (.+?) HP, remaining HP is (.+?)/', message_content)
            if health_search is None:
                if f'{user_name}** lost but' in message_content.lower() or 'but lost fighting' in message_content.lower():
                    return
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'Health not found in training/adventure message: {message_content}')
                return
            try:
                health_lost = int(health_search.group(1))
                health_remaining = int(health_search.group(2))
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'Health not found in training/adventure message. {error}')
                return
            if health_lost > (health_remaining - (health_lost / 10)):
                warning = f'Hey! Time to heal! {emojis.LIFE_POTION}'
                if not user_settings.dnd_mode_enabled:
                    await message.channel.send(f'{user.mention} {warning}')
                else:
                    await message.channel.send(f'**{user.name}**, {warning}')


# Initialization
def setup(bot):
    bot.add_cog(HealWarningCog(bot))