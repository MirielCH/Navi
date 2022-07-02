# clans.py
"""Provides access to the table "clans" in the database"""


from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import List, NamedTuple, Optional, Tuple, Union

from database import errors
from resources import exceptions, settings, strings


# Containers
@dataclass()
class Clan():
    """Object that represents a record from table "clans"."""
    alert_enabled: bool
    alert_message: str
    channel_id: int
    clan_name: str
    leader_id: int
    member_ids: Tuple[int]
    quest_user_id: int
    stealth_current: int
    stealth_threshold: int
    upgrade_quests_enabled: bool
    record_exists: bool = True

    async def delete(self) -> None:
        """Deletes the clan record from the database. Also calls refresh().

        Raises
        ------
        RecordExistsError if there was no error but the record was not deleted.
        """
        await _delete_clan(self.clan_name)
        await self.refresh()
        if self.record_exists:
            error_message = f'Clan got deleted but record still exists.\n{self}'
            await errors.log_error(error_message)
            raise exceptions.RecordExistsError(error_message)

    async def refresh(self) -> None:
        """Refreshes clan data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_settings = await get_clan_by_clan_name(self.clan_name)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.alert_enabled = new_settings.alert_enabled
        self.alert_message = new_settings.alert_message
        self.channel_id = new_settings.channel_id
        self.leader_id = new_settings.leader_id
        self.member_ids = new_settings.member_ids
        self.quest_user_id = new_settings.quest_user_id
        self.stealth_current = new_settings.stealth_current
        self.stealth_threshold = new_settings.stealth_threshold
        self.upgrade_quests_enabled = new_settings.upgrade_quests_enabled

    async def update(self, **kwargs) -> None:
        """Updates the clan record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            alert_enabled: bool
            alert_message: str
            channel_id: int
            clan_name: str
            leader_id: int
            member_ids: Union[Tuple[int],List[int]] (up to 10)
            quest_user_id: int
            stealth_current: int
            stealth_threshold: int
            upgrade_quests_enabled: bool

        Raises
        ------
        sqlite3.Error if something happened within the database.
        NoArgumentsError if no kwargs are passed (need to pass at least one)
        Also logs all errors to the database.
        """
        await _update_clan(self.clan_name, **kwargs)
        await self.refresh()


class ClanRaid(NamedTuple):
    """Object that represents a record from table "clans_raids"."""
    clan_name: str
    energy: int
    raid_time: datetime
    user_id: int

class ClanLeaderboard(NamedTuple):
    """Object that provides all data necessary for the clan leaderboard."""
    best_raids: Tuple[ClanRaid]
    worst_raids: Tuple[ClanRaid]

class ClanWeeklyReport(NamedTuple):
    """Object that provides all data necessary for a weekly report."""
    best_raid: ClanRaid
    energy_total: int
    praise: str
    roast: str
    worst_raid: ClanRaid

# Miscellaneous functions
async def _dict_to_clan(record: dict) -> Clan:
    """Creates a Clan object from a database record

    Arguments
    ---------
    record: Database record from table "clans" as a dict.

    Returns
    -------
    Clan object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_clan'
    try:
        clan = Clan(
            alert_enabled = bool(record['alert_enabled']),
            alert_message = record['alert_message'],
            channel_id = record['channel_id'],
            clan_name = record['clan_name'],
            leader_id = record['leader_id'],
            member_ids = (
                record['member1_id'],
                 record['member2_id'],
                 record['member3_id'],
                 record['member4_id'],
                 record['member5_id'],
                 record['member6_id'],
                 record['member7_id'],
                 record['member8_id'],
                 record['member9_id'],
                 record['member10_id'],
            ),
            quest_user_id = record['quest_user_id'],
            stealth_current = record['stealth_current'],
            stealth_threshold = record['stealth_threshold'],
            upgrade_quests_enabled = bool(record['upgrade_quests_enabled'])
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return clan


async def _dict_to_clan_raid(record: dict) -> ClanRaid:
    """Creates a ClanRaid object from a database record

    Arguments
    ---------
    record: Database record from table "clans_raids" as a dict.

    Returns
    -------
    ClanRaid object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_leaderbord_user'
    try:
        clan_raid = ClanRaid(
            clan_name = record['clan_name'],
            energy = record['energy'],
            raid_time = datetime.fromisoformat(record['raid_time']),
            user_id = record['user_id']
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return clan_raid


# Read Data
async def get_clan_by_user_id(user_id: int) -> Clan:
    """Gets all settings for a clan (EPIC RPG guild) from a user id. The provided user can be a member or the owner.

    Returns
    -------
    Clan object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans'
    function_name = 'get_clan_by_user_id'
    sql = (
        f'SELECT * FROM {table} WHERE leader_id=? or member1_id=? or member2_id=? or member3_id=? or member4_id=? '
        f'or member5_id=? or member6_id=? or member7_id=? or member8_id=? or member9_id=? or member10_id=?'
    )
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,) * 11)
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(f'No clan data found in database for user "{user_id}".')
    clan = await _dict_to_clan(dict(record))

    return clan


