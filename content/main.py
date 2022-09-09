# main.py
"""Contains error handling and the help and about commands"""

from datetime import datetime
from humanfriendly import format_timespan
import psutil
import sys
from typing import Union

import discord
from discord.ext import commands

from database import users
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
async def command_help(ctx: Union[discord.ApplicationContext, commands.Context, discord.Message]) -> None:
    """Help command"""
    view = LinksView()
    embed = await embed_help(ctx)
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
async def embed_help(ctx: discord.ApplicationContext) -> discord.Embed:
    """Main menu embed"""
    reminder_settings = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["list"]} : List all your active reminders\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["ready"]} : List all commands off cooldown\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["custom-reminder"]} : Add a custom reminder\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings messages"]} : Manage reminder messages\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings ready"]} : Manage ready commands\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings reminders"]} : Enable/disable reminders\n'
    )
    stats = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["stats"]} : Shows your command stats\n'
    )
    user_settings = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["on"]} : Turn on Navi\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["off"]} : Turn off Navi\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings user"]} : Manage your user settings\n'
    )
    helper_settings = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings helpers"]} : Enable/disable helpers\n'
    )
    partner_settings = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings partner"]} : Manage partner settings\n'
    )
    guild_settings = (
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["leaderboard guild"]} : Check the weekly raid leaderboard\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NAVI["settings guild"]} : Manage guild channel reminders\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS_NEW["guild list"]} : Add/update your guild\n'
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
            f'Hey! **{ctx.author.name}**! Hello!\n'
            f'Here are some settings you can change.'
        )
    )
    embed.add_field(name='USER', value=user_settings, inline=False)
    embed.add_field(name='PARTNER', value=partner_settings, inline=False)
    embed.add_field(name='REMINDERS', value=reminder_settings, inline=False)
    embed.add_field(name='HELPERS', value=helper_settings, inline=False)
    embed.add_field(name='GUILD CHANNEL REMINDERS', value=guild_settings, inline=False)
    embed.add_field(name='COMMAND TRACKING', value=stats, inline=False)
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
    creator = f'{emojis.BP} Miriel#0001'
    dev_stuff = (
        f'{emojis.BP} Language: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n'
        f'{emojis.BP} Library: Pycord {discord.__version__}\n'
        f'{emojis.BP} System CPU usage: {psutil.cpu_percent()}%\n'
        f'{emojis.BP} System RAM usage: {psutil.virtual_memory()[2]}%\n'
    )
    img_navi = discord.File(settings.IMG_NAVI, filename='navi.png')
    image_url = 'attachment://navi.png'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'ABOUT NAVI',
        description = f'I am as free as a fairy.'
    )
    embed.add_field(name='BOT STATS', value=general, inline=False)
    embed.add_field(name='CREATOR', value=creator, inline=False)
    embed.add_field(name='DEV STUFF', value=dev_stuff, inline=False)
    embed.add_field(name='SPECIAL THANKS TO', value=f'{emojis.BP} Swiss cheese', inline=False)
    embed.set_thumbnail(url=image_url)
    return (img_navi, embed)