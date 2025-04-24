# main.py
"""Contains error handling and the help and about commands"""

from datetime import datetime, timedelta, timezone
from humanfriendly import format_timespan
import os
import psutil
import random
import sys
from typing import List, Union

import discord
from discord import utils
from discord.ext import bridge

from database import cooldowns, guilds, users
from database import settings as settings_db
from resources import emojis, functions, settings, strings


class LinksView(discord.ui.View):
    """View with link buttons."""
    def __init__(self):
        super().__init__(timeout=None)
        if settings.LINK_SUPPORT is not None:
            self.add_item(discord.ui.Button(label="Support", style=discord.ButtonStyle.link,
                                            url=settings.LINK_SUPPORT, emoji=emojis.SUPPORT, row=0))
        self.add_item(discord.ui.Button(label="Changelog", style=discord.ButtonStyle.link,
                                        url=strings.LINK_CHANGELOG, emoji=emojis.GITHUB, row=0))
        self.add_item(discord.ui.Button(label="Github", style=discord.ButtonStyle.link,
                                        url=strings.LINK_GITHUB, emoji=emojis.GITHUB, row=0))
        if settings.LINK_PRIVACY_POLICY is not None:
            self.add_item(discord.ui.Button(label="Privacy policy", style=discord.ButtonStyle.link,
                                            url=settings.LINK_PRIVACY_POLICY, emoji=emojis.PRIVACY_POLICY, row=1))
        if settings.LINK_TERMS is not None:
            self.add_item(discord.ui.Button(label="Terms of Service", style=discord.ButtonStyle.link,
                                            url=settings.LINK_TERMS, emoji=emojis.TERMS, row=1))
        if settings.LINK_INVITE is not None:
            self.add_item(discord.ui.Button(label="Invite", style=discord.ButtonStyle.link,
                          url=settings.LINK_INVITE, emoji=emojis.INVITE, row=2))
            

# --- Commands ---
async def command_event_reduction(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext) -> None:
    """Help command"""
    all_cooldowns = list(await cooldowns.get_all_cooldowns())
    embed = await embed_event_reductions(bot, ctx, all_cooldowns)
    await ctx.respond(embed=embed)


async def command_help(bot: bridge.AutoShardedBot, ctx: Union[bridge.BridgeContext, discord.Message]) -> None:
    """Help command"""
    view = LinksView()
    embed = await embed_help(bot, ctx)
    if isinstance(ctx, discord.Message):
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.respond(embed=embed, view=view)


async def command_about(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext) -> None:
    """About command"""
    start_time: datetime = utils.utcnow()
    interaction = await ctx.respond('Testing API latency...')
    end_time: datetime = utils.utcnow()
    api_latency: timedelta = end_time - start_time
    img_navi = discord.File
    embed = discord.Embed
    img_navi, embed = await embed_about(bot, ctx, api_latency)
    view: LinksView = LinksView()
    if ctx.guild is not None:
        channel_permissions = ctx.channel.permissions_for(ctx.guild.me) # TODO: Typing
        if not channel_permissions.attach_files:
            await interaction.edit(content=None, embed=embed, view=view)
        else:
            await interaction.edit(content=None, embed=embed, view=view, file=img_navi)
    else:
        await interaction.edit(content=None, embed=embed, view=view)


# --- Embeds ---
async def embed_event_reductions(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext,
                                 all_cooldowns: List[cooldowns.Cooldown]) -> discord.Embed:
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
    prefix = await guilds.get_prefix(ctx)
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'ACTIVE EVENT REDUCTIONS',
        description = (
            f'_Event reductions are set by your Navi bot owner._\n'
            f'_You can set additional personal multipliers with '
            f'{await functions.get_navi_slash_command(bot, "settings multipliers")} or `{prefix}multi`_\n'
        )
    )
    embed.add_field(name='SLASH COMMANDS', value=reductions_slash, inline=False)
    embed.add_field(name='TEXT & MENTION COMMANDS', value=reductions_text, inline=False)
    return embed


