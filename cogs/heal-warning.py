# heal-warning.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, functions, exceptions, logs, settings


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

        # Hunt together
        if 'are hunting together' in message_content.lower():
            user_name = None
            try:
                user_name_search = re.search("\*\*(.+?)\*\* and \*\*(.+?)\*\*", message_content)
                user_name = user_name_search.group(1)
                partner_name = user_name_search.group(2)
                user_name_encoded = await functions.encode_text(user_name)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User or partner not found in hunt together message for heal warning: {message_content}'
                )
                return
            user = await functions.get_interaction_user(message)
            if user is None:
                user = await functions.get_guild_member_by_name(message.guild, user_name)
            if user is None:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in hunt together message for heal warning: {message_content}',
                    message
                )
                logs.logger.error(
                    f'User not found in hunt together message for heal warning: {message_content}\n'
                    f'Full guild.members list:\n{message.guild.members}'
                )
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.heal_warning_enabled: return
            if message_content.startswith('__'):
                partner_start = message_content.rfind(partner_name)
                message_content_user = message_content[:partner_start]
                health_search = re.search('-(.+?) HP \(:heart: (.+?)/', message_content_user)
            else:
                health_search = re.search(f'\*\*{re.escape(user_name)}\*\* lost (.+?) HP, remaining HP is (.+?)/', message_content)
            if health_search is None:
                if (f'{user_name}** lost but' not in message_content
                    and 'but lost fighting' not in message_content.lower()):
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Health not found in hunt together message for heal warning: {message_content}',
                        message
                    )
                    return
            try:
                if health_search is not None:
                    health_lost = health_search.group(1).replace(',','')
                    health_lost = int(health_lost)
                    health_remaining = health_search.group(2).replace(',','')
                    health_remaining = int(health_remaining)
                else:
                    health_lost = 100
                    health_remaining = 0
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Health not found in hunt together message for heal warning: {error}',
                    message
                )
                return
            if health_lost > (health_remaining - (health_lost / 9)):
                warning = f'Hey! Time to heal! {emojis.LIFE_POTION}'
                if not user_settings.dnd_mode_enabled:
                    await message.channel.send(f'{user.mention} {warning}')
                else:
                    await message.channel.send(f'**{user.name}**, {warning}')

        # Hunt solo and adventure
        elif '** found a' in message_content.lower():
            user_name = None
            try:
                user_name_search = re.search("^\*\*(.+?)\*\* ", message_content)
                user_name = user_name_search.group(1)
                user_name_encoded = await functions.encode_text(user_name)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in hunt/adventure message for heal warning: {message_content}',
                    message
                )
                return
            user = await functions.get_interaction_user(message)
            if user is None:
                user = await functions.get_guild_member_by_name(message.guild, user_name)
            if user is None:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in hunt/adventure message for heal warning: {message_content}',
                    message
                )
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.heal_warning_enabled: return
            health_search = re.search('Lost (.+?) HP, remaining HP is (.+?)/', message_content)
            if health_search is None:
                if (f'{user_name}** lost but' not in message_content
                    and 'but lost fighting' not in message_content.lower()):
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Health not found in hunt/adventure message for heal warning: {message_content}',
                        message
                    )
                    return
            try:
                if health_search is not None:
                    health_lost = health_search.group(1).replace(',','')
                    health_lost = int(health_lost)
                    health_remaining = health_search.group(2).replace(',','')
                    health_remaining = int(health_remaining)
                else:
                    health_lost = 100
                    health_remaining = 0
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Health not found in hunt/adventure message for heal warning: {error}',
                    message
                )
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