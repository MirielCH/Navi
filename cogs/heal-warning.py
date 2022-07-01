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
        search_strings = [
            'are hunting together', #English
            'stan cazando juntos', #Spanish
            'estão caçando juntos', #Portuguese
        ]
        if any(search_string in message_content.lower() for search_string in search_strings):
            user_name = None
            search_patterns = [
                    "\*\*(.+?)\*\* and \*\*(.+?)\*\*", #English
                    "\*\*(.+?)\*\* y \*\*(.+?)\*\*", #Spanish
                    "\*\*(.+?)\*\* e \*\*(.+?)\*\*", #Portuguese
                ]
            user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
            try:
                user_name = user_name_match.group(1)
                partner_name = user_name_match.group(2)
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
                user = await functions.get_guild_member_by_name(message.guild, user_name_encoded)
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
                health_match = re.search('-(.+?) hp \(:heart: (.+?)/', message_content_user.lower())
            else:
                search_patterns = [
                    f'\*\*{re.escape(user_name)}\*\* lost (.+?) hp, remaining hp is (.+?)/', #English
                    f'\*\*{re.escape(user_name)}\*\* perdió (.+?) hp, la hp restante es (.+?)/', #Spanish
                    f'\*\*{re.escape(user_name)}\*\* perdeu (.+?) hp, restam (.+?)/', #Portuguese
                ]
                health_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
            if health_match is None:
                search_strings = [
                    f'{user_name}** lost but', #English 1
                    'but lost fighting', #English 1
                    f'{user_name}** perdió pero ', #Spanish 1
                    'pero perdió luchando', #Spanish 2
                    f'{user_name}** perdeu, mas ', #Portuguese 1
                    'mas perdeu a luta', #Portuguese 2
                ]
                if all(search_string not in message_content for search_string in search_strings):
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Health not found in hunt together message for heal warning: {message_content}',
                        message
                    )
                    return
            try:
                if health_match is not None:
                    health_lost = health_match.group(1).replace(',','')
                    health_lost = int(health_lost)
                    health_remaining = health_match.group(2).replace(',','')
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
                    if user_settings.ping_after_message:
                        await message.channel.send(f'{warning} {user.mention}')
                    else:
                        await message.channel.send(f'{user.mention} {warning}')
                else:
                    await message.channel.send(f'**{user.name}**, {warning}')

        # Hunt solo and adventure
        search_strings = [
            '** found a', #English
            '** encontró', #Spanish
            '** encontrou', #Portuguese
        ]
        if any(search_string in message_content.lower() for search_string in search_strings):
            user_name = None
            try:
                user_name_match = re.search("^\*\*(.+?)\*\* ", message_content)
                user_name = user_name_match.group(1)
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
                user = await functions.get_guild_member_by_name(message.guild, user_name_encoded)
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
            search_patterns = [
                'lost (.+?) hp, remaining hp is (.+?)/', #English
                '[perdió|perdiste] (.+?) hp, la hp restante es (.+?)/', #Spanish
                'perdeu (.+?) hp, restam (.+?)/', #Spanish
            ]
            health_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
            if health_match is None:
                search_strings = [
                    f'{user_name}** lost but', #English 1
                    'but lost fighting', #English 1
                    f'{user_name}** perdió pero ', #Spanish 1
                    'pero perdió luchando', #Spanish 2
                    f'{user_name}** perdeu, mas ', #Portuguese 1
                    'mas perdeu a luta', #Portuguese 2
                ]
                if all(search_string not in message_content for search_string in search_strings):
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Health not found in hunt/adventure message for heal warning: {message_content}',
                        message
                    )
                    return
            try:
                if health_match is not None:
                    health_lost = health_match.group(1).replace(',','')
                    health_lost = int(health_lost)
                    health_remaining = health_match.group(2).replace(',','')
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
                    if user_settings.ping_after_message:
                        await message.channel.send(f'{warning} {user.mention}')
                    else:
                        await message.channel.send(f'{user.mention} {warning}')
                else:
                    await message.channel.send(f'**{user.name}**, {warning}')


# Initialization
def setup(bot):
    bot.add_cog(HealWarningCog(bot))