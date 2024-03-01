# slashboard.py
"""Contains the slashboard command"""

import discord
from discord.ext import bridge

from resources import emojis, settings, strings


# --- Commands ---
async def command_slashboard(ctx: bridge.BridgeContext) -> None:
    """Help command"""
    embed = await embed_slashboard()
    await ctx.respond(embed=embed)


# --- Embeds ---
async def embed_slashboard() -> discord.Embed:
    """Slashboard embed"""
    gambling = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["big dice"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["blackjack"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["coinflip"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["cups"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["dice"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["multidice"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["slots"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["wheel"]}\n'
    )
    items = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["cook"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["craft"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["dismantle"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["forge"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["inventory"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["recipes"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["trade items"]}\n'
    )
    profile = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["cd"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["horse stats"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["inventory"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["professions stats"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["profile"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["rd"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["world status"]}\n'
    )
    actions = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["buy"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["heal"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["jail"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["open"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["sell"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["use"]}\n'
    )
    pets = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["pets adventure"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["pets claim"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["pets list"]}\n'
    )
    enchanting = (
        f'{emojis.BP} {strings.SLASH_COMMANDS["enchant"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["refine"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["transmute"]}\n'
        f'{emojis.BP} {strings.SLASH_COMMANDS["transcend"]}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'SLASHBOARD',
    )
    embed.add_field(name='PROFILE', value=profile, inline=True)
    embed.add_field(name='ITEM MANAGEMENT', value=items, inline=True)
    embed.add_field(name='GAMBLING', value=gambling, inline=True)
    embed.add_field(name='ACTIONS', value=actions, inline=True)
    embed.add_field(name='ENCHANTING', value=enchanting, inline=True)
    embed.add_field(name='PETS', value=pets, inline=True)
    return embed