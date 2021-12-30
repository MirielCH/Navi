# tracking.py
"""Contains commands related to command tracking"""

import asyncio
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from database import clans, reminders, users
from resources import emojis, functions, exceptions, settings, strings


class TrackingCog(commands.Cog):
    """Cog with command tracking commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('statistics','statistic','stat'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def stats(self, ctx: commands.Context, *args: str) -> None:
        """Returns current command statistics"""
        if ctx.prefix.lower() == 'rpg ': return
        embed = await embed_stats_overview(self.bot, ctx)
        await ctx.reply(embed=embed, mention_author=False)


# Initialization
def setup(bot):
    bot.add_cog(TrackingCog(bot))


# --- Embeds ---
async def embed_stats_overview(bot: commands.Bot, ctx: commands.Context) -> discord.Embed:
    """Stats overview embed"""
    async def bool_to_text(boolean: bool):
        return 'Enabled' if boolean else 'Disabled'

    # Get user settings
    partner_channel_name = 'N/A'
    user_settings: users.User = await users.get_user(ctx.author.id)
    if user_settings.partner_channel_id is not None:
        await bot.wait_until_ready()
        partner_channel = bot.get_channel(user_settings.partner_channel_id)
        partner_channel_name = partner_channel.name

    # Get partner settings
    partner_name = partner_hardmode_status = 'N/A'
    if user_settings.partner_id is not None:
        partner_settings: users.User = await users.get_user(user_settings.partner_id)
        await bot.wait_until_ready()
        partner = bot.get_user(user_settings.partner_id)
        partner_name = f'{partner.name}#{partner.discriminator}'
        partner_hardmode_status = await bool_to_text(partner_settings.hardmode_mode_enabled)

    # Get clan settings
    clan_name = clan_alert_status = stealth_threshold = clan_channel_name = 'N/A'
    try:
        clan_settings: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        clan_name = clan_settings.clan_name
        clan_alert_status = await bool_to_text(clan_settings.alert_enabled)
        stealth_threshold = clan_settings.stealth_threshold
        if clan_settings.channel_id is not None:
            await bot.wait_until_ready()
            clan_channel = bot.get_channel(clan_settings.channel_id)
            clan_channel_name = clan_channel.name
    except exceptions.NoDataFoundError:
        pass

    # Fields
    field_user = (
        f'{emojis.BP} Reminders: `{await bool_to_text(user_settings.reminders_enabled)}`\n'
        f'{emojis.BP} Command tracking: `{await bool_to_text(user_settings.tracking_enabled)}`\n'
        f'{emojis.BP} Donor tier: `{user_settings.user_donor_tier}`'
        f'({strings.DONOR_TIERS[user_settings.user_donor_tier]})\n'
        f'{emojis.BP} DND mode: `{await bool_to_text(user_settings.dnd_mode_enabled)}`\n'
        f'{emojis.BP} Hardmode mode: `{await bool_to_text(user_settings.hardmode_mode_enabled)}`\n'
        f'{emojis.BP} Partner alert channel: `{partner_channel_name}`\n'
        f'{emojis.BP} Ruby counter: `{await bool_to_text(user_settings.ruby_counter_enabled)}`\n'
        f'{emojis.BP} Training helper: `{await bool_to_text(user_settings.training_helper_enabled)}`\n'
    )
    field_partner = (
        f'{emojis.BP} Name: `{partner_name}`\n'
        f'{emojis.BP} Donor tier: `{user_settings.partner_donor_tier}` '
        f'({strings.DONOR_TIERS[user_settings.partner_donor_tier]})\n'
        f'{emojis.BP} Hardmode mode: `{partner_hardmode_status}`\n'
    )
    field_clan = (
        f'{emojis.BP} Name: `{clan_name}`\n'
        f'{emojis.BP} Reminders: `{clan_alert_status}`\n'
        f'{emojis.BP} Alert channel: `{clan_channel_name}`\n'
        f'{emojis.BP} Stealth threshold: `{stealth_threshold}`'
    )
    field_reminders = (
        f'{emojis.BP} Adventure: `{await bool_to_text(user_settings.alert_adventure.enabled)}`\n'
        f'{emojis.BP} Arena: `{await bool_to_text(user_settings.alert_arena.enabled)}`\n'
        f'{emojis.BP} Daily: `{await bool_to_text(user_settings.alert_daily.enabled)}`\n'
        f'{emojis.BP} Duel: `{await bool_to_text(user_settings.alert_duel.enabled)}`\n'
        f'{emojis.BP} Dungeon / Miniboss: `{await bool_to_text(user_settings.alert_dungeon_miniboss.enabled)}`\n'
        f'{emojis.BP} Farm: `{await bool_to_text(user_settings.alert_farm.enabled)}`\n'
        f'{emojis.BP} Horse: `{await bool_to_text(user_settings.alert_horse_breed.enabled)}`\n'
        f'{emojis.BP} Hunt: `{await bool_to_text(user_settings.alert_hunt.enabled)}`\n'
        f'{emojis.BP} Lootbox: `{await bool_to_text(user_settings.alert_lootbox.enabled)}`\n'
        f'{emojis.BP} Lottery: `{await bool_to_text(user_settings.alert_lottery.enabled)}`\n'
        f'{emojis.BP} Partner alert: `{await bool_to_text(user_settings.alert_partner.enabled)}`\n'
        f'{emojis.BP} Pets: `{await bool_to_text(user_settings.alert_pets.enabled)}`\n'
        f'{emojis.BP} Quest: `{await bool_to_text(user_settings.alert_quest.enabled)}`\n'
        f'{emojis.BP} Training: `{await bool_to_text(user_settings.alert_training.enabled)}`\n'
        f'{emojis.BP} Vote: `{await bool_to_text(user_settings.alert_vote.enabled)}`\n'
        f'{emojis.BP} Weekly: `{await bool_to_text(user_settings.alert_weekly.enabled)}`\n'
        f'{emojis.BP} Work: `{await bool_to_text(user_settings.alert_work.enabled)}`'
    )
    field_event_reminders = (
        f'{emojis.BP} Big arena: `{await bool_to_text(user_settings.alert_big_arena.enabled)}`\n'
        f'{emojis.BP} Horse race: `{await bool_to_text(user_settings.alert_horse_race.enabled)}`\n'
        f'{emojis.BP} Not so mini boss: `{await bool_to_text(user_settings.alert_not_so_mini_boss.enabled)}`\n'
        f'{emojis.BP} Pet tournament: `{await bool_to_text(user_settings.alert_pet_tournament.enabled)}`\n'
    )
    if not user_settings.reminders_enabled:
        field_reminders = f'**These settings are ignored because your reminders are off.**\n{field_reminders}'

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name}\'s settings'.upper(),
    )
    embed.add_field(name='USER', value=field_user, inline=False)
    embed.add_field(name='PARTNER', value=field_partner, inline=False)
    embed.add_field(name='GUILD', value=field_clan, inline=False)
    embed.add_field(name='COMMAND REMINDERS', value=field_reminders, inline=False)
    embed.add_field(name='EVENT REMINDERS', value=field_event_reminders, inline=False)

    return embed