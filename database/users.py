# users.py
"""Provides access to the table "users" in the database"""


from dataclasses import dataclass
from datetime import datetime
import itertools
import sqlite3
from typing import NamedTuple, Optional

from discord.ext import commands

from database import errors
from resources import exceptions, settings, strings


# Containers
class UserAlert(NamedTuple):
    """Object that summarizes all user settings for a specific alert"""
    enabled: bool
    message: str

@dataclass()
class User():
    """Object that represents a record from table "user"."""
    alert_adventure: UserAlert
    alert_arena: UserAlert
    alert_big_arena: UserAlert
    alert_daily: UserAlert
    alert_duel: UserAlert
    alert_dungeon_miniboss: UserAlert
    alert_farm: UserAlert
    alert_horse_breed: UserAlert
    alert_horse_race: UserAlert
    alert_hunt: UserAlert
    alert_lootbox: UserAlert
    alert_lottery: UserAlert
    alert_not_so_mini_boss: UserAlert
    alert_partner: UserAlert
    alert_pet_tournament: UserAlert
    alert_pets: UserAlert
    alert_quest: UserAlert
    alert_training: UserAlert
    alert_vote: UserAlert
    alert_weekly: UserAlert
    alert_work: UserAlert
    clan_name: str
    dnd_mode_enabled: bool
    hardmode_mode_enabled: bool
    last_tt: datetime
    partner_channel_id: int
    partner_donor_tier: int
    partner_id: int
    partner_name: str
    reminders_enabled: bool
    rubies: int
    ruby_counter_enabled: bool
    training_helper_enabled: bool
    user_donor_tier: int
    user_id: int

    async def refresh(self) -> None:
        """Refreshes guild data from the database."""
        new_settings: User = await get_user(self.user_id)
        self.alert_adventure = new_settings.alert_adventure
        self.alert_arena = new_settings.alert_arena
        self.alert_big_arena = new_settings.alert_big_arena
        self.alert_daily = new_settings.alert_daily
        self.alert_duel = new_settings.alert_duel
        self.alert_dungeon_miniboss = new_settings.alert_dungeon_miniboss
        self.alert_farm = new_settings.alert_farm
        self.alert_horse_breed = new_settings.alert_horse_breed
        self.alert_horse_race = new_settings.alert_horse_race
        self.alert_hunt = new_settings.alert_hunt
        self.alert_lootbox = new_settings.alert_lootbox
        self.alert_lottery = new_settings.alert_lottery
        self.alert_not_so_mini_boss = new_settings.alert_not_so_mini_boss
        self.alert_partner = new_settings.alert_partner
        self.alert_pet_tournament = new_settings.alert_pet_tournament
        self.alert_pets = new_settings.alert_pets
        self.alert_quest = new_settings.alert_quest
        self.alert_training = new_settings.alert_training
        self.alert_vote = new_settings.alert_vote
        self.alert_weekly = new_settings.alert_weekly
        self.alert_work = new_settings.alert_work
        self.clan_name = new_settings.clan_name
        self.dnd_mode_enabled = new_settings.dnd_mode_enabled
        self.hardmode_mode_enabled = new_settings.hardmode_mode_enabled
        self.last_tt = new_settings.last_tt
        self.partner_channel_id = new_settings.partner_channel_id
        self.partner_donor_tier = new_settings.partner_donor_tier
        self.partner_id = new_settings.partner_id
        self.partner_name = new_settings.partner_name
        self.reminders_enabled = new_settings.reminders_enabled
        self.rubies = new_settings.rubies
        self.ruby_counter_enabled = new_settings.ruby_counter_enabled
        self.training_helper_enabled = new_settings.training_helper_enabled
        self.user_donor_tier = new_settings.user_donor_tier

    async def update(self, **kwargs) -> None:
        """Updates the user record in the database. Also calls refresh().
        If user_donor_tier is updated and a partner is set, the partner's partner_donor_tier is updated as well.

        Arguments
        ---------
        kwargs (column=value):
            alert_adventure_enabled: bool
            alert_adventure_message: str
            alert_arena_enabled: bool
            alert_arena_message: str
            alert_big_arena_enabled: bool
            alert_big_arena_message: str
            alert_daily_enabled: bool
            alert_daily_message: str
            alert_duel_enabled: bool
            alert_duel_message: str
            alert_dungeon_miniboss_enabled: bool
            alert_dungeon_miniboss_message: str
            alert_farm_enabled: bool
            alert_farm_message: str
            alert_horse_breed_enabled: bool
            alert_horse_breed_message: str
            alert_horse_race_enabled: bool
            alert_horse_race_message: str
            alert_hunt_enabled: bool
            alert_hunt_message: str
            alert_lootbox_enabled: bool
            alert_lootbox_message: str
            alert_lottery_enabled: bool
            alert_lottery_message: str
            alert_not_so_mini_boss_enabled: bool
            alert_not_so_mini_boss_message: str
            alert_partner_enabled: bool
            alert_partner_message: str
            alert_pet_tournament_enabled: bool
            alert_pet_tournament_message: str
            alert_pets_enabled: bool
            alert_pets_message: str
            alert_quest_enabled: bool
            alert_quest_message: str
            alert_training_enabled: bool
            alert_training_message: str
            alert_vote_enabled: bool
            alert_vote_message: str
            alert_weekly_enabled: bool
            alert_weekly_message: str
            alert_work_enabled: bool
            alert_work_message: str
            clan_name: str
            dnd_mode_enabled: bool
            hardmode_mode_enabled: bool
            last_tt: datetime UTC
            partner_channel_id: int
            partner_donor_tier: int
            partner_id: int
            partner_name: str
            reminders_enabled: bool
            rubies: int
            ruby_counter_enabled: bool
            training_helper_enabled: bool
            user_donor_tier: int
        """
        await _update_user(self, kwargs)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_user(record: dict) -> User:
    """Creates a User object from a database record

    Arguments
    ---------
    record: Database record from table "user" as a dict.

    Returns
    -------
    User object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_user'
    try:
        guild = User(
            alert_adventure = UserAlert(enabled=bool(record['alert_adventure_enabled']),
                                        message=record['alert_adventure_message']),
            alert_arena = UserAlert(enabled=bool(record['alert_arena_enabled']),
                                    message=record['alert_arena_message']),
            alert_big_arena = UserAlert(enabled=bool(record['alert_big_arena_enabled']),
                                        message=record['alert_big_arena_message']),
            alert_daily = UserAlert(enabled=bool(record['alert_daily_enabled']),
                                    message=record['alert_daily_message']),
            alert_duel = UserAlert(enabled=bool(record['alert_duel_enabled']),
                                   message=record['alert_duel_message']),
            alert_dungeon_miniboss = UserAlert(enabled=bool(record['alert_dungeon_miniboss_enabled']),
                                               message=record['alert_dungeon_miniboss_message']),
            alert_farm = UserAlert(enabled=bool(record['alert_farm_enabled']),
                                   message=record['alert_farm_message']),
            alert_horse_breed = UserAlert(enabled=bool(record['alert_horse_breed_enabled']),
                                          message=record['alert_horse_breed_message']),
            alert_horse_race = UserAlert(enabled=bool(record['alert_horse_race_enabled']),
                                         message=record['alert_horse_race_message']),
            alert_hunt = UserAlert(enabled=bool(record['alert_hunt_enabled']),
                                   message=record['alert_hunt_message']),
            alert_lootbox = UserAlert(enabled=bool(record['alert_lootbox_enabled']),
                                      message=record['alert_lootbox_message']),
            alert_lottery = UserAlert(enabled=bool(record['alert_lottery_enabled']),
                                      message=record['alert_lottery_message']),
            alert_not_so_mini_boss = UserAlert(enabled=bool(record['alert_not_so_mini_boss_enabled']),
                                               message=record['alert_not_so_mini_boss_message']),
            alert_partner = UserAlert(enabled=bool(record['alert_partner_enabled']),
                                      message=record['alert_partner_message']),
            alert_pet_tournament = UserAlert(enabled=bool(record['alert_pet_tournament_enabled']),
                                             message=record['alert_pet_tournament_message']),
            alert_pets = UserAlert(enabled=bool(record['alert_pets_enabled']),
                                   message=record['alert_pets_message']),
            alert_quest = UserAlert(enabled=bool(record['alert_quest_enabled']),
                                    message=record['alert_quest_message']),
            alert_training = UserAlert(enabled=bool(record['alert_training_enabled']),
                                       message=record['alert__message']),
            alert_vote = UserAlert(enabled=bool(record['alert_vote_enabled']),
                                   message=record['alert_vote_message']),
            alert_weekly = UserAlert(enabled=bool(record['alert_weekly_enabled']),
                                    message=record['alert_weekly_message']),
            alert_work = UserAlert(enabled=bool(record['alert_work_enabled']),
                                   message=record['alert_work_message']),
            clan_name = record['clan_name'],
            dnd_mode_enabled = bool(record['dnd_mode_enabled']),
            hardmode_mode_enabled = bool(record['hardmode_mode_enabled']),
            last_tt = datetime.strptime(record['last_tt']),
            partner_channel_id = record['partner_channel_id'],
            partner_donor_tier = record['partner_donor_tier'],
            partner_id = record['partner_id'],
            partner_name = record['partner_name'],
            reminders_enabled = bool(record['reminders_enabeld']),
            rubies = record['rubies'],
            ruby_counter_enabled = bool(record['ruby_counter_enabled']),
            training_helper_enabled = bool(record['training_helper_enabled']),
            user_donor_tier = record['user_donor_tier'],
            user_id = record['user_id'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, recod=record)
        )
        raise LookupError

    return guild


# Get data
async def get_user(user_id: int) -> User:
    """Gets all user settings.

    Returns
    -------
    User object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'users'
    function_name = 'get_user'
    sql = f'SELECT * FROM {table} where user_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_DATA_FOUND.format(table=table, function=function_name, sql=sql)
        )
        raise exceptions.NoDataFoundError(f'No user data found in database for user "{user_id}".')
    user = await _dict_to_user(record)

    return user


