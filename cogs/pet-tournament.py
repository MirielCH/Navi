# pet-tournament.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class PetTournamentCog(commands.Cog):
    """Cog that contains the horse race detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if not message.embeds:
            message_content = message.content
            if 'pet successfully sent to the pet tournament!' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().replace(' ','').startswith('rpgpet') and ' tournament ' in msg.content.lower()
                                and not msg.author.bot):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the pet tournament message.',
                            message
                        )
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pet_tournament.enabled: return
                timestring = re.search("next pet tournament is in \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_footer = embed_author = ''
            if embed.description: embed_description = str(embed.description)
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.footer: embed_footer = str(embed.footer.text)

            # Pet list
            if 'pets can collect items and coins, more information' in embed_description.lower():
                pet_tournament_search = re.search('pet id "(.+?)" registered', embed_footer.lower())
                if pet_tournament_search is None:
                    return
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s pets", embed_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in pet list message for pet tournament: {embed_author}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in pet list message for pet tournament: {embed_author}',
                        message
                    )
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
                reminder_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'pet-tournament', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

# Initialization
def setup(bot):
    bot.add_cog(PetTournamentCog(bot))