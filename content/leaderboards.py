# leaderboards.py
"""Contains leaderboard commands"""

import discord
from discord.ext import bridge

from database import clans
from resources import emojis, exceptions, settings, strings


# -- Commands ---
async def command_leaderboard_clan(ctx: bridge.BridgeContext) -> None:
    """Shows the clan leaderboard"""
    try:
        clan_settings: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
    except exceptions.NoDataFoundError:
        await ctx.respond(
            f'Your guild is not registered with Navi. If you are in a guild, use '
            f'{strings.SLASH_COMMANDS["guild list"]} or `rpg guild list` to add it.'
        )
        return
    embed = await embed_leaderboard_clan(clan_settings)
    await ctx.respond(embed=embed)


# -- Embeds ---
async def embed_leaderboard_clan(clan_settings: clans.Clan) -> discord.Embed:
    """Embed with clan leaderboard"""
    leaderboard: clans.ClanLeaderboard = await clans.get_leaderboard(clan_settings)
    field_best_raids = field_worst_raids = ''
    for index, best_raid in enumerate(leaderboard.best_raids):
        emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
        field_best_raids = (
            f'{field_best_raids}\n'
            f'{emoji} **{best_raid.energy:,}** {emojis.ENERGY} by <@{best_raid.user_id}>'
        )
    for index, worst_raid in enumerate(leaderboard.worst_raids):
        emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
        field_worst_raids = (
            f'{field_worst_raids}\n'
            f'{emoji} **{worst_raid.energy:,}** {emojis.ENERGY} by <@{worst_raid.user_id}>'
        )
    if field_best_raids == '': field_best_raids = f'{emojis.BP} _No cool raids yet._'
    if field_worst_raids == '': field_worst_raids = f'{emojis.BP} _No lame raids yet._'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{clan_settings.clan_name.upper()} WEEKLY LEADERBOARD',
    )
    embed.set_footer(text='Imagine being on the lower list.')
    embed.add_field(name=f'COOL RAIDS {emojis.BEST_RAIDS}', value=field_best_raids, inline=False)
    embed.add_field(name=f'WHAT THE HELL IS THIS {emojis.WORST_RAIDS}', value=field_worst_raids, inline=False)
    return embed