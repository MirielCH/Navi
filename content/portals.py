# link.py
"""Contains the link command"""

import random

import discord
from discord.ext import bridge

from database import portals, users
from resources import emojis, exceptions, functions, settings


# --- Commands ---
async def command_portals(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext) -> None:
    """Portal command"""
    user_settings: users.User = await users.get_user(ctx.author.id)
    message_content, embed = await embed_portals(bot, ctx, user_settings)
    await ctx.respond(content=message_content, embed=embed)


# --- Embeds ---
async def embed_portals(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext,
                        user_settings: users.User) -> discord.Embed:
    """Portal embed"""
    description = ''
    message_content = embed = None
    if ctx.is_app:
        footer_command = f'/settings portals'
        description_command = await functions.get_navi_slash_command(bot, "settings portals")
    else:
        footer_command = f'{ctx.prefix}set pt'
        description_command = f'`{footer_command}`'
    try:
        user_portals = await portals.get_portals(ctx.author.id)
    except exceptions.NoDataFoundError:
        user_portals = None
        description = (
            f'_No portals found. Use {description_command} to set some._'
        )
    if user_portals is not None:
        for portal in user_portals:
            description = f'{description}\n{emojis.BP} <#{portal.channel_id}>'
            if user_settings.portals_spacing_enabled:
                description = f'{description}\n'
    titles = [
        'UP UP AND AWAY',
        'PORT ME BABY, ONE MORE TIME',
        'THIS IS TOTALLY SAFE',
        'BEAM ME UP, SCOTTY',
        'GOTTA GO, BYE',
        'SECRET FBI LINKS',
        'I\'M GOING ON AN ADVENTURE!',
        'SO LONG, I\'M OUTTA HERE',
        'AND THE ROAD GOES ON AND ON',
        'LINKING PARK',
        'TO INFINITY AND BEYOND',
        'SPAAAAAAACE',
        'WHERE SHALL I GO TODAY?',
        'EVERYWHERE BUT HERE!',
        'U BORING, ME LEAVE',
    ]
    if not user_settings.portals_as_embed:
        message_content = (
            f'**{random.choice(titles)}**\n'
            f'{description.strip()}'
        )
    else:
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = random.choice(titles),
            description = description.strip(),
        )
        embed.set_footer(text=f'Use \'{footer_command}\' to edit this list.')
    return (message_content, embed)