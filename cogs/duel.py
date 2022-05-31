# duel.py

import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class DuelCog(commands.Cog):
    """Cog that contains the duel detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Daily cooldown
            if 'you have been in a duel recently' in message_title.lower():
                user_id = user_name = None
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgduel'):
                                interaction_user = msg.author
                                break
                    if interaction_user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find an interaction user for the duel cooldown message.',
                            message
                        )
                        return
                try:
                    user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                except:
                    try:
                        user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'Embed user not found in duel cooldown message: {message.embeds[0].fields}',
                            message
                        )
                        return
                if user_id is not None:
                    embed_user = await message.guild.fetch_member(user_id)
                else:
                    embed_user = await functions.get_guild_member_by_name(message.guild, user_name)
                if embed_user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Embed user not found in duel cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if embed_user != interaction_user: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_duel: return
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_duel.message.replace('{command}', 'rpg duel')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'duel', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(DuelCog(bot))