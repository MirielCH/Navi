# tracking.py
"""Contains commands related to command tracking"""

from math import floor
import re

import discord
from discord import utils
from discord.commands import slash_command
from discord.ext import bridge, commands

from cache import messages
from content import tracking as tracking_cmd
from database import errors, reminders, users, tracking
from resources import emojis, functions, exceptions, regex, settings


class TrackingCog(commands.Cog):
    """Cog with command tracking commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Slash commands
    @slash_command()
    @discord.option('timestring', str, description='The relative timeframe you want stats for. Example: 1d5h30m.', default=None)
    @discord.option('user', discord.User, description='User to view the stats of.', default=None)
    async def stats(self, ctx: discord.ApplicationContext, timestring: str, user: discord.User) -> None:
        """Shows your tracking stats"""
        await tracking_cmd.command_stats(self.bot, ctx, timestring, user)

    # Text commands
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
        args = ' '.join(args)
        if not user:
            user_id_match = re.match(r'(\b[\d]{16,20}\b)', args)
            if user_id_match:
                user = self.bot.get_user(int(user_id_match.group(1)))
                if not user:
                    await ctx.reply(f'No user found with id `{user_id_match.group(1)}`.')
                    return
        if user:
            if user.bot:
                await ctx.reply('Imagine trying to check the reminders of a bot.')
                return
        weeks_match = re.search(r'(\d+\s*w)', args.lower())
        days_match = re.search(r'(\d+\s*d)', args.lower())
        hours_match = re.search(r'(\d+\s*h)', args.lower())
        minutes_match = re.search(r'(\d+\s*m)', args.lower())
        seconds_match = re.search(r'(\d+\s*s)', args.lower())
        timestring = ''
        if weeks_match:
            timestring = weeks_match.group(1)
        if days_match:
            timestring = f'{timestring}{days_match.group(1)}'
        if hours_match:
            timestring = f'{timestring}{hours_match.group(1)}'
        if minutes_match:
            timestring = f'{timestring}{minutes_match.group(1)}'
        if seconds_match:
            timestring = f'{timestring}{seconds_match.group(1)}'
        if not timestring: timestring = None
        await tracking_cmd.command_stats(self.bot, ctx, timestring, user)

    # Events
    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
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
                        await tracking.insert_log_entry(user.id, message.guild.id, 'epic guard',
                                                        utils.utcnow())
                        
                # Losing time travel in area 20
                search_strings = [
                    'was severely affected by the effects of this area and lost', #English
                    'was severely affected by the effects of this area and lost', #TODO: Spanish
                    'was severely affected by the effects of this area and lost', #TODO: Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings):
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a user for a20 lost time travel message.', message)
                            return
                        user_command_message = (
                            await messages.find_message(message.channel.id, user_name=user_name)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for a20 lost time travel message.',
                                                message)
                            return
                        user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled: return
                    lost_tt_count_match = re.search(r' (\d+) <:', message_content)
                    if lost_tt_count_match:
                        lost_tt_count = int(lost_tt_count_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a  lost tt count in a20 lost time travel message.', message)
                        return
                    time_travel_count_new = user_settings.time_travel_count - lost_tt_count
                    trade_daily_total = floor(100 * (time_travel_count_new + 1) ** 1.35)
                    await user_settings.update(time_travel_count=time_travel_count_new, trade_daily_total=trade_daily_total)
                        

            if message.embeds:
                # Last time travel
                try:
                    embed_description = str(message.embeds[0].description)
                except:
                    return
                search_strings = [
                    'has traveled in time', #English
                    'viajou no tempo', #Spanish
                    'tempo de viagem', #Portuguese
                ]
                if any(search_string in embed_description.lower() for search_string in search_strings):
                    user_command_message = None
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        search_patterns = [
                            r'\*\*(.+?)\*\* has', #English
                            r'\*\*(.+?)\*\* viajó', #English
                            r'\*\*(.+?)\*\* tempo', #Portuguese
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, embed_description)
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
                    tt_time = message.created_at
                    kwargs = {
                        'last_tt': tt_time.isoformat(sep=' '),
                        'inventory_bread': 0,
                        'inventory_carrot': 0,
                        'inventory_potato': 0,
                        'inventory_seed_bread': 0,
                        'inventory_seed_potato': 0,
                        'inventory_seed_carrot': 0,
                        'inventory_ruby': 0,
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
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(TrackingCog(bot))