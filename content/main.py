# main.py
"""Contains error handling and the help and about commands"""

from datetime import datetime
from humanfriendly import format_timespan
import psutil
import random
import sys
from typing import List, Union

import discord
from discord.ext import commands

from database import cooldowns, guilds, users
from database import settings as settings_db
from resources import emojis, functions, settings, strings


class LinksView(discord.ui.View):
    """View with link buttons."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Github", style=discord.ButtonStyle.link,
                                        url=strings.LINK_GITHUB, emoji=emojis.GITHUB))
        self.add_item(discord.ui.Button(label="Privacy policy", style=discord.ButtonStyle.link,
                                        url=strings.LINK_PRIVACY_POLICY, emoji=emojis.PRIVACY_POLICY))


# --- Commands ---
async def command_event_reduction(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """Help command"""
    all_cooldowns = list(await cooldowns.get_all_cooldowns())
    embed = await embed_event_reductions(bot, all_cooldowns)
    await ctx.respond(embed=embed)

        
async def command_help(bot: discord.Bot, ctx: Union[discord.ApplicationContext, commands.Context, discord.Message]) -> None:
    """Help command"""
    view = LinksView()
    embed = await embed_help(bot, ctx)
    if isinstance(ctx, discord.ApplicationContext):
        await ctx.respond(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed, view=view)


async def command_about(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """About command"""
    start_time = datetime.utcnow()
    interaction = await ctx.respond('Testing API latency...')
    end_time = datetime.utcnow()
    api_latency = end_time - start_time
    img_navi, embed = await embed_about(bot, api_latency)
    view = LinksView()
    await functions.edit_interaction(interaction, content=None, embed=embed, view=view, file=img_navi)


# --- Embeds ---
async def embed_event_reductions(bot: discord.Bot, all_cooldowns: List[cooldowns.Cooldown]) -> discord.Embed:
    """Event reductions embed"""
    reductions_slash = reductions_text = ''
    for cooldown in all_cooldowns:
        if cooldown.event_reduction_slash > 0:
            reductions_slash = f'{reductions_slash}\n{emojis.BP} {cooldown.activity}: `{cooldown.event_reduction_slash}`%'
        if cooldown.event_reduction_mention > 0:
            reductions_text = f'{reductions_text}\n{emojis.BP} {cooldown.activity}: `{cooldown.event_reduction_mention}`%'
    if reductions_slash == '':
        reductions_slash = f'{emojis.BP} No event reductions active'
    if reductions_text == '':
        reductions_text = f'{emojis.BP} No event reductions active'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'ACTIVE EVENT REDUCTIONS',
        description = (
            f'_Event reductions are set by your Navi bot admin._\n'
            f'_You can set additional personal multipliers with '
            f'{await functions.get_navi_slash_command(bot, "settings reminders")}_\n'
        )
    )
    embed.add_field(name='SLASH COMMANDS', value=reductions_slash, inline=False)
    embed.add_field(name='TEXT & MENTION COMMANDS', value=reductions_text, inline=False)
    return embed


async def embed_help(bot: discord.Bot, ctx: discord.ApplicationContext) -> discord.Embed:
    """Main menu embed"""
    prefix = await guilds.get_prefix(ctx)
    reminder_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "list")} : Your active reminders\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}list`, `{prefix}cd`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "ready")} : Your ready commands\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}ready`, `{prefix}rd`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "custom-reminder")} : Add a custom reminder\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}reminder`, `{prefix}rm`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings messages")} : Manage reminder messages\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings multipliers")} : Manage custom multipliers\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings ready")} : Manage the ready list\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings reminders")} : Enable/disable reminders\n'
    )
    stats = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "stats")} : Shows your command stats\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}stats`, `{prefix}st`_\n'
    )
    user_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "on")} : Turn on Navi\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "off")} : Turn off Navi\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings user")} : Manage your user settings\n'
    )
    helper_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings helpers")} : Enable/disable helpers\n'
    )
    partner_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings alts")} : Manage alts\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings partner")} : Manage partner settings\n'
    )
    guild_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "leaderboard guild")} : Check the weekly raid leaderboard\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}guild leaderboard`, `{prefix}guild lb`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings guild")} : Manage guild channel reminders\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["guild list"]} : Add/update your guild\n'
    )
    misc_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "enable")} & '
        f'{await functions.get_navi_slash_command(bot, "disable")} : Speed enable/disable settings\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}enable` & `{prefix}disable`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "event-reductions")} : Check active event reductions\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "portals")} : Customizable list of channel links\n'
        f'{emojis.DETAIL} _Aliases: `{prefix}portals`, `{prefix}pt`_\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "purge data")} : Purges your user data\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings portals")} : Manage your portals\n'
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "slashboard")} : List of some EPIC RPG slash commands\n'
    )
    server_settings = (
        f'{emojis.BP} {await functions.get_navi_slash_command(bot, "settings server")} : Server settings\n'
        f'{emojis.DETAIL} _Requires `Manage server` permission._\n'
    )
    supported_languages = (
        f'{emojis.BP} :flag_us: English\n'
        f'{emojis.BP} :flag_es: Spanish\n'
        f'{emojis.BP} :flag_br: Portuguese\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'NAVI',
        description =   (
            f'_Hey! **{ctx.author.name}**! Hello!_\n'
            f'_May I interest you in some settings?_'
        )
    )
    embed.add_field(name='USER', value=user_settings, inline=False)
    embed.add_field(name='PARTNER & ALTS', value=partner_settings, inline=False)
    embed.add_field(name='REMINDERS', value=reminder_settings, inline=False)
    embed.add_field(name='HELPERS', value=helper_settings, inline=False)
    embed.add_field(name='GUILD CHANNEL REMINDERS', value=guild_settings, inline=False)
    embed.add_field(name='COMMAND TRACKING', value=stats, inline=False)
    embed.add_field(name='MISC', value=misc_settings, inline=False)
    embed.add_field(name='SERVER', value=server_settings, inline=False)
    embed.add_field(name='SUPPORTED EPIC RPG LANGUAGES', value=supported_languages, inline=False)
    return embed


async def embed_about(bot: commands.Bot, api_latency: datetime) -> discord.Embed:
    """Bot info embed"""
    user_count = await users.get_user_count()
    all_settings = await settings_db.get_settings()
    uptime = datetime.utcnow().replace(microsecond=0) - datetime.fromisoformat(all_settings['startup_time'])
    general = (
        f'{emojis.BP} {len(bot.guilds):,} servers\n'
        f'{emojis.BP} {user_count:,} users\n'
        f'{emojis.BP} {round(bot.latency * 1000):,} ms bot latency\n'
        f'{emojis.BP} {round(api_latency.total_seconds() * 1000):,} ms API latency\n'
        f'{emojis.BP} Online for {format_timespan(uptime)}'
    )
    creator = f'{emojis.BP} miriel.ch'
    dev_stuff = (
        f'{emojis.BP} Version: {settings.VERSION}\n'
        f'{emojis.BP} Language: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'
        f'{emojis.BP} Library: Pycord {discord.__version__}\n'
        f'{emojis.BP} System CPU usage: {psutil.cpu_percent()}%\n'
        f'{emojis.BP} System RAM usage: {psutil.virtual_memory()[2]}%\n'
    )
    thanks_to = [
        'Swiss cheese',
        'Black coffee',
        'Shigeru Miyamoto',
        'Guido van Rossum',
        'No Starch Press',
        'Visual Studio Code',
        'Herbal tea',
        'DXRacer',
        'People complaining about bugs',
        'Not having a family',
        'My brain cells',
        'Being able to read and write',
        'My waning interest in WoW',
        'My keyboard',
        'That one QBasic book back in 1997',
    ]
    img_navi = discord.File(settings.IMG_NAVI, filename='navi.png')
    image_url = 'attachment://navi.png'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'ABOUT NAVI',
        description = 'I am as free as a fairy.'
    )
    embed.add_field(name='BOT STATS', value=general, inline=False)
    embed.add_field(name='CREATOR', value=creator, inline=False)
    embed.add_field(name='DEV STUFF', value=dev_stuff, inline=False)
    embed.add_field(name='SPECIAL THANKS TO', value=f'{emojis.BP} {random.choice(thanks_to)}', inline=False)
    embed.set_thumbnail(url=image_url)
    return (img_navi, embed)