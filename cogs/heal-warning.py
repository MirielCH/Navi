# heal-warning.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, functions, exceptions, logs, settings, strings


class HealWarningCog(commands.Cog):
    """Cog that contains the heal warning detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content

        # Hunt together
        search_strings_hunt_together = [
            'are hunting together', #English
            'cazando juntos', #Spanish
            'caçando juntos', #Portuguese
        ]
        search_strings_hunt_adv = [
            '** found a', #English
            '** encontr', #Spanish, Portuguese
        ]
        if any(search_string in message_content.lower() for search_string in search_strings_hunt_together):
            user_name = None
            interaction = await functions.get_interaction(message)
            search_patterns = [
                    r"\*\*(.+?)\*\* and \*\*(.+?)\*\*", #English
                    r"\*\*(.+?)\*\* y \*\*(.+?)\*\*", #Spanish
                    r"\*\*(.+?)\*\* e \*\*(.+?)\*\*", #Portuguese
                ]
            user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
            if user_name_match:
                user_name, partner_name = user_name_match.groups()
                user_name_encoded = await functions.encode_text(user_name)
            else:
                await functions.add_warning_reaction(message)
                await errors.log_error('User or partner not found in hunt together message for heal warning.')
                return
            user = await functions.get_interaction_user(message)
            if user is None:
                user = await functions.get_guild_member_by_name(message.guild, user_name_encoded)
            if user is None:
                await functions.add_warning_reaction(message)
                await errors.log_error('User not found in hunt together message for heal warning.', message)
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
                health_match = re.search(r'-(.+?) hp \(:heart: (.+?)/', message_content_user.lower())
            else:
                search_patterns = [
                    fr'\*\*{re.escape(user_name)}\*\* lost (.+?) hp, remaining hp is (.+?)/', #English
                    fr'\*\*{re.escape(user_name)}\*\* perdió (.+?) hp, la hp restante es (.+?)/', #Spanish
                    fr'\*\*{re.escape(user_name)}\*\* perdeu (.+?) hp, restam (.+?)/', #Portuguese
                ]
                health_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
            if not health_match:
                search_strings = [
                    f'{user_name}** lost but', #English 1
                    'but lost fighting', #English 1
                    f'{user_name}** perdió pero ', #Spanish 1
                    'pero perdió luchando', #Spanish 2
                    f'{user_name}** perdeu, mas ', #Portuguese 1
                    'mas perdeu a luta', #Portuguese 2
                ]
                if all(search_string not in message_content for search_string in search_strings):
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Health not found in hunt together message for heal warning.', message)
                    return
            if health_match:
                health_lost = int(health_match.group(1).replace(',',''))
                health_remaining = int(health_match.group(2).replace(',',''))
            else:
                health_lost = 100
                health_remaining = 0
            if health_lost > (health_remaining - (health_lost / 9)):
                if interaction is not None:
                    action = await functions.get_slash_command(user_settings, 'heal')
                else:
                    action = 'heal'
                warning = f'Hey! Time to {action}! {emojis.LIFE_POTION}'
                if not user_settings.dnd_mode_enabled:
                    if user_settings.ping_after_message:
                        await message.channel.send(f'{warning} {user.mention}')
                    else:
                        await message.channel.send(f'{user.mention} {warning}')
                else:
                    await message.channel.send(f'**{user.name}**, {warning}')

        # Hunt solo and adventure
        elif any(search_string in message_content.lower() for search_string in search_strings_hunt_adv):
            if 'horslime' in message_content.lower(): return
            user_name = None
            interaction = await functions.get_interaction(message)
            user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE_START, message_content)
            if user_name_match:
                user_name_encoded = await functions.encode_text(user_name_match.group(1))
            else:
                await functions.add_warning_reaction(message)
                await errors.log_error('User not found in hunt/adventure message for heal warning.', message)
                return
            user = await functions.get_interaction_user(message)
            if user is None:
                user = await functions.get_guild_member_by_name(message.guild, user_name_encoded)
            if user is None:
                await functions.add_warning_reaction(message)
                await errors.log_error('User not found in hunt/adventure message for heal warning.', message)
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled or not user_settings.heal_warning_enabled: return
            search_patterns = [
                r'lost (.+?) hp, remaining hp is (.+?)/', #English
                r'(?:perdió|perdiste) (.+?) hp, la hp restante es (.+?)/', #Spanish
                r'perdeu (.+?) hp, restam (.+?)/', #Spanish
            ]
            health_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
            if not health_match:
                search_strings = [
                    f'{user_name}** lost but', #English 1
                    'but lost fighting', #English 2
                    'both lost fighting', #English 3
                    f'{user_name}** perdió pero ', #Spanish 1
                    'pero perdió luchando', #Spanish 2
                    'pero perdió luchando', #Spanish 3, MISSING
                    f'{user_name}** perdeu, mas ', #Portuguese 1
                    'mas perdeu a luta', #Portuguese 2
                    'mas perdeu a luta', #Portuguese 3, MISSING
                ]
                if all(search_string not in message_content for search_string in search_strings):
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Health not found in hunt/adventure message for heal warning.', message)
                    return
            if health_match:
                health_lost = int(health_match.group(1).replace(',',''))
                health_remaining = int(health_match.group(2).replace(',',''))
            else:
                health_lost = 100
                health_remaining = 0
            if health_lost > (health_remaining - (health_lost / 10)):
                if interaction is not None:
                    action = await functions.get_slash_command(user_settings, 'heal')
                else:
                    action = 'heal'
                warning = f'Hey! Time to {action}! {emojis.LIFE_POTION}'
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