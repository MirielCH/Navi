# pet-tournament.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class PetTournamentCog(commands.Cog):
    """Cog that contains the horse race detection"""
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
        if not message.embeds:
            message_content = message.content
            search_strings = [
                'pet successfully sent to the pet tournament!', #English
                'mascota exitosamente enviada al torneo de mascotas!', #Spanish
                'pet enviado com sucesso para o torneio de pets!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+pets?\s+tournament\s+[a-z]+\b"
                        )
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
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_footer = embed_author = ''
            if embed.description: embed_description = str(embed.description)
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.footer: embed_footer = str(embed.footer.text)

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
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet list message for pet tournament.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in pet list message for pet tournament.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pet_tournament.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0, tzinfo=None)
                today_20pm = datetime.utcnow().replace(hour=20, minute=0, second=0, microsecond=0)
                today_8am = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
                tomorrow_8am = today_8am + timedelta(days=1)
                if today_8am > current_time:
                    time_left = today_8am - current_time
                elif today_20pm > current_time:
                    time_left = today_20pm - current_time
                else:
                    time_left = tomorrow_8am - current_time
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

# Initialization
def setup(bot):
    bot.add_cog(PetTournamentCog(bot))