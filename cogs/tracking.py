# tracking.py
"""Contains commands related to command tracking"""

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, users, tracking
from resources import emojis, functions, exceptions, settings, strings


class TrackingCog(commands.Cog):
    """Cog with command tracking commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=('statistics','statistic','stat'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def stats(self, ctx: commands.Context, *args: str) -> None:
        """Returns current command statistics"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        if ctx.message.mentions:
            mentioned_user = ctx.message.mentions[0]
            if mentioned_user.bot:
                await ctx.reply(
                    'Imaging trying to check the stats of a bot.',
                    mention_author=False
                )
                return
            user = mentioned_user
            args = list(args)
            matches = (f'<@!{user.id}>', f'<@{user.id}>')
            for index, arg in enumerate(args):
                if any(match in arg for match in matches):
                    args.pop(index)
        else:
            user = ctx.author

        try:
            user_settings: users.User = await users.get_user(user.id)
        except exceptions.FirstTimeUserError:
            await ctx.reply(f'User **{user.name}** is not registered with this bot.', mention_author=False)
            return

        if not args or len(args) > 1:
            embed = await embed_stats_overview(ctx, user)
        if args:
            timestring = args[0]
            try:
                timestring = await functions.check_timestring(timestring)
            except Exception as error:
                await ctx.reply(error, mention_author=False)
                return

            time_left = await functions.parse_timestring_to_timedelta(ctx, timestring)
            if time_left.days > 365:
                await ctx.reply('The maximum time is 365d.', mention_author=False)
                return
            embed = await embed_stats_timeframe(ctx, user, time_left)

        await ctx.reply(embed=embed, mention_author=False)

    # Events
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Fires when a message is sent"""
        if message.author.id == settings.EPIC_RPG_ID:
            if not message.embeds:
                try:
                    message_content = message.content
                except:
                    return

                if 'we have to check you are actually playing' in message_content.lower():
                    if not message.mentions: return
                    user = message.mentions[0]
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.NoDataFoundError:
                        return
                    if user_settings.tracking_enabled and user_settings.bot_enabled:
                        current_time = datetime.utcnow().replace(microsecond=0)
                        await tracking.insert_log_entry(user.id, message.guild.id, 'epic guard', current_time)

            if message.embeds:
                try:
                    message_content = str(message.embeds[0].description)
                except:
                    return
                if 'has traveled in time' not in message_content.lower(): return
                try:
                    user_name = re.search("\*\*(.+?)\*\* has", message_content).group(1)
                except Exception as error:
                    await errors.log_error(f'Error while reading user name from time travel message:\n{error}')
                    return
                user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                user = None
                for member in message.guild.members:
                    member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    if member_name == user_name:
                        user = member
                        break
                if user is None:
                    await errors.log_error(f'Couldn\'t find a user with user_name {user_name}.')
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.NoDataFoundError:
                    return
                tt_time = message.created_at.replace(microsecond=0)
                await user_settings.update(last_tt=tt_time.isoformat(sep=' '))
                if user_settings.last_tt == tt_time and user_settings.bot_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(TrackingCog(bot))


# --- Embeds ---
async def embed_stats_overview(ctx: commands.Context, user: discord.Member) -> discord.Embed:
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
    field_last_tt = f'{field_last_tt.strip()}\n\nYour last TT was on <t:{int(user_settings.last_tt.timestamp())}:f> UTC.'

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user.name}\'s stats'.upper(),
        description = '**Command tracking is currently turned off!**' if not user_settings.tracking_enabled else ''
    )
    embed.set_footer(text=f'Use "{ctx.prefix}stats [time]" to check a custom timeframe.')
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
    embed.set_footer(text=f'Use "{ctx.prefix}stats" to see an overview.')
    embed.add_field(name=f'LAST {timeframe}'.upper(), value=field_timeframe, inline=False)

    return embed