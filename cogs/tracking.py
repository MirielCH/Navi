# tracking.py
"""Contains commands related to command tracking"""

from datetime import datetime
import re

import discord
from discord.commands import slash_command, Option
from discord.ext import commands

from cache import messages
from content import tracking as tracking_cmd
from database import errors, reminders, users, tracking
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
        user: Option(discord.User, 'User to view the stats of. Shows your own stats it empty.', default=None),
    ) -> None:
        """Lists your command statistics"""
        await tracking_cmd.command_stats(self.bot, ctx, timestring, user)

    @commands.command(name='stats', aliases=('stat','st','statistic', 'statistics'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def prefix_stats(self, ctx: commands.Context, *args: str) -> None:
        """Lists all stats (prefix version)"""
        user = None
        for mentioned_user in ctx.message.mentions.copy():
            if mentioned_user == self.bot.user:
                ctx.message.mentions.remove(mentioned_user)
                break
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            if user.bot:
                await ctx.reply('Imagine trying to check the reminders of a bot.')
                return
        args = ''.join(args)
        timestring = re.sub(r'<@!?[0-9]+>', '', args.lower())
        if timestring == '': timestring = None
        await tracking_cmd.command_stats(self.bot, ctx, timestring, user)

    # Events
    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Fires when a message is sent"""
        if message.author.id in [settings.EPIC_RPG_ID, settings.TESTY_ID]:
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
                    'viajou no tempo', #Spanish
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
                                await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await errors.log_error('User name not found in time travel message.', message)
                            return
                        user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled: return
                    tt_time = message.created_at.replace(microsecond=0, tzinfo=None)
                    kwargs = {
                        'last_tt': tt_time.isoformat(sep=' '),
                        'inventory_bread': 0,
                        'inventory_carrot': 0,
                        'inventory_potato': 0,
                        'inventory_seed_bread': 0,
                        'inventory_seed_potato': 0,
                        'inventory_seed_carrot': 0,
                        'inventory_ruby': 0,
                        'trade_daily_total': 0,
                    }
                    await user_settings.update(**kwargs)
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'lottery')
                        await reminder.delete()
                    except exceptions.NoDataFoundError:
                        pass
                    try:
                        user_command = await functions.get_slash_command(user_settings, 'farm')
                        reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'farm')
                        await reminder.update(message=reminder_message)
                    except exceptions.NoDataFoundError:
                        pass
                    if user_settings.last_tt == tt_time and user_settings.bot_enabled and user_settings.reactions_enabled:
                        await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(TrackingCog(bot))