async def get_clan_by_clan_name(clan_name: str) -> Clan:
    """Gets all settings for a clan (EPIC RPG guild) from a clan name.

    Returns
    -------
    Clan object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans'
    function_name = 'get_clan_by_clan_name'
    sql = f'SELECT * FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(f'No clan data found in database with clan name "{clan_name}".')
    clan = await _dict_to_clan(dict(record))

    return clan


async def get_all_clans() -> Tuple[Clan]:
    """Gets the clan settings for all clans.

    Returns
    -------
    Tuple[Clan]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans'
    function_name = 'get_all_clans'
    sql = f'SELECT * FROM {table}'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        raise exceptions.NoDataFoundError('No clan data found in database.')
    clans = []
    for record in records:
        clan = await _dict_to_clan(dict(record))
        clans.append(clan)

    return tuple(clans)


async def get_clan_raid(clan_name: str, user_id: str, raid_time: datetime) -> ClanRaid:
    """Gets a specific clan raid based on a specific user, clan and an EXACT time.
    Since the exact time is usually unknown, this is mostly used for returning the object after insertion.

    Returns
    -------
    ClanRaid object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans_raids'
    function_name = 'get_clan_raid'
    sql = f'SELECT * FROM {table} WHERE clan_name=? AND user_id=? AND raid_time=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name, user_id, raid_time))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(
            f'No clan raid data found in database for clan name "{clan_name}", user id "{user_id}" '
            f'and raid time "{raid_time}".'
        )
    clan_raid = await _dict_to_clan_raid(dict(record))

    return clan_raid


async def get_leaderboard(clan: Clan) -> ClanLeaderboard:
    """Gets the clan leaderboard for a clan.

    Returns
    -------
    ClanLeaderboard object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans_raids'
    function_name = 'get_leaderboard'
    stealth_threshold = 1000
    sql = f'SELECT * FROM {table} WHERE clan_name=? AND energy>={stealth_threshold} ORDER BY energy DESC LIMIT 5'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan.clan_name,))
        records_best = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    sql = f'SELECT * FROM {table} WHERE clan_name=? AND energy<{stealth_threshold} ORDER BY energy ASC LIMIT 5'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan.clan_name,))
        records_worst = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    best_raids = []
    worst_raids = []
    for record_best in records_best:
        best_raid = await _dict_to_clan_raid(dict(record_best))
        best_raids.append(best_raid)
    for record_worst in records_worst:
        worst_raid = await _dict_to_clan_raid(dict(record_worst))
        worst_raids.append(worst_raid)

    clan_leaderboard = ClanLeaderboard(
        best_raids = tuple(best_raids) if best_raids else (),
        worst_raids = tuple(worst_raids) if worst_raids else ()
    )

    return clan_leaderboard


