# data.py
"""Contains the Navi data command"""

import discord
from discord import utils
from discord.ext import bridge

from database import reminders, users
from resources import emojis, exceptions, settings, strings


# --- Commands ---
async def command_data(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext, user: discord.User | None) -> None:
    """Data command"""
    try:
        user_settings: users.User = await users.get_user(user.id)
    except exceptions.FirstTimeUserError:
        await ctx.respond('This user is not registered with Navi.')
        return
    embed = await embed_data(bot, ctx, user, user_settings)
    await ctx.respond(embed=embed)


# --- Embeds ---
async def embed_data(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext,
                     user: discord.User, user_settings: users.User) -> discord.Embed:
    """Data embed"""
    user_name = user.global_name if user.global_name is not None else user.name
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user_name}\'s TRACKED EPIC RPG DATA'.upper(),
        description = (
            '_This embed shows the EPIC RPG data Navi currently tracks to do its job._\n'
            '_You can use this to check for incorrect values._\n'
        ),
    )

    user_donor_tier = strings.DONOR_TIERS[user_settings.user_donor_tier]
    user_donor_tier_emoji = strings.DONOR_TIERS_EMOJIS[user_donor_tier]
    user_donor_tier = f'{user_donor_tier_emoji} `{user_donor_tier}`'.lstrip('None ')

    game_data = (
        f'{emojis.BP} **Donor tier**: {user_donor_tier}\n'
        f'{emojis.BP} **Guild name**: `{user_settings.clan_name}`\n'
        f'{emojis.BP} **TT count**: `{user_settings.time_travel_count:,}`\n'
        f'{emojis.BP} **Last TT time**: {utils.format_dt(user_settings.last_tt)}\n'
        f'{emojis.BP} **Current area**: `{user_settings.current_area}`\n'
        f'{emojis.BP} **Ascension**: '
        f'{f'{emojis.ENABLED}`Ascended`' if user_settings.ascended else f'{emojis.DISABLED}`Not ascended`'}\n'
        f'{emojis.BP} **Daily trades**: `{user_settings.trade_daily_done}` / `{user_settings.trade_daily_total}`\n'
        f'{emojis.BP} **Eternal boosts tier**: `{user_settings.eternal_boosts_tier}`\n'
    )
    try:
        time_potion_reminder = await reminders.get_user_reminder(user_settings.user_id, 'time-potion')
        time_potion_active = True
    except exceptions.NoDataFoundError:
        time_potion_active = False
    boosts = (
        f'{emojis.BP} **Auto healing**: '
        f'{f'{emojis.ENABLED}`Active`' if user_settings.auto_healing_active else f'{emojis.DISABLED}`Not active`'}\n'
        f'{emojis.BP} **Dragon breath potion**: '
        f'{f'{emojis.ENABLED}`Active`' if user_settings.potion_dragon_breath_active else f'{emojis.DISABLED}`Not active`'}\n'
        f'{emojis.BP} **Flask potion**: '
        f'{f'{emojis.ENABLED}`Active`' if user_settings.potion_flask_active else f'{emojis.DISABLED}`Not active`'}\n'
        f'{emojis.BP} **Round card**: '
        f'{f'{emojis.ENABLED}`Active`' if user_settings.round_card_active else f'{emojis.DISABLED}`Not active`'}\n'
        f'{emojis.BP} **TIME potion**: '
        f'{f'{emojis.ENABLED}`Active`' if time_potion_active else f'{emojis.DISABLED}`Not active`'}\n'
    )
    artifacts = (
        f'{emojis.BP} **Chocolate box**: '
        f'{f'{emojis.ENABLED}`Unlocked`' if user_settings.chocolate_box_unlocked else f'{emojis.DISABLED}`Not yet unlocked`'}\n'
        f'{emojis.BP} **Pocket watch reduction**: `{100 - (user_settings.user_pocket_watch_multiplier * 100)}`%\n'
        f'{emojis.BP} **Top hat**: '
        f'{f'{emojis.ENABLED}`Unlocked`' if user_settings.top_hat_unlocked else f'{emojis.DISABLED}`Not yet unlocked`'}\n'
    )
    inventory = (
        f'{emojis.BP} **Bread**: `{user_settings.inventory.bread:,}`\n'
        f'{emojis.BP} **Bread seeds**: `{user_settings.inventory.seed_bread:,}`\n'
        f'{emojis.BP} **Carrots**: `{user_settings.inventory.carrot:,}`\n'
        f'{emojis.BP} **Carrot seeds**: `{user_settings.inventory.seed_carrot:,}`\n'
        f'{emojis.BP} **ETERNAL presents**: `{user_settings.inventory.present_eternal:,}`\n'
        f'{emojis.BP} **Potatoes**: `{user_settings.inventory.potato:,}`\n'
        f'{emojis.BP} **Potato seeds**: `{user_settings.inventory.seed_potato:,}`\n'
        f'{emojis.BP} **Rubies**: `{user_settings.inventory.ruby:,}`\n'
    )
    last_commands_used = (
        f'{emojis.BP} **Adventure**: `adventure {user_settings.last_adventure_mode}`\n'
        f'{emojis.BP} **Farm**: `farm {user_settings.last_farm_seed}`\n'
        f'{emojis.BP} **Hunt**: `hunt {user_settings.last_hunt_mode}`\n'
        f'{emojis.BP} **Lootbox**: `buy {user_settings.last_lootbox} lootbox`\n'
        f'{emojis.BP} **Quest**: `{user_settings.last_quest_command}`\n'
        f'{emojis.BP} **Training**: `{user_settings.last_training_command}`\n'
        f'{emojis.BP} **Work**: `{user_settings.last_work_command}`\n'
    )

    embed.add_field(name='GAME DATA', value=game_data, inline=False)
    embed.add_field(name='BOOSTS', value=boosts, inline=False)
    embed.add_field(name='ARTIFACTS', value=artifacts, inline=False)
    embed.add_field(name='ITEMS', value=inventory, inline=False)
    embed.add_field(name='LAST USED COMMANDS', value=last_commands_used, inline=False)
    
    return embed