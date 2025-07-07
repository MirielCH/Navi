# clans.py
"""Provides access to the table "clans" in the database"""


from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Any, NamedTuple, Optional, Union

from database import errors
from resources import exceptions, settings, strings


# Containers
@dataclass()
class ClanMember():
    """Object that represents a record from table "clan_members"."""
    clan_name: str
    member_type: str
    user_id: int

    async def refresh(self) -> None:
        """Refreshes clan member data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_settings = await get_clan_member(self.user_id)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.clan_name = new_settings.clan_name
        self.member_type = new_settings.member_type

    async def update(self, **updated_settings) -> None:
        """Updates the clan member record in the database. Also calls refresh().

        Arguments
        ---------
        updated_settings (column=value):
            clan_name: str
            member_type: str

        Raises
        ------
        sqlite3.Error if something happened within the database.
        NoArgumentsError if no kwargs are passed (need to pass at least one)
        Also logs all errors to the database.
        """
        await _update_clan_member(self.user_id, **updated_settings)
        await self.refresh()

@dataclass()
class Clan():
    """Object that represents a record from table "clans"."""
    alert_enabled: bool
    alert_message: str
    alert_visible: bool
    channel_id: int
    clan_name: str
    members: tuple[ClanMember, ...]
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
        self.alert_visible = new_settings.alert_visible
        self.channel_id = new_settings.channel_id
        self.members = new_settings.members
        self.quest_user_id = new_settings.quest_user_id
        self.stealth_current = new_settings.stealth_current
        self.stealth_threshold = new_settings.stealth_threshold
        self.upgrade_quests_enabled = new_settings.upgrade_quests_enabled

    async def update(self, **updated_settings) -> None:
        """Updates the clan record in the database. Also calls refresh().

        Arguments
        ---------
        updated_settings (column=value):
            alert_enabled: bool
            alert_message: str
            alert_visible: bool
            channel_id: int
            clan_name: str
            leader_ids: list[int] (required if member_ids is provided)
            member_ids: list[int] (needs to contain ALL members of the clan!)
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
        await _update_clan(self.clan_name, **updated_settings)
        await self.refresh()


class ClanRaid(NamedTuple):
    """Object that represents a record from table "clans_raids"."""
    clan_name: str
    energy: int
    raid_time: datetime
    user_id: int

class ClanLeaderboard(NamedTuple):
    """Object that provides all data necessary for the clan leaderboard."""
    best_raids: tuple[ClanRaid, ...]
    worst_raids: tuple[ClanRaid, ...]

class ClanWeeklyReport(NamedTuple):
    """Object that provides all data necessary for a weekly report."""
    best_raid: ClanRaid | None
    energy_total: int
    praise: str
    roast: str
    worst_raid: ClanRaid | None


