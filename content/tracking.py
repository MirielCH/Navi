# tracking.py
"""Contains commands related to command tracking"""

from datetime import timedelta, timezone
from humanfriendly import format_timespan
from typing import Coroutine

import discord
from discord import utils
from discord.ext import bridge, commands

from database import users, tracking
from resources import emojis, functions, exceptions, settings, views


# --- Commands ---
async def command_stats(
    bot: bridge.AutoShardedBot,
    ctx: commands.Context | discord.ApplicationContext | discord.Message,
    timestring: str | None = None,
    user: discord.User | discord.Member | None = None,
) -> None:
    """Lists all stats"""
    if user and user != ctx.author:
        user_mentioned: bool = True
    else:
        user = ctx.author
        user_mentioned: bool = False
    try:
        user_settings: users.User = await users.get_user(user.id)
    except exceptions.FirstTimeUserError:
        if user == ctx.author:
            raise
        else:
            await functions.reply_or_respond(ctx, 'This user is not registered with this bot.', True)
            return
    if not timestring:
        time_left: timedelta = timedelta(0)
        embed: discord.Embed = await embed_stats_overview(ctx, user)
        embed_function: Coroutine = embed_stats_overview
    else:
        try:
            timestring: str = await functions.check_timestring(timestring)
        except exceptions.InvalidTimestringError as error:
            msg_error: str = (
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
            time_left: timedelta = await functions.parse_timestring_to_timedelta(timestring)
        except OverflowError as error:
            await ctx.reply(error)
            return
        if time_left.days > 28: time_left = timedelta(days=time_left.days)
        if time_left.days > 365:
            await ctx.reply('The maximum time is 365d, sorry.')
            return
        embed: discord.Embed = await embed_stats_timeframe(ctx, user, time_left)
        embed_function: Coroutine = embed_stats_timeframe
    view: views.StatsView | None = None
    if not user_mentioned:
        view = views.StatsView(bot, ctx, user_settings, user_mentioned, time_left, embed_function)
    if isinstance(ctx, discord.ApplicationContext):
        interaction_message: discord.Interaction | discord.WebhookMessage
        interaction_message = await ctx.respond(embed=embed, view=view)
    else:
        interaction_message: discord.Message = await ctx.reply(embed=embed, view=view)
    if not user_mentioned and view:
        view.interaction_message = interaction_message
        await view.wait()


# --- Embeds ---
async def embed_stats_overview(ctx: commands.Context, user: discord.User | discord.Member,
                               time_left: timedelta = timedelta(0)) -> discord.Embed:
    """Stats overview embed"""
    user_global_name: str = user.global_name if user.global_name else user.name
    user_settings: users.User = await users.get_user(user.id)
    field_last_1h: str = await design_field(timedelta(hours=1), user)
    field_last_12h: str = await design_field(timedelta(hours=12), user)
    field_last_24h: str = await design_field(timedelta(hours=24), user)
    field_last_7d: str = await design_field(timedelta(days=7), user)
    field_last_4w: str = await design_field(timedelta(days=28), user)
    field_last_1y: str = await design_field(timedelta(days=365), user)
    field_last_tt: str = await design_field(utils.utcnow()-user_settings.last_tt, user)
    try:
        timestamp: float = user_settings.last_tt.timestamp()
    except OSError as error: # Windows throws an error if datetime is set to 0 apparently
        timestamp: float = 0
    field_last_tt = f'{field_last_tt.strip()}\n\nYour last TT was on <t:{int(timestamp)}:f>.'

    embed: discord.Embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user_global_name}\'s stats'.upper(),
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


async def embed_stats_timeframe(ctx: commands.Context, user: discord.User | discord.Member, time_left: timedelta) -> discord.Embed:
    """Stats timeframe embed"""
    user_global_name: str = user.global_name if user.global_name else user.name
    user_settings: users.User = await users.get_user(user.id)
    field_content: str = await design_field(time_left, user)
    embed: discord.Embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user_global_name}\'s stats'.upper(),
        description = '**Command tracking is currently turned off!**' if not user_settings.tracking_enabled else ''
    )
    embed.add_field(name=f'Last {format_timespan(time_left)}'.upper(), value=field_content, inline=False)
    return embed


# --- Functions ---
async def design_field(timeframe: timedelta, user: discord.User | discord.Member) -> str:
    report: tracking.LogReport = await tracking.get_log_report(user.id, timeframe)
    field_content: str = (
        f'{emojis.BP} `hunt`: {report.hunt_amount:,}\n'
        f'{emojis.BP} `hunt together`: {report.hunt_together_amount:,}\n'
        f'{emojis.BP} `work`: {report.work_amount:,}\n'
        f'{emojis.BP} `farm`: {report.farm_amount:,}\n'
        f'{emojis.BP} `training`: {report.training_amount:,}\n'
        f'{emojis.BP} `ultraining`: {report.ultraining_amount:,}\n'
        f'{emojis.BP} `adventure`: {report.adventure_amount:,}\n'
        f'{emojis.BP} `epic guard`: {report.epic_guard_amount:,}\n'
    )
    return field_content