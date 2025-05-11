# pets_tournament.py

import asyncio
from datetime import timedelta
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class PetsTournamentCog(commands.Cog):
    """Cog that contains the horse race detection"""
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
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if not message.embeds:
            message_content = message.content
            search_strings = [
                'pet successfully sent to the pet tournament!', #English
                'mascota exitosamente enviada al torneo de mascotas!', #Spanish
                'pet enviado com sucesso para o torneio de pets!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PETS_TOURNAMENT)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the pet tournament message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pet_tournament.enabled: return
                search_patterns = [
                    r'next pet tournament is in \*\*(.+?)\*\*', #English
                    r'el siguiente torneo es el \*\*(.+?)\*\*', #Spanish
                    r'o próximo torneio é em \*\*(.+?)\*\*', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in pet tournament message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                time_left = time_left + timedelta(seconds=random.randint(0, 120))
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                        message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'pet-tournament'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_footer = embed_author = ''
            if embed.description is not None: embed_description = str(embed.description)
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.footer is not None: embed_footer = str(embed.footer.text)

            # Pet list
            search_strings = [
                'pets can collect items and coins, more information', #English
                'las mascotas puedes recoger items y coins, más información', #Spanish
                'pets podem coletar itens e coins, mais informações', #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                search_patterns = [
                    r'pet id "(.+?)" is registered', #English
                    r'la mascota "(.+?)" está registrada', #Spanish
                    r'de pet "(.+?)" está registrado', #Portuguese
                ]
                pet_tournament_match = await functions.get_match_from_patterns(search_patterns, embed_footer.lower())
                if not pet_tournament_match: return
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PETS,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet list message for pet tournament.', message)
                            return
                        user = user_command_message.author
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in pet list message for pet tournament.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pet_tournament.enabled: return
                current_time = utils.utcnow()
                today_20pm = current_time.replace(hour=20, minute=0, second=0, microsecond=0)
                today_8am = current_time.replace(hour=8, minute=0, second=0, microsecond=0)
                tomorrow_8am = today_8am + timedelta(days=1)
                if today_8am > current_time:
                    time_left = today_8am - current_time
                elif today_20pm > current_time:
                    time_left = today_20pm - current_time
                else:
                    time_left = tomorrow_8am - current_time
                time_left = time_left + timedelta(seconds=random.randint(0, 120))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(PetsTournamentCog(bot))