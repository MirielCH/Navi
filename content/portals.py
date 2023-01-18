# link.py
"""Contains the link command"""

import random
from typing import Union

import discord
from discord.ext import commands

from database import portals, users
from resources import emojis, exceptions, functions, settings


# --- Commands ---
async def command_portals(bot: discord.Bot, ctx: Union[discord.ApplicationContext, commands.Context]) -> None:
    """Link command"""
    user_settings: users.User = await users.get_user(ctx.author.id)
    message_content, embed = await embed_portals(bot, ctx, user_settings)
    if isinstance(ctx, discord.ApplicationContext):
        await ctx.respond(content=message_content, embed=embed)
    else:
        await ctx.reply(content=message_content, embed=embed)


# --- Embeds ---
async def embed_portals(bot: discord.Bot, ctx: Union[discord.ApplicationContext, commands.Context],
                        user_settings: users.User) -> discord.Embed:
    """Link embed"""
    description = ''
    message_content = embed = None
    try:
        user_portals = await portals.get_portals(ctx.author.id)
    except exceptions.NoDataFoundError:
        user_portals = None
        description = (
            f'_No portals found. Use {await functions.get_navi_slash_command(bot, "settings portals")} '
            f'to set some._'
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
        embed.set_footer(text='Use \'/settings portals\' to edit this list.')
    return (message_content, embed)