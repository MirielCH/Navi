# guilds.py
"""Provides access to the table "guilds" in the database"""


from dataclasses import dataclass
import itertools
import sqlite3
from typing import NamedTuple, Union

import discord
from discord.ext import bridge, commands

from database import errors
from resources import exceptions, settings, strings


# Containers
class EventPing(NamedTuple):
    enabled: bool
    message: str

@dataclass()
class Guild():
    """Object that represents a record from table "guilds"."""
    auto_flex_brew_electronical_enabled: bool
    auto_flex_channel_id: int
    auto_flex_enabled: bool
    auto_flex_artifacts_enabled: bool
    auto_flex_card_drop_enabled: bool
    auto_flex_card_golden_enabled: bool
    auto_flex_card_hand_enabled: bool
    auto_flex_card_slots_enabled: bool
    auto_flex_epic_berry_enabled: bool
    auto_flex_event_coinflip_enabled: bool
    auto_flex_event_enchant_enabled: bool
    auto_flex_event_farm_enabled: bool
    auto_flex_event_heal_enabled: bool
    auto_flex_event_lb_enabled: bool
    auto_flex_event_training_enabled: bool
    auto_flex_forge_cookie_enabled: bool
    auto_flex_hal_boo_enabled: bool
    auto_flex_lb_a18_enabled: bool
    auto_flex_lb_edgy_ultra_enabled: bool
    auto_flex_lb_eternal_enabled: bool
    auto_flex_lb_godly_enabled: bool
    auto_flex_lb_godly_tt_enabled: bool
    auto_flex_lb_omega_enabled: bool
    auto_flex_lb_omega_ultra_enabled: bool
    auto_flex_lb_party_popper_enabled: bool
    auto_flex_lb_void_enabled: bool
    auto_flex_pets_catch_epic_enabled: bool
    auto_flex_pets_catch_tt_enabled: bool
    auto_flex_pets_claim_omega_enabled: bool
    auto_flex_pr_ascension_enabled: bool
    auto_flex_time_travel_enabled: bool
    auto_flex_work_epicberry_enabled: bool
    auto_flex_work_hyperlog_enabled: bool
    auto_flex_work_ultimatelog_enabled: bool
    auto_flex_work_ultralog_enabled: bool
    auto_flex_work_superfish_enabled: bool
    auto_flex_work_watermelon_enabled: bool
    auto_flex_xmas_chimney_enabled: bool
    auto_flex_xmas_eternal_enabled: bool
    auto_flex_xmas_godly_enabled: bool
    auto_flex_xmas_snowball_enabled: bool
    auto_flex_xmas_void_enabled: bool
    event_arena: EventPing
    event_coin: EventPing
    event_fish: EventPing
    event_legendary_boss: EventPing
    event_log: EventPing
    event_lootbox: EventPing
    event_miniboss: EventPing
    event_rare_hunt_monster: EventPing
    guild_id: int
    prefix: str

    async def refresh(self) -> None:
        """Refreshes guild data from the database."""
        new_settings = await get_guild(self.guild_id)
        self.prefix = new_settings.prefix
        self.auto_flex_brew_electronical_enabled = new_settings.auto_flex_brew_electronical_enabled
        self.auto_flex_channel_id = new_settings.auto_flex_channel_id
        self.auto_flex_enabled = new_settings.auto_flex_enabled
        self.auto_flex_artifacts_enabled = new_settings.auto_flex_artifacts_enabled
        self.auto_flex_card_drop_enabled = new_settings.auto_flex_card_drop_enabled
        self.auto_flex_card_golden_enabled = new_settings.auto_flex_card_golden_enabled
        self.auto_flex_card_hand_enabled = new_settings.auto_flex_card_hand_enabled
        self.auto_flex_card_slots_enabled = new_settings.auto_flex_card_slots_enabled
        self.auto_flex_epic_berry_enabled = new_settings.auto_flex_epic_berry_enabled
        self.auto_flex_event_coinflip_enabled = new_settings.auto_flex_event_coinflip_enabled
        self.auto_flex_event_enchant_enabled = new_settings.auto_flex_event_enchant_enabled
        self.auto_flex_event_farm_enabled = new_settings.auto_flex_event_farm_enabled
        self.auto_flex_event_heal_enabled = new_settings.auto_flex_event_heal_enabled
        self.auto_flex_event_lb_enabled = new_settings.auto_flex_event_lb_enabled
        self.auto_flex_event_training_enabled = new_settings.auto_flex_event_training_enabled
        self.auto_flex_forge_cookie_enabled = new_settings.auto_flex_forge_cookie_enabled
        self.auto_flex_hal_boo_enabled = new_settings.auto_flex_hal_boo_enabled
        self.auto_flex_lb_a18_enabled = new_settings.auto_flex_lb_a18_enabled
        self.auto_flex_lb_edgy_ultra_enabled = new_settings.auto_flex_lb_edgy_ultra_enabled
        self.auto_flex_lb_eternal_enabled = new_settings.auto_flex_lb_eternal_enabled
        self.auto_flex_lb_godly_enabled = new_settings.auto_flex_lb_godly_enabled
        self.auto_flex_lb_godly_tt_enabled = new_settings.auto_flex_lb_godly_tt_enabled
        self.auto_flex_lb_omega_enabled = new_settings.auto_flex_lb_omega_enabled
        self.auto_flex_lb_omega_ultra_enabled = new_settings.auto_flex_lb_omega_ultra_enabled
        self.auto_flex_lb_party_popper_enabled = new_settings.auto_flex_lb_party_popper_enabled
        self.auto_flex_lb_void_enabled = new_settings.auto_flex_lb_void_enabled
        self.auto_flex_pets_catch_epic_enabled = new_settings.auto_flex_pets_catch_epic_enabled
        self.auto_flex_pets_catch_tt_enabled = new_settings.auto_flex_pets_catch_tt_enabled
        self.auto_flex_pets_claim_omega_enabled = new_settings.auto_flex_pets_claim_omega_enabled
        self.auto_flex_pr_ascension_enabled = new_settings.auto_flex_pr_ascension_enabled
        self.auto_flex_time_travel_enabled = new_settings.auto_flex_time_travel_enabled
        self.auto_flex_work_epicberry_enabled = new_settings.auto_flex_work_epicberry_enabled
        self.auto_flex_work_hyperlog_enabled = new_settings.auto_flex_work_hyperlog_enabled
        self.auto_flex_work_ultimatelog_enabled = new_settings.auto_flex_work_ultimatelog_enabled
        self.auto_flex_work_ultralog_enabled = new_settings.auto_flex_work_ultralog_enabled
        self.auto_flex_work_superfish_enabled = new_settings.auto_flex_work_superfish_enabled
        self.auto_flex_work_watermelon_enabled = new_settings.auto_flex_work_watermelon_enabled
        self.auto_flex_xmas_chimney_enabled = new_settings.auto_flex_xmas_chimney_enabled
        self.auto_flex_xmas_eternal_enabled = new_settings.auto_flex_xmas_eternal_enabled
        self.auto_flex_xmas_godly_enabled = new_settings.auto_flex_xmas_godly_enabled
        self.auto_flex_xmas_snowball_enabled = new_settings.auto_flex_xmas_snowball_enabled
        self.auto_flex_xmas_void_enabled = new_settings.auto_flex_xmas_void_enabled
        self.event_arena = new_settings.event_arena
        self.event_coin = new_settings.event_coin
        self.event_fish = new_settings.event_fish
        self.event_legendary_boss = new_settings.event_legendary_boss
        self.event_log = new_settings.event_log
        self.event_lootbox = new_settings.event_lootbox
        self.event_miniboss = new_settings.event_miniboss
        self.event_rare_hunt_monster = new_settings.event_rare_hunt_monster

    async def update(self, **updated_settings) -> None:
        """Updates the guild record in the database. Also calls refresh().

        Arguments
        ---------
        updated_settings (column=value):
            auto_flex_brew_electronical_enabled: bool
            auto_flex_channel_id: int
            auto_flex_enabled: bool
            auto_flex_artifacts_enabled: bool
            auto_flex_card_drop_enabled: bool
            auto_flex_card_golden_enabled: bool
            auto_flex_card_hand_enabled: bool
            auto_flex_card_slots_enabled: bool
            auto_flex_epic_berry_enabled: bool
            auto_flex_event_coinflip_enabled: bool
            auto_flex_event_enchant_enabled: bool
            auto_flex_event_farm_enabled: bool
            auto_flex_event_heal_enabled: bool
            auto_flex_event_lb_enabled: bool
            auto_flex_event_training_enabled: bool
            auto_flex_forge_cookie_enabled: bool
            auto_flex_hal_boo_enabled: bool
            auto_flex_lb_a18_enabled: bool
            auto_flex_lb_edgy_ultra_enabled: bool
            auto_flex_lb_eternal_enabled: bool
            auto_flex_lb_godly_enabled: bool
            auto_flex_lb_godly_tt_enabled: bool
            auto_flex_lb_omega_enabled: bool
            auto_flex_lb_omega_ultra_enabled: bool
            auto_flex_lb_party_popper_enabled: bool
            auto_flex_lb_void_enabled: bool
            auto_flex_pets_catch_epic_enabled: bool
            auto_flex_pets_catch_tt_enabled: bool
            auto_flex_pets_claim_omega_enabled: bool
            auto_flex_pr_ascension_enabled: bool
            auto_flex_time_travel_enabled: bool
            auto_flex_work_epicberry_enabled: bool
            auto_flex_work_hyperlog_enabled: bool
            auto_flex_work_ultimatelog_enabled: bool
            auto_flex_work_ultralog_enabled: bool
            auto_flex_work_superfish_enabled: bool
            auto_flex_work_watermelon_enabled: bool
            auto_flex_xmas_chimney_enabled: bool
            auto_flex_xmas_eternal_enabled: bool
            auto_flex_xmas_godly_enabled: bool
            auto_flex_xmas_snowball_enabled: bool
            auto_flex_xmas_void_enabled: bool
            event_arena_enabled: bool
            event_arena_message: str
            event_coin_enabled: bool
            event_coin_message: str
            event_fish_enabled: bool
            event_fish_message: str
            event_legendary_boss_enabled: bool
            event_legendary_boss_message: str
            event_log_enabled: bool
            event_log_message: str
            event_lootbox_enabled: bool
            event_lootbox_message: str
            event_miniboss_enabled: bool
            event_miniboss_message: str
            event_rare_hunt_monster_enabled: bool
            event_rare_hunt_monster_message: str
            prefix: str
        """
        await _update_guild(self.guild_id, **updated_settings)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_guild(record: dict) -> Guild:
    """Creates a Guild object from a database record

    Arguments
    ---------
    record: Database record from table "guilds" as a dict.

    Returns
    -------
    Guild object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_guild'
    try:
        guild = Guild(
            auto_flex_brew_electronical_enabled = bool(record['auto_flex_brew_electronical_enabled']),
            auto_flex_channel_id = record['auto_flex_channel_id'],
            auto_flex_enabled = bool(record['auto_flex_enabled']),
            auto_flex_artifacts_enabled = bool(record['auto_flex_artifacts_enabled']),
            auto_flex_card_drop_enabled = bool(record['auto_flex_card_drop_enabled']),
            auto_flex_card_golden_enabled = bool(record['auto_flex_card_golden_enabled']),
            auto_flex_card_slots_enabled = bool(record['auto_flex_card_slots_enabled']),
            auto_flex_card_hand_enabled = bool(record['auto_flex_card_hand_enabled']),
            auto_flex_epic_berry_enabled = bool(record['auto_flex_epic_berry_enabled']),
            auto_flex_event_coinflip_enabled = bool(record['auto_flex_event_coinflip_enabled']),
            auto_flex_event_enchant_enabled = bool(record['auto_flex_event_enchant_enabled']),
            auto_flex_event_farm_enabled = bool(record['auto_flex_event_farm_enabled']),
            auto_flex_event_heal_enabled = bool(record['auto_flex_event_heal_enabled']),
            auto_flex_event_lb_enabled = bool(record['auto_flex_event_lb_enabled']),
            auto_flex_event_training_enabled = bool(record['auto_flex_event_training_enabled']),
            auto_flex_forge_cookie_enabled = bool(record['auto_flex_forge_cookie_enabled']),
            auto_flex_hal_boo_enabled = bool(record['auto_flex_hal_boo_enabled']),
            auto_flex_lb_a18_enabled = bool(record['auto_flex_lb_a18_enabled']),
            auto_flex_lb_edgy_ultra_enabled = bool(record['auto_flex_lb_edgy_ultra_enabled']),
            auto_flex_lb_eternal_enabled = bool(record['auto_flex_lb_eternal_enabled']),
            auto_flex_lb_godly_enabled = bool(record['auto_flex_lb_godly_enabled']),
            auto_flex_lb_godly_tt_enabled = bool(record['auto_flex_lb_godly_tt_enabled']),
            auto_flex_lb_omega_enabled = bool(record['auto_flex_lb_omega_enabled']),
            auto_flex_lb_omega_ultra_enabled = bool(record['auto_flex_lb_omega_ultra_enabled']),
            auto_flex_lb_party_popper_enabled = bool(record['auto_flex_lb_party_popper_enabled']),
            auto_flex_lb_void_enabled = bool(record['auto_flex_lb_void_enabled']),
            auto_flex_pets_catch_epic_enabled = bool(record['auto_flex_pets_catch_epic_enabled']),
            auto_flex_pets_catch_tt_enabled = bool(record['auto_flex_pets_catch_tt_enabled']),
            auto_flex_pets_claim_omega_enabled = bool(record['auto_flex_pets_claim_omega_enabled']),
            auto_flex_pr_ascension_enabled = bool(record['auto_flex_pr_ascension_enabled']),
            auto_flex_time_travel_enabled = bool(record['auto_flex_time_travel_enabled']),
            auto_flex_work_epicberry_enabled = bool(record['auto_flex_work_epicberry_enabled']),
            auto_flex_work_hyperlog_enabled = bool(record['auto_flex_work_hyperlog_enabled']),
            auto_flex_work_ultimatelog_enabled = bool(record['auto_flex_work_ultimatelog_enabled']),
            auto_flex_work_ultralog_enabled = bool(record['auto_flex_work_ultralog_enabled']),
            auto_flex_work_superfish_enabled = bool(record['auto_flex_work_superfish_enabled']),
            auto_flex_work_watermelon_enabled = bool(record['auto_flex_work_watermelon_enabled']),
            auto_flex_xmas_chimney_enabled = bool(record['auto_flex_xmas_chimney_enabled']),
            auto_flex_xmas_eternal_enabled = bool(record['auto_flex_xmas_eternal_enabled']),
            auto_flex_xmas_godly_enabled = bool(record['auto_flex_xmas_godly_enabled']),
            auto_flex_xmas_snowball_enabled = bool(record['auto_flex_xmas_snowball_enabled']),
            auto_flex_xmas_void_enabled = bool(record['auto_flex_xmas_void_enabled']),
            event_arena = EventPing(enabled=bool(record['event_arena_enabled']), message=record['event_arena_message']),
            event_coin = EventPing(enabled=bool(record['event_coin_enabled']), message=record['event_coin_message']),
            event_fish = EventPing(enabled=bool(record['event_fish_enabled']), message=record['event_fish_message']),
            event_log = EventPing(enabled=bool(record['event_log_enabled']), message=record['event_log_message']),
            event_legendary_boss = EventPing(enabled=bool(record['event_legendary_boss_enabled']), message=record['event_legendary_boss_message']),
            event_lootbox = EventPing(enabled=bool(record['event_lootbox_enabled']), message=record['event_lootbox_message']),
            event_miniboss = EventPing(enabled=bool(record['event_miniboss_enabled']), message=record['event_miniboss_message']),
            event_rare_hunt_monster = EventPing(enabled=bool(record['event_rare_hunt_monster_enabled']), message=record['event_rare_hunt_monster_message']),
            guild_id = record['guild_id'],
            prefix = record['prefix'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return guild


async def _get_mixed_case_prefixes(prefix: str) -> list[str]:
    """Turns a string into a list of all mixed case variations of said string

    Returns
    -------
    All mixed case variations: List[str]
    """
    mixed_prefixes = []
    all_prefixes = map(''.join, itertools.product(*((char.upper(), char.lower()) for char in prefix)))
    for prefix in list(all_prefixes):
        mixed_prefixes.append(prefix)
    return mixed_prefixes


# Read data
async def get_prefix(ctx_or_message: Union[bridge.BridgeContext, discord.Message]) -> str:
    """Check database for stored prefix. If no prefix is found, the default prefix is used"""
    table = 'guilds'
    function_name = 'get_prefix'
    sql = f'SELECT prefix FROM {table} WHERE guild_id=?'
    if ctx_or_message.guild is None:
        return settings.DEFAULT_PREFIX
    guild_id = ctx_or_message.guild.id
    try:
        cur=settings.NAVI_DB.cursor()
        cur.execute(sql, (guild_id,))
        record = cur.fetchone()
        prefix = record['prefix'].replace('"','') if record else settings.DEFAULT_PREFIX
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            ctx_or_message
        )

    return prefix

async def get_all_prefixes(bot: bridge.AutoShardedBot, message: discord.Message) -> list[str]:
    """Gets all prefixes. If no prefix is found, a record for the guild is created with the
    default prefix.

    Returns
    -------
    A tuple with the current server prefix, all "rpg" prefixes and the pingable bot

    Raises
    ------
    sqlite3.Error if something happened within the database.  Also logs this error to the database.
    """
    table = 'guilds'
    function_name = 'get_all_prefixes'
    sql = f'SELECT prefix FROM {table} WHERE guild_id=?'
    if message.guild is None: return commands.when_mentioned_or()(bot, message)
    guild_id = message.guild.id
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (guild_id,))
        record = cur.fetchone()
        prefixes = []
        if record:
            prefix_db = record['prefix'].replace('"','')
            prefix_db_mixed_case = await _get_mixed_case_prefixes(prefix_db)
            for prefix in prefix_db_mixed_case:
                prefixes.append(prefix)
        else:
            sql = f'INSERT INTO {table} (guild_id, prefix) VALUES (?, ?)'
            cur.execute(sql, (guild_id, settings.DEFAULT_PREFIX))
            prefix_default_mixed_case = await _get_mixed_case_prefixes(settings.DEFAULT_PREFIX)
            for prefix in prefix_default_mixed_case:
                prefixes.append(prefix)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
            message
        )
        raise
    return commands.when_mentioned_or(*prefixes)(bot, message)


async def get_guild(guild_id: int) -> Guild:
    """Gets all guild settings.

    Returns
    -------
    Guild object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'guilds'
    function_name = 'get_guild'
    sql_select = f'SELECT * FROM {table} WHERE guild_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql_select, (guild_id,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql_select)
        )
        raise
    if not record:
        sql = f'INSERT INTO {table} (guild_id, prefix) VALUES (?, ?)'
        try:
            cur.execute(sql, (guild_id, settings.DEFAULT_PREFIX))
            sql = sql_select
            cur.execute(sql, (guild_id,))
            record = cur.fetchone()
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
    guild = await _dict_to_guild(dict(record))

    return guild