# Miscellaneous functions
async def _dict_to_clan(record_clan: dict[str, Any], clan_members: tuple[ClanMember, ...]) -> Clan:
    """Creates a Clan object from a database record and a list of clan members

    Arguments
    ---------
    record_clan: Database record from table "clans" as a dict.
    clan_members: List of clan members.
    
    Returns
    -------
    Clan object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name: str = '_dict_to_clan'
    leader_found: bool = False
    clan_member: ClanMember
    
    try:
        clan = Clan(
            alert_enabled = bool(record_clan['alert_enabled']),
            alert_message = record_clan['alert_message'],
            alert_visible = bool(record_clan['alert_visible']),
            channel_id = record_clan['channel_id'],
            clan_name = record_clan['clan_name'],
            members = clan_members,
            quest_user_id = record_clan['quest_user_id'],
            stealth_current = record_clan['stealth_current'],
            stealth_threshold = record_clan['stealth_threshold'],
            upgrade_quests_enabled = bool(record_clan['upgrade_quests_enabled'])
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return clan


async def _dict_to_clan_member(record: dict[str, Any]) -> ClanMember:
    """Creates a ClanMember object from a database record

    Arguments
    ---------
    record: Database record from table "clan_members" as a dict.

    Returns
    -------
    ClanMember object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name: str = '_dict_to_clan_member'
    try:
        clan_member = ClanMember(
            clan_name = record['clan_name'],
            member_type = record['member_type'],
            user_id = record['user_id']
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return clan_member


async def _dict_to_clan_raid(record: dict[str, Any]) -> ClanRaid:
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
    function_name: str = '_dict_to_leaderbord_user'
    try:
        clan_raid = ClanRaid(
            clan_name = record['clan_name'],
            energy = record['energy'],
            raid_time = record['raid_time'],
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
    function_name: str = 'get_clan_by_user_id'
    table: str = 'clan_members'
    sql: str = f'SELECT * FROM {table} WHERE user_id=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        record_clan_member: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record_clan_member:
        raise exceptions.NoDataFoundError(f'No clan member found in database for user "{user_id}".')
    
    table = 'clans'
    sql = f'SELECT * FROM {table} WHERE clan_name=?'
    clan_name: str = dict(record_clan_member)['clan_name']
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        record_clan: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record_clan:
        raise exceptions.NoDataFoundError(f'Clan "{clan_name}" not found in database.')

    clan_members: tuple[ClanMember, ...] = await get_clan_members_by_clan_name(clan_name)
    clan: Clan = await _dict_to_clan(dict(record_clan), clan_members)

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
    function_name: str = 'get_clan_by_clan_name'    
    table: str = 'clans'
    sql: str = f'SELECT * FROM {table} WHERE clan_name=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        record_clan: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not record_clan:
        raise exceptions.NoDataFoundError(f'No clan found in database for clan name "{clan_name}".')

    clan_members: tuple[ClanMember, ...] = await get_clan_members_by_clan_name(clan_name)
    clan: Clan = await _dict_to_clan(dict(record_clan), clan_members)
    
    return clan


async def get_clan_member(user_id: int) -> ClanMember:
    """Get a clan member record for a specific user.

    Returns
    -------
    ClanMember object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    function_name: str = 'get_clan_member'    
    table: str = 'clan_members'
    sql: str = f'SELECT * FROM {table} WHERE user_id=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        record: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    
    if not record:
        raise exceptions.NoDataFoundError(f'No clan member found in database for user id "{user_id}".')
   
    clan_member: ClanMember = await _dict_to_clan_member(dict(record))

    return clan_member


async def get_all_clans() -> tuple[Clan, ...]:
    """Gets the clan settings for all clans.

    Returns
    -------
    tuple[Clan, ...]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    function_name: str = 'get_all_clans'
    table: str = 'clans'
    sql: str = f'SELECT * FROM {table}'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql)
        records: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        raise exceptions.NoDataFoundError('No clan data found in database.')
    
    clans: list[Clan] = []
    record: Any
    clan_members: tuple[ClanMember, ...]
    for record in records:
        clan_members = await get_clan_members_by_clan_name(record['clan_name'])
        clan: Clan = await _dict_to_clan(dict(record), clan_members)
        clans.append(clan)

    return tuple(clans)


async def get_clan_members_by_clan_name(clan_name: str) -> tuple[ClanMember, ...]:
    """Gets all clan members of a clan.

    Returns
    -------
    tuple[ClanMember, ...]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    function_name: str = 'get_clan_members_by_clan_name'
    table: str = 'clan_members'
    sql: str = f'SELECT * FROM {table} WHERE clan_name = ?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        records: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    record: Any
    clan_members: list[ClanMember] = []
    for record in records:
        clan_member: ClanMember = await _dict_to_clan_member(dict(record))
        clan_members.append(clan_member)

    return tuple(clan_members)


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
    table: str = 'clans_raids'
    function_name: str = 'get_clan_raid'
    sql: str = f'SELECT * FROM {table} WHERE clan_name=? AND user_id=? AND raid_time=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name, user_id, raid_time))
        record: Any = cur.fetchone()
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
    clan_raid: ClanRaid = await _dict_to_clan_raid(dict(record))

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
    table: str = 'clans_raids'
    function_name: str = 'get_leaderboard'
    stealth_threshold: int = 1000
    sql: str = f'SELECT * FROM {table} WHERE clan_name=? AND energy>={stealth_threshold} ORDER BY energy DESC LIMIT 5'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan.clan_name,))
        records_best: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    sql = f'SELECT * FROM {table} WHERE clan_name=? AND energy<{stealth_threshold} ORDER BY energy ASC LIMIT 5'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan.clan_name,))
        records_worst: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    best_raids: list[ClanRaid] = []
    worst_raids: list[ClanRaid] = []
    record_best: Any
    record_worst: Any
    for record_best in records_best:
        best_raid: ClanRaid = await _dict_to_clan_raid(dict(record_best))
        best_raids.append(best_raid)
    for record_worst in records_worst:
        worst_raid: ClanRaid = await _dict_to_clan_raid(dict(record_worst))
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
    table: str = 'clans_leaderboard_praises'
    function_name: str = 'get_weekly_report'
    sql: str = f'SELECT text FROM {table} ORDER BY RANDOM() LIMIT 1'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql)
        praise_record: Any = cur.fetchone()
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
        roast_record: Any = cur.fetchone()
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
        all_raids_records: list[Any] = cur.fetchall()
    except:
        raise exceptions.NoDataFoundError(f'No raids found for clan {clan.clan_name}')
    energy_total: int = 0
    record: Any
    for record in all_raids_records:
        energy_total += record['energy']
    clan_leaderboard: ClanLeaderboard = await get_leaderboard(clan)
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
    """Deletes the clan record and all clan member records for a clan. Use Clan.delete() to trigger this function.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table: str = 'clans'
    function_name: str = '_delete_clan'
    sql: str = f'DELETE FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    await delete_clan_members(clan_name)
    await delete_clan_leaderboard(clan_name)


async def delete_clan_members(clan_name: str) -> None:
    """Deletes all clan member records for a clan.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table: str = 'clan_members'
    function_name: str = '_delete_clan_members'
    sql: str = f'DELETE FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def _update_clan(current_clan_name: str, **updated_settings) -> None:
    """Updates a clan record. Use Clan.update() to trigger this function.
    
    Note:
    - If the argument "member_ids" is specified, it needs to contain ALL member ids of the clan.
    All members not in this list will be deleted.
    - If the argument "member_ids" is specified, argument "leader_ids" also needs to be specified.

    Arguments
    ---------
    clan_name: str
    updated_settings (column=value):
        alert_enabled: bool
        alert_message: str
        alert_visible: bool
        channel_id: int
        leader_ids: list[int]
        member_ids: list[int]
        clan_name: str
        stealth_current: int
        stealth_threshold: int
        
    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table: str = 'clans'
    function_name: str = '_update_clan'
    if not updated_settings:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    if 'member_ids' in updated_settings and not 'leader_ids' in updated_settings:
        error_msg: str = 'If argument "member_ids" is specified, argument "leader_ids" also needs to be specified.'
        await errors.log_error(error_msg)
        raise exceptions.MissingArgumentsError(error_msg)

    member_ids: list[int] = updated_settings.pop('member_ids', [])
    leader_ids: list[int] = updated_settings.pop('leader_ids', [])

    if updated_settings:
        try:
            cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
            sql: str = f'UPDATE {table} SET'
            for updated_setting in updated_settings:
                sql = f'{sql} {updated_setting} = :{updated_setting},'
            updated_settings['clan_name_old'] = current_clan_name
            sql = sql.strip(",")
            sql = f'{sql} WHERE clan_name = :clan_name_old'
            cur.execute(sql, updated_settings)
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise

    clan_name = updated_settings['clan_name'] if 'clan_name' in updated_settings else current_clan_name

    if clan_name != current_clan_name and not member_ids:
        clan_members: tuple[ClanMember, ...] = await get_clan_members_by_clan_name(current_clan_name)
        clan_member: ClanMember
        for clan_member in clan_members:
            await clan_member.update(clan_name=clan_name)

    member_type: str
    if leader_ids and not member_ids:
        clan_members: tuple[ClanMember, ...] = await get_clan_members_by_clan_name(clan_name)
        clan_member: ClanMember
        for clan_member in clan_members:
            member_type = 'leader' if clan_member.user_id in leader_ids else 'member'
            await clan_member.update(member_type=member_type)

    if member_ids:
        await delete_clan_members(clan_name)
        member_id: int
        for member_id in member_ids:
            member_type = 'leader' if member_id in leader_ids else 'member'
            try:
                clan_member = await get_clan_member(member_id)
                await clan_member.update(clan_name=clan_name, member_type=member_type)
            except exceptions.NoDataFoundError:
                await insert_clan_member(clan_name, member_id, member_type)
        

async def _update_clan_member(user_id: str, **updated_settings) -> None:
    """Updates a clan member record. Use ClanMember.update() to trigger this function.

    Arguments
    ---------
    user_id: int
    updated_settings (column=value):
        clan_name: str
        member_type: str

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table: str = 'clan_members'
    function_name: str = '_update_clan_member'
    if not updated_settings:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        sql: str = f'UPDATE {table} SET'
        for updated_setting in updated_settings:
            sql = f'{sql} {updated_setting} = :{updated_setting},'
        updated_settings['user_id'] = user_id
        sql = sql.strip(",")
        sql = f'{sql} WHERE user_id = :user_id'
        cur.execute(sql, updated_settings)
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
    table: str = 'clans_raids'
    function_name: str = 'delete_clan_leaderboard'
    sql: str = f'DELETE FROM {table}' if clan_name is None else f'DELETE FROM {table} WHERE clan_name=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql) if clan_name is None else cur.execute(sql, (clan_name,))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_clan(clan_name: str, leader_ids: list[int], member_ids: list[int]) -> Clan:
    """Inserts a record in the table "clans".

    Arguments
    ---------
    clan_name: str
    leader_ids: list[int]
    member_ids: list[int]

    Returns
    -------
    Clan object with the newly created clan.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name: str = 'insert_clan'
    table: str = 'clans'
    sql: str = (
        f'INSERT INTO {table} (clan_name, stealth_current, stealth_threshold) VALUES (?, ?, ?)'
    )
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name, 1, settings.CLAN_DEFAULT_STEALTH_THRESHOLD))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    member_id: int
    for member_id in member_ids:
        member_type = 'leader' if member_id in leader_ids else 'member'
        try:
            clan_member: ClanMember = await get_clan_member(member_id)
            await clan_member.update(clan_name=clan_name, member_type=member_type)
        except exceptions.NoDataFoundError:
            await insert_clan_member(clan_name, member_id, member_type)
    
    clan: Clan = await get_clan_by_clan_name(clan_name)

    return clan


async def insert_clan_member(clan_name: str, user_id: int, member_type: str) -> ClanMember:
    """Inserts a record in the table "clan_members".

    Returns
    -------
    ClanMember object with the newly created clan member.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name: str = 'insert_clan_member'
    table: str = 'clan_members'
    sql: str = f'INSERT INTO {table} (user_id, clan_name, member_type) VALUES (?, ?, ?)'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, clan_name, member_type))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    clan_member: ClanMember = await get_clan_member(user_id)

    return clan_member


async def insert_clan_raid(clan_name: str, user_id: int, energy: int, raid_time: datetime) -> ClanRaid:
    """Inserts a record in the table "clans_raids".

    Returns
    -------
    ClanRaid object with the newly created clan raid.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name: str = 'insert_clan_raid'
    table: str = 'clans_raids'
    sql: str = f'INSERT INTO {table} (clan_name, user_id, energy, raid_time) VALUES (?, ?, ?, ?)'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name, user_id, energy, raid_time))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    clan_raid: ClanRaid = await get_clan_raid(clan_name, user_id, raid_time)

    return clan_raid