async def embed_help(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext) -> discord.Embed:
    """Main menu embed"""
    prefix = await guilds.get_prefix(ctx)
    title_link = 'https://youtu.be/SB4sDPTZPYM'
    reminder_settings = (
        f'{emojis.BP} **[Check active reminders]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "list")}, `{prefix}cd`\n'
        f'{emojis.BP} **[Add custom reminder]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "custom-reminder")}, `{prefix}rm`\n'
        f'{emojis.BP} **[Manage reminders]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings reminders")}, `{prefix}srm`\n'
        f'{emojis.BP} **[Manage reminder messages]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings messages")}, `{prefix}sm`\n'
    )
    ready_settings = (
        f'{emojis.BP} **[Check ready commands]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "ready")}, `{prefix}rd`\n'
        f'{emojis.BP} **[Manage ready list]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings ready")}, `{prefix}srd`\n'
    )
    stats = (
        f'{emojis.BP} **[Check stats]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "stats")}, `{prefix}st`\n'
        f'{emojis.BP} **[Manage tracking settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings user")}, `{prefix}s`\n'
    )
    user_settings = (
        f'{emojis.BP} **[Enable Navi]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "on")}, `{prefix}on`\n'
        f'{emojis.BP} **[Disable Navi]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "off")}, `{prefix}off`\n'
        f'{emojis.BP} **[Manage user settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings user")}, `{prefix}s`\n'
    )
    helper_settings = (
        f'{emojis.BP} **[Manage helper settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings helpers")}, `{prefix}sh`\n'
    )
    partner_settings = (
        f'{emojis.BP} **[Manage alts]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings alts")}, `{prefix}sa`\n'
        f'{emojis.BP} **[Manage partner]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings partner")}, `{prefix}sp`\n'
    )
    guild_settings = (
        f'{emojis.BP} **[Check weekly leaderboard]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "guild leaderboard")}, `{prefix}glb`\n'
        f'{emojis.BP} **[Manage guild settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings guild")}, `{prefix}sg`\n'
        f'{emojis.BP} **[Add or update your guild]({title_link})**: '
        f'{strings.SLASH_COMMANDS["guild list"]}, `rpg guild list`\n'
    )
    multiplier_settings = (
        f'{emojis.BP} **[Check event reductions]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "event-reductions")}, `{prefix}er`\n'
        f'{emojis.BP} **[Manage multipliers]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings multipliers")}, `{prefix}multi`\n'
    )
    portal_settings = (
        f'{emojis.BP} **[Check your portals]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "portals")}, `{prefix}pt`\n'
        f'{emojis.BP} **[Manage your portals]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "settings portals")}, `{prefix}spt`\n'
    )
    misc_settings = (
        f'{emojis.BP} **[Speed enable settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "enable")}, `{prefix}e`\n'
        f'{emojis.BP} **[Speed disable settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "disable")}, `{prefix}d`\n'
        f'{emojis.BP} **[Purge your data]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "purge")}, `{prefix}purge`\n'
        f'{emojis.BP} **[Slash command overview]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "slashboard")}, `{prefix}sb`\n'
        f'{emojis.BP} **[Calculator]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "calculator")}, `{prefix}calc`\n'
        f'{emojis.BP} **[About Navi]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "about")}, `{prefix}about`\n'
    )
    server_settings = (
        f'_Requires `Manage server` permission._\n'
        f'{emojis.BP} **[Manage server settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "server-settings main")}, `{prefix}ss`\n'
        f'{emojis.BP} **[Manage auto-flex settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "server-settings auto-flex")}, `{prefix}ssa`\n'
        f'{emojis.BP} **[Manage event-ping settings]({title_link})**: '
        f'{await functions.get_navi_slash_command(bot, "server-settings event-pings")}, `{prefix}sse`\n'
    )
    supported_languages = (
        f'{emojis.BP} :flag_us: English\n'
        f'{emojis.BP} :flag_es: Spanish\n'
        f'{emojis.BP} :flag_br: Portuguese\n'
    )
        
    ctx_author_name = ctx.author.global_name if ctx.author.global_name is not None else ctx.author.name
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'NAVI' if not settings.LITE_MODE else 'NAVI LITE',
        description =   (
            f'_Hey! **{ctx_author_name}**! Hello!_\n'
        )
    )
    embed.add_field(name='USER', value=user_settings, inline=False)
    embed.add_field(name='REMINDERS', value=reminder_settings, inline=False)
    embed.add_field(name='READY COMMANDS', value=ready_settings, inline=False)
    embed.add_field(name='ALTS & PARTNER', value=partner_settings, inline=False)
    embed.add_field(name='HELPERS', value=helper_settings, inline=False)
    embed.add_field(name='GUILD', value=guild_settings, inline=False)
    embed.add_field(name='TRACKING', value=stats, inline=False)
    embed.add_field(name='MULTIPLIERS & EVENT REDUCTIONS', value=multiplier_settings, inline=False)
    embed.add_field(name='PORTALS', value=portal_settings, inline=False)
    embed.add_field(name='SERVER', value=server_settings, inline=False)
    embed.add_field(name='MISC', value=misc_settings, inline=False)
    embed.add_field(name='SUPPORTED EPIC RPG LANGUAGES', value=supported_languages, inline=False)
    all_settings: dict[str, str] = await settings_db.get_settings()
    if all_settings['seasonal_event'] in strings.SEASONAL_EVENTS:
        embed.set_footer(text=f'{all_settings["seasonal_event"].replace("_"," ").capitalize()} event mode active.')
    return embed