# Write Data
async def _update_guild(guild_id: int, **updated_settings) -> None:
    """Updates guild record. Use Guild.update() to trigger this function.

    Arguments
    ---------
    updated_settings (column=value):
        auto_flex_brew_electronical_enabled: bool
        auto_flex_channel_id: int
        auto_flex_enabled: bool
        auto_flex_artifacts_enabled: bool
        auto_flex_card_drop_enabled: bool
        auto_flex_card_golden_enabled: bool
        auto_flex_card_hand_enabled: bool
        auto_flex_card_slots_enabled: bool
        auto_flex_epic_berry_enabled: bool
        auto_flex_event_coinflip_enabled: bool
        auto_flex_event_enchant_enabled: bool
        auto_flex_event_farm_enabled: bool
        auto_flex_event_heal_enabled: bool
        auto_flex_event_lb_enabled: bool
        auto_flex_event_training_enabled: bool
        auto_flex_forge_cookie_enabled: bool
        auto_flex_hal_boo_enabled: bool
        auto_flex_lb_a18_enabled: bool
        auto_flex_lb_edgy_ultra_enabled: bool
        auto_flex_lb_godly_enabled: bool
        auto_flex_lb_godly_tt_enabled: bool
        auto_flex_lb_omega_enabled: bool
        auto_flex_lb_omega_ultra_enabled: bool
        auto_flex_lb_party_popper_enabled: bool
        auto_flex_lb_void_enabled: bool
        auto_flex_pets_catch_epic_enabled: bool
        auto_flex_pets_catch_tt_enabled: bool
        auto_flex_pets_claim_omega_enabled: bool
        auto_flex_pr_ascension_enabled: bool
        auto_flex_time_travel_enabled: bool
        auto_flex_work_epicberry_enabled: bool
        auto_flex_work_hyperlog_enabled: bool
        auto_flex_work_ultimatelog_enabled: bool
        auto_flex_work_ultralog_enabled: bool
        auto_flex_work_superfish_enabled: bool
        auto_flex_work_watermelon_enabled: bool
        auto_flex_xmas_chimney_enabled: bool
        auto_flex_xmas_eternal_enabled: bool
        auto_flex_xmas_godly_enabled: bool
        auto_flex_xmas_snowball_enabled: bool
        auto_flex_xmas_void_enabled: bool
        event_arena_enabled: bool
        event_arena_message: str
        event_coin_enabled: bool
        event_coin_message: str
        event_fish_enabled: bool
        event_fish_message: str
        event_legendary_boss_enabled: bool
        event_legendary_boss_message: str
        event_log_enabled: bool
        event_log_message: str
        event_lootbox_enabled: bool
        event_lootbox_message: str
        event_miniboss_enabled: bool
        event_miniboss_message: str
        event_rare_hunt_monster_enabled: bool
        event_rare_hunt_monster_message: str
        prefix: str

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no updated_settings are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'guilds'
    function_name = '_update_guild'
    if not updated_settings:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for updated_setting in updated_settings:
            sql = f'{sql} {updated_setting} = :{updated_setting},'
        sql = sql.strip(",")
        updated_settings['guild_id'] = guild_id
        sql = f'{sql} WHERE guild_id = :guild_id'
        cur.execute(sql, updated_settings)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise