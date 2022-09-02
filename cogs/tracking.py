# tracking.py
"""Contains commands related to command tracking"""

from datetime import datetime
from email.policy import default

import discord
from discord.commands import slash_command, Option
from discord.ext import commands

from content import tracking as tracking_cmd
from database import errors, users, tracking
from resources import emojis, functions, exceptions, regex, settings


class TrackingCog(commands.Cog):
    """Cog with command tracking commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @slash_command()
    async def stats(
        self,
        ctx: discord.ApplicationContext,
        timestring: Option(str, 'The relative timeframe you want stats for. Example: 1d5h30m.', default=None),
    ) -> None:
        """Lists your command statistics"""
        await tracking_cmd.command_stats(self.bot, ctx, timestring)

    @commands.command(name='stats', aliases=('stat','st','statistic', 'statistics'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def prefix_stats(self, ctx: commands.Context, *args: str) -> None:
        """Lists all stats (prefix version)"""
        timestring = ''.join(args).lower()
        await tracking_cmd.command_stats(self.bot, ctx, timestring)

    # Events
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Fires when a message is sent"""
        if message.author.id == settings.EPIC_RPG_ID:
            if not message.embeds:
                message_content = message.content
                # Epic Guard
                search_strings = [
                    'we have to check you are actually playing', #English
                    'tenemos que revisar que realmente estés jugando', #Spanish
                    'temos que verificar se você está realmente jogando', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings):
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        if message.mentions:
                            user = message.mentions[0]
                        else:
                            return
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if user_settings.tracking_enabled and user_settings.bot_enabled:
                        current_time = datetime.utcnow().replace(microsecond=0)
                        await tracking.insert_log_entry(user.id, message.guild.id, 'epic guard', current_time)

            if message.embeds:
                # Last time travel
                try:
                    message_content = str(message.embeds[0].description)
                except:
                    return
                search_strings = [
                    'has traveled in time', #English
                    'viajó en el tiempo', #Spanish
                    'tempo de viagem', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings):
                    user_command_message = None
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        search_patterns = [
                            r'\*\*(.+?)\*\* has', #English
                            r'\*\*(.+?)\*\* viajó', #English
                            r'\*\*(.+?)\*\* tempo', #Portuguese
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await functions.get_message_from_channel_history(
                                    message.channel, regex.COMMAND_TIME_TRAVEL,
                                    user_name=user_name
                                )
                            )
                        if not user_name_match or user_command_message is None:
                            await errors.log_error('User name not found in time travel message.', message)
                            return
                        user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    tt_time = message.created_at.replace(microsecond=0, tzinfo=None)
                    await user_settings.update(last_tt=tt_time.isoformat(sep=' '))
                    if user_settings.last_tt == tt_time and user_settings.bot_enabled and user_settings.reactions_enabled:
                        await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(TrackingCog(bot))