# heal-warning.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, functions, exceptions, settings


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

        if '** found a' in message_content.lower() or 'are hunting together' in message_content.lower():
            user_name = None
            try:
                user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                user_name_encoded = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in hunt/adventure message for heal warning: {message_content}')
                return
            user = await functions.get_interaction_user(message)
            if user is None:
                for member in message.guild.members:
                    member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    if member_name == user_name_encoded:
                        user = member
                        break
            if user is None:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'User not found in hunt/adventure message for heal warning: {message_content}')
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
                if (f'{user_name}** lost but' not in message_content
                    and 'but lost fighting' not in message_content.lower()):
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(f'Health not found in hunt/adventure message for heal warning: {message_content}')
                    return
            try:
                if health_search is not None:
                    health_lost = int(health_search.group(1))
                    health_remaining = int(health_search.group(2))
                else:
                    health_lost = 100
                    health_remaining = 0
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(f'Health not found in hunt/adventure message for heal warning: {error}')
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