async def embed_about(bot: bridge.AutoShardedBot, ctx: bridge.Context, api_latency: timedelta) -> tuple[discord.File, discord.Embed]:
    """Bot info embed"""
    user_count: int = await users.get_user_count()
    all_settings: dict[str, str] = await settings_db.get_settings()
    uptime: timedelta = utils.utcnow() - datetime.fromisoformat(all_settings['startup_time']).replace(tzinfo=timezone.utc)
    uptime: timedelta = timedelta(seconds=round(uptime.total_seconds()))

    general: str = (
        f'{emojis.BP} `{len(bot.guilds):,}` servers\n'
        f'{emojis.BP} `{user_count:,}` users\n'
        f'{emojis.BP} `{len(bot.shards):,}` shards\n'
        f'{emojis.BP} `{round(bot.latency * 1000):,}` ms average bot latency\n'
        f'{emojis.BP} `{round(api_latency.total_seconds() * 1000):,}` ms API latency\n'
        f'{emojis.BP} Online for {format_timespan(uptime)}\n'
        f'{emojis.BP} Bot owner: <@{settings.OWNER_ID}>\n'
    )
    if ctx.guild is not None:
        current_shard: discord.ShardInfo | None = bot.get_shard(ctx.guild.shard_id)
        bot_latency: str = f'`{round(current_shard.latency * 1000):,}` ms' if current_shard is not None else '`N/A`'
        current_shard_status: str = (
            f'{emojis.BP} Shard `{ctx.guild.shard_id + 1}` of `{len(bot.shards):,}`\n'
            f'{emojis.BP} {bot_latency} bot latency\n'
            f'{emojis.BP} `{round(api_latency.total_seconds() * 1000):,}` ms API latency'
        )
    app_process: psutil.Process = psutil.Process(os.getpid())
    navi_memory: float = app_process.memory_info().vms / (1024 ** 2)
    system_memory: psutil = psutil.virtual_memory()
    system_memory_total = round(system_memory[0] / (1024 ** 2)) # TODO: Typing
    system_memory_available: int = round(system_memory[1] / (1024 ** 2))
    system_memory_used: int = system_memory_total - system_memory_available
    creator: str = f'{emojis.BP} <@619879176316649482>'
    dev_stuff: str = (
        f'{emojis.BP} Version: `{settings.VERSION}`\n'
        f'{emojis.BP} Language: Python `{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}`\n'
        f'{emojis.BP} Library: Pycord `{discord.__version__}`\n'
        f'{emojis.BP} Navi RAM usage: `{navi_memory:,.2f}` MB\n'
        f'{emojis.BP} System CPU usage: `{psutil.cpu_percent():g}`%\n'
        f'{emojis.BP} System RAM usage: `{system_memory[2]}`% (`{system_memory_used:,}` / `{system_memory_total:,}` MB)\n'
    )
    thanks_to: list[str] = [
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
        'VisualBasic 3, 4, 5 and 6',
        'An Intel 486-DX2-S with 16 MB of RAM',
        'The Raspberry Pi Foundation',
        'Mom',
    ]
    img_navi: discord.File = discord.File(settings.IMG_NAVI, filename='navi.png')
    image_url: str = 'attachment://navi.png'
    embed: discord.Embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'ABOUT NAVI' if not settings.LITE_MODE else 'ABOUT NAVI LITE',
        description = 'I am as free as a fairy.'
    )
    embed.add_field(name='BOT STATS', value=general, inline=False)
    if ctx.guild is not None:
        embed.add_field(name='CURRENT SHARD', value=current_shard_status, inline=False)
    embed.add_field(name='CREATOR', value=creator, inline=False)
    embed.add_field(name='DEV STUFF', value=dev_stuff, inline=False)
    embed.add_field(name='SPECIAL THANKS TO', value=f'{emojis.BP} {random.choice(thanks_to)}', inline=False)
    embed.set_thumbnail(url=image_url)
    return (img_navi, embed)