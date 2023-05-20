# tracking.py
"""Contains commands related to command tracking"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union

import discord
from discord.ext import commands

from database import users, tracking
from resources import emojis, functions, exceptions, settings, strings, views


# --- Commands ---
async def command_stats(
    bot: discord.Bot,
    ctx: Union[commands.Context, discord.ApplicationContext, discord.Message],
    timestring: Optional[str] = None,
    user: Optional[discord.User] = None,
) -> None:
    """Lists all stats"""
    if user is not None and user != ctx.author:
        user_mentioned = True
    else:
        user = ctx.author
        user_mentioned = False
    try:
        user_settings: users.User = await users.get_user(user.id)
    except exceptions.FirstTimeUserError:
        if user == ctx.author:
            raise
        else:
            await functions.reply_or_respond(ctx, 'This user is not registered with this bot.', True)
            return
    if timestring is None:
        time_left = timedelta(0)
        embed = await embed_stats_overview(ctx, user)
        embed_function = embed_stats_overview
    else:
        try:
            timestring = await functions.check_timestring(timestring)
        except exceptions.InvalidTimestringError as error:
            msg_error = (
                f'{error}\n'
                f'Supported time codes: `w`, `d`, `h`, `m`, `s`\n\n'
                f'Examples:\n'
                f'{emojis.BP} `30s`\n'
                f'{emojis.BP} `1h30m`\n'
                f'{emojis.BP} `7d`\n'
            )
            await functions.reply_or_respond(ctx, msg_error, True)
            return
        try:
            time_left = await functions.parse_timestring_to_timedelta(timestring)
        except OverflowError as error:
            await ctx.reply(error)
            return
        if time_left.days > 28: time_left = timedelta(days=time_left.days)
        if time_left.days > 365:
            await ctx.reply('The maximum time is 365d, sorry.')
            return
        embed = await embed_stats_timeframe(ctx, user, time_left)
        embed_function = embed_stats_timeframe
    if not user_mentioned:
        view = views.StatsView(bot, ctx, user_settings, user_mentioned, time_left, embed_function)
    else:
        view = None
    if isinstance(ctx, discord.ApplicationContext):
        interaction_message = await ctx.respond(embed=embed, view=view)
    else:
        interaction_message = await ctx.reply(embed=embed, view=view)
    if not user_mentioned:
        view.interaction_message = interaction_message
        await view.wait()


# --- Embeds ---
async def embed_stats_overview(ctx: commands.Context, user: discord.User,
                               time_left: timedelta = timedelta(0)) -> discord.Embed:
    """Stats overview embed"""

    async def command_count(command: str, timeframe: timedelta) -> str:
        try:
            report = await tracking.get_log_report(user.id, command, timeframe)
            text = f'{emojis.BP} `{report.command}`: {report.command_count:,}'
        except exceptions.NoDataFoundError:
            text = f'{emojis.BP} `{command}`: 0'

        return text

    user_settings: users.User = await users.get_user(user.id)
    field_last_1h = field_last_12h = field_last_24h = field_last_7d = field_last_4w = field_last_1y = field_last_tt = ''
    current_time = datetime.utcnow().replace(microsecond=0)
    for command in strings.TRACKED_COMMANDS:
        last_1h = await command_count(command, timedelta(hours=1))
        field_last_1h = f'{field_last_1h}\n{last_1h}'
        last_12h = await command_count(command, timedelta(hours=12))
        field_last_12h = f'{field_last_12h}\n{last_12h}'
        last_24h = await command_count(command, timedelta(hours=24))
        field_last_24h = f'{field_last_24h}\n{last_24h}'
        last_7d = await command_count(command, timedelta(days=7))
        field_last_7d = f'{field_last_7d}\n{last_7d}'
        last_4w = await command_count(command, timedelta(days=28))
        field_last_4w = f'{field_last_4w}\n{last_4w}'
        last_1y = await command_count(command, timedelta(days=365))
        field_last_1y = f'{field_last_1y}\n{last_1y}'
        last_tt = await command_count(command, current_time-user_settings.last_tt)
        field_last_tt = f'{field_last_tt}\n{last_tt}'
    try:
        timestamp = user_settings.last_tt.replace(tzinfo=timezone.utc).timestamp()
    except OSError as error: # Windows throws an error if datetime is set to 0 apparently
        timestamp = 0
    field_last_tt = f'{field_last_tt.strip()}\n\nYour last TT was on <t:{int(timestamp)}:f>.'

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user.name}\'s stats'.upper(),
        description = '**Command tracking is currently turned off!**' if not user_settings.tracking_enabled else ''
    )
    embed.add_field(name='LAST HOUR', value=field_last_1h, inline=True)
    embed.add_field(name='LAST 12 HOURS', value=field_last_12h, inline=True)
    embed.add_field(name='LAST 24 HOURS', value=field_last_24h, inline=True)
    embed.add_field(name='LAST 7 DAYS', value=field_last_7d, inline=True)
    embed.add_field(name='LAST 4 WEEKS', value=field_last_4w, inline=True)
    embed.add_field(name='LAST YEAR', value=field_last_1y, inline=True)
    embed.add_field(name=f'SINCE LAST TT', value=field_last_tt, inline=True)
    return embed


async def embed_stats_timeframe(ctx: commands.Context, user: discord.Member, time_left: timedelta) -> discord.Embed:
    """Stats timeframe embed"""
    field_timeframe = ''
    user_settings: users.User = await users.get_user(user.id)
    for command in strings.TRACKED_COMMANDS:
        try:
            report = await tracking.get_log_report(user.id, command, time_left)
            field_timeframe = f'{field_timeframe}\n{emojis.BP} `{report.command}`: {report.command_count:,}'
        except exceptions.NoDataFoundError:
            field_timeframe = f'{field_timeframe}\n{emojis.BP} `{command}`: 0'

    time_left_seconds = int(time_left.total_seconds())
    days = time_left_seconds // 86400
    hours = (time_left_seconds % 86400) // 3600
    minutes = (time_left_seconds % 3600) // 60
    seconds = time_left_seconds % 60
    timeframe = ''
    if days > 0: timeframe = f'{days} days'
    if hours > 0: timeframe = f'{timeframe}, {hours} hours'
    if minutes > 0: timeframe = f'{timeframe}, {minutes} minutes'
    if seconds > 0: timeframe = f'{timeframe}, {seconds} seconds'
    timeframe = timeframe.strip(',').strip()

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user.name}\'s stats'.upper(),
        description = '**Command tracking is currently turned off!**' if not user_settings.tracking_enabled else ''
    )
    embed.add_field(name=f'LAST {timeframe}'.upper(), value=field_timeframe, inline=False)
    return embed