async def get_weekly_report(clan: Clan) -> ClanWeeklyReport:
    """Gets the weekly report for a clan.

    Returns
    -------
    ClanWeeklyReport object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'clans_leaderboard_praises'
    function_name = 'get_weekly_report'
    sql = f'SELECT text FROM {table} ORDER BY RANDOM() LIMIT 1'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        praise_record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    table = 'clans_leaderboard_roasts'
    sql = f'SELECT text FROM {table} ORDER BY RANDOM() LIMIT 1'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        roast_record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    table = 'clans_raids'
    sql = f'SELECT energy FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan.clan_name,))
        all_raids_records = cur.fetchall()
    except:
        raise exceptions.NoDataFoundError(f'No raids found for clan {clan.clan_name}')
    energy_total = 0
    for record in all_raids_records:
        energy_total += record['energy']
    clan_leaderboard = await get_leaderboard(clan)
    weekly_report = ClanWeeklyReport(
        best_raid =  clan_leaderboard.best_raids[0] if clan_leaderboard.best_raids else None,
        energy_total = energy_total,
        praise = praise_record['text'],
        roast = roast_record['text'],
        worst_raid = clan_leaderboard.worst_raids[0] if clan_leaderboard.worst_raids else None,
    )

    return weekly_report


# Write Data
async def _delete_clan(clan_name: str) -> None:
    """Deletes clan record. Use Clan.delete() to trigger this function.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table = 'clans'
    function_name = '_delete_clan'
    sql = f'DELETE FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    await delete_clan_leaderboard()


async def _update_clan(clan_name: str, **kwargs) -> None:
    """Updates clan record. Use Clan.update() to trigger this function.

    Arguments
    ---------
    clan_name: str
    kwargs (column=value):
        alert_enabled: bool
        alert_message: str
        channel_id: int
        clan_name: str
        leader_id: int
        member_ids: Union[Tuple[int],List[int]] (up to 10)
        stealth_current: int
        stealth_threshold: int

    Note: If member_ids is passed and there are less than 10 members, the remaining columns will be filled with NULL.
    If member_ids is not passed, no members will be changed.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'clans'
    function_name = '_update_clan'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    member_ids = [None] * 10
    member_ids_kwarg = kwargs.get('member_ids', None)
    if member_ids_kwarg is not None:
        for index, member_id_kwarg in enumerate(member_ids_kwarg):
            member_ids[index] = member_id_kwarg
        for index, member_id in enumerate(member_ids):
            kwargs[f'member{index+1}_id'] = member_id
        kwargs.pop('member_ids', None)
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['clan_name_old'] = clan_name
        sql = f'{sql} WHERE clan_name = :clan_name_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def delete_clan_leaderboard(clan_name: Optional[str] = None) -> None:
    """Deletes records in "clans_raids". If clan_name is omitted, this deletes ALL RECORDS!

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table = 'clans_raids'
    function_name = 'delete_clan_leaderboard'
    sql = f'DELETE FROM {table}' if clan_name is None else f'DELETE FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql) if clan_name is None else cur.execute(sql, (clan_name,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_clan(clan_name: str, leader_id: int, member_ids: Union[Tuple[int],List[int]]) -> Clan:
    """Inserts a record in the table "clans".

    Arguments
    ---------
    clan_name: str
    leader_id: int
    member_ids: Union[Tuple[int],List[int]] (up to 10)

    Note: If member_ids is passed and there are less than 10 members, the remaining columns will be filled with NULL.
    If member_ids is not passed, no members will be changed.

    Returns
    -------
    Clan object with the newly created clan.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_clan'
    table = 'clans'
    sql = (
        f'INSERT INTO {table} '
        f'(clan_name, stealth_current, stealth_threshold, leader_id, '
        f'member1_id, member2_id, member3_id, member4_id, member5_id, '
        f'member6_id, member7_id, member8_id, member9_id, member10_id) '
        f'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    )
    member_ids_all = [None] * 10
    if member_ids is not None:
        for index, member_id in enumerate(member_ids):
            member_ids_all[index] = member_id
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(
            sql,
            (clan_name, 1, settings.CLAN_DEFAULT_STEALTH_THRESHOLD, leader_id,
             member_ids_all[0], member_ids_all[1], member_ids_all[2], member_ids_all[3], member_ids_all[4],
             member_ids_all[5], member_ids_all[6], member_ids_all[7], member_ids_all[8], member_ids_all[9])
        )
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    clan = await get_clan_by_clan_name(clan_name)

    return clan


async def insert_clan_raid(clan_name: str, user_id: int, energy: int, raid_time: datetime) -> Clan:
    """Inserts a record in the table "clans_raids".

    Returns
    -------
    ClanRaid object with the newly created clan raid.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_clan_raid'
    table = 'clans_raids'
    sql = f'INSERT INTO {table} (clan_name, user_id, energy, raid_time) VALUES (?, ?, ?, ?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name, user_id, energy, raid_time))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    clan_raid = await get_clan_raid(clan_name, user_id, raid_time)

    return clan_raid