async def get_user_count() -> int:
    """Gets the amount of users in the table "users".

    Returns
    -------
    Amound of users: int

    Raises
    ------
    sqlite3.Error if something happened within the database. Also logs this error to the log file.
    """
    table = 'users'
    function_name = 'get_user_count'
    sql = f'SELECT COUNT(user_id) FROM {table}'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    (user_count,) = record

    return user_count


# Write Data
async def _update_user(user: User, **kwargs) -> None:
    """Updates user record. Use User.update() to trigger this function.
    If user_donor_tier is updated and a partner is set, the partner's partner_donor_tier is updated as well.

    Arguments
    ---------
    user_id: int
    kwargs (column=value):
        alert_adventure_enabled: bool
        alert_adventure_message: str
        alert_arena_enabled: bool
        alert_arena_message: str
        alert_big_arena_enabled: bool
        alert_big_arena_message: str
        alert_daily_enabled: bool
        alert_daily_message: str
        alert_duel_enabled: bool
        alert_duel_message: str
        alert_dungeon_miniboss_enabled: bool
        alert_dungeon_miniboss_message: str
        alert_farm_enabled: bool
        alert_farm_message: str
        alert_horse_breed_enabled: bool
        alert_horse_breed_message: str
        alert_horse_race_enabled: bool
        alert_horse_race_message: str
        alert_hunt_enabled: bool
        alert_hunt_message: str
        alert_lootbox_enabled: bool
        alert_lootbox_message: str
        alert_lottery_enabled: bool
        alert_lottery_message: str
        alert_not_so_mini_boss_enabled: bool
        alert_not_so_mini_boss_message: str
        alert_partner_enabled: bool
        alert_partner_message: str
        alert_pets_enabled: bool
        alert_pets_message: str
        alert_quest_enabled: bool
        alert_quest_message: str
        alert_training_enabled: bool
        alert_training_message: str
        alert_vote_enabled: bool
        alert_vote_message: str
        alert_weekly_enabled: bool
        alert_weekly_message: str
        alert_work_enabled: bool
        alert_work_message: str
        clan_name: str
        dnd_mode_enabled: bool
        hardmode_mode_enabled: bool
        last_tt: datetime UTC
        partner_channel_id: int
        partner_donor_tier: int
        partner_id: int
        partner_name: str
        reminders_enabled: bool
        rubies: int
        ruby_counter_enabled: bool
        training_helper_enabled: bool
        user_donor_tier: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'users'
    function_name = '_update_user'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['user_id'] = user.user_id
        sql = f'{sql} WHERE user_id = :user_id'
        cur.execute(sql, kwargs)
        if 'user_donor_tier' in kwargs and user.partner_id is not None:
            partner = await get_user(user.partner_id)
            await partner.update(partner_donor_tier=user.user_donor_tier)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_user(user_id: int) -> User:
    """Inserts a record in the table "users".

    Returns
    -------
    User object with the newly created user.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_user'
    table = 'users'
    sql = f'INSERT INTO {table} (user_id) VALUES (?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    user = await get_user(user_id)

    return user