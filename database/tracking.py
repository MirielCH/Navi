# tracking.py
"""Provides access to the tables "tracking_log" and "tracking_leaderboard" in the database"""


from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from typing import NamedTuple, Optional, Tuple

from discord.ext import tasks

from database import errors, users
from resources import exceptions, settings, strings


# Containers
@dataclass()
class LogEntry():
    """Object that represents a record from table "tracking_log"."""
    command: str
    command_count: int
    date_time: datetime
    entry_type: str
    guild_id: int
    user_id: int
    record_exists: bool = True

    async def delete(self) -> None:
        """Deletes the clan record from the database. Also calls refresh().

        Raises
        ------
        RecordExistsError if there was no error but the record was not deleted.
        """
        await _delete_log_entry(self)
        await self.refresh()
        if self.record_exists:
            error_message = f'Log entry got deleted but record still exists.\n{self}'
            await errors.log_error(error_message)
            raise exceptions.RecordExistsError(error_message)

    async def refresh(self) -> None:
        """Refreshes the log entry from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_settings = await get_log_entry(self.user_id, self.guild_id, self.command, self.date_time)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.command = new_settings.command
        self.command_count = new_settings.command_count
        self.entry_type = new_settings.entry_type
        self.date_time = new_settings.date_time
        self.guild_id = new_settings.guild_id
        self.user_id = new_settings.user_id

    async def update(self, **kwargs) -> None:
        """Updates the log entry record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            command: str
            command_count: int
            date_time: datetime
            entry_type: Literal['single', 'summary']
            guild_id: int
        """
        await _update_log_entry(self, **kwargs)
        await self.refresh()

class LogReport(NamedTuple):
    """Object that represents a report based on a certain amount of log entries."""
    adventure_amount: int
    epic_guard_amount: int
    farm_amount: int
    guild_id: int # Set to None if no guild_id was provided
    hunt_amount: str
    timeframe: timedelta
    training_amount: int
    ultraining_amount: int
    user_id: int
    work_amount: int

@dataclass()
class LogLeaderboardUser():
    """Object that represents a user report from table "tracking_leaderboard"."""
    all_time: int
    command: str
    guild_id: int # Set to None if report_type is 'global'
    report_type: str # Either 'guild' or 'global'
    last_1h: int
    last_12h: int
    last_24h: int
    last_7d: int
    last_4w: int
    last_12m: int
    updated: int
    user_id: int

    async def refresh(self) -> None:
        """Refreshes leaderboard user data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_settings = await get_log_leaderboard_user(self.user_id, self.guild_id, self.command)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.all_time = new_settings.all_time
        self.command = new_settings.command
        self.guild_id = new_settings.guild_id
        self.report_type = new_settings.report_type
        self.last_1h = new_settings.last_1h
        self.last_12h = new_settings.last_12h
        self.last_24h = new_settings.last_24h
        self.last_7d = new_settings.last_7d
        self.last_4w = new_settings.last_4w
        self.last_12m = new_settings.last_12m
        self.updated = new_settings.updated
        self.user_id = new_settings.user_id

    async def update(self, **kwargs) -> None:
        """Updates the leaderboard record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            user_id: int
            guild_id: int
            command: str
            last_1h: int
            last_12h: int
            last_24h: int
            last_7d: int
            last_4w: int
            last_1y: int
            all_time: int
            updated: datetime UTC - If not specified, will be set to current time
        """
        await _update_log_leaderboard_user(self, **kwargs)
        await self.refresh()

# Tasks
@tasks.loop(minutes=5.0)
async def log_to_leaderboard():
    """Task that converts the tracking log entries into leaderboard entries"""
    async def count_commands(log_entries: Tuple[LogEntry]) -> dict:
        """Returns dict with total command count for each guild for a tuple of log entries

        Returns
        ---------
        dict with command count per guild
        key: value --> guild_id: command count
        """
        guild_command_count = {}
        for log_entry in log_entries:
            if log_entry.guild_id in guild_command_count:
                guild_command_count[log_entry.guild_id] += log_entry.command_count
            else:
                guild_command_count[log_entry.guild_id] = log_entry.command_count
        return guild_command_count

    all_users: users.User = await users.get_all_users()
    for user in all_users:
        log_entries_1h = await get_log_entries(user.user_id, 'hunt', timedelta(hours=1))
        count_1h = await count_commands(log_entries_1h)
        log_entries_12h = await get_log_entries(user.user_id, 'hunt', timedelta(hours=12))
        count_12h = await count_commands(log_entries_12h)
        log_entries_24h = await get_log_entries(user.user_id, 'hunt', timedelta(hours=24))
        count_24h = await count_commands(log_entries_24h)
        log_entries_7d = await get_log_entries(user.user_id, 'hunt', timedelta(days=7))
        count_7d = await count_commands(log_entries_7d)
        log_entries_4w = await get_log_entries(user.user_id, 'hunt', timedelta(weeks=4))
        count_4w = await count_commands(log_entries_4w)
        log_entries_1y = await get_log_entries(user.user_id, 'hunt', timedelta(weeks=52))
        count_1y = await count_commands(log_entries_1y)
        for guild_id in count_1h:
            pass
        await insert_log_leaderboard_user(user.user_id, )

# Miscellaneous functions
async def _dict_to_log_entry(record: dict) -> LogEntry:
    """Creates a LogEntry object from a database record

    Arguments
    ---------
    record: Database record from table "tracking_log" as a dict.

    Returns
    -------
    LogEntry object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_log_entry'
    try:
        log_entry = LogEntry(
            command = record['command'],
            command_count = record['command_count'],
            date_time = datetime.fromisoformat(record['date_time']),
            entry_type = record['type'],
            guild_id = record['guild_id'],
            user_id = record['user_id'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return log_entry


async def _dict_to_leaderboard_user(record: dict) -> LogEntry:
    """Creates a LogLeaderboardUser object from a database record

    Arguments
    ---------
    record: Database record from table "tracking_leaderboard" as a dict.

    Returns
    -------
    LogLeaderboardUser object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_log_leaderboard_user'
    try:
        log_leaderboard_user = LogLeaderboardUser(
            all_time =  record['all_time'],
            command = record['commmand'],
            guild_id = record['guild_id'],
            last_1h = record['last_1h'],
            last_12h = record['last_12h'],
            last_24h = record['last_24h'],
            last_7d = record['last_7d'],
            last_4w = record['last_4w'],
            last_12m = record['last_12m'],
            report_type = 'global' if record['guild_id'] is None else 'guild',
            updated = datetime.fromisoformat(record['updated']),
            user_id = record['user_id'],
        )

    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return log_leaderboard_user


# Read Data
async def get_log_entry(user_id: int, guild_id: int, command: str, date_time: datetime, entry_type: Optional[str] = 'single') -> LogEntry:
    """Gets a specific log entry based on a specific user, command and an EXACT time.
    Since the exact time is usually unknown, this is mostly used for refreshing an object.

    Returns
    -------
    LogEntry

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = 'get_log_entry'
    sql = f'SELECT * FROM {table} WHERE user_id=? AND guild_id=? AND command=? AND date_time=? AND type=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, guild_id, command, date_time, entry_type))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(
            f'No log data found in database for user "{user_id}", command "{command}" and time "{str(datetime)}".'
        )
    log_entry = await _dict_to_log_entry(dict(record))

    return log_entry


async def get_log_entries(user_id: int, command: str, timeframe: timedelta,
                          guild_id: Optional[int] = None) -> Tuple[LogEntry]:
    """Gets all log entries for one command for a certain amount of time from a user id.
    If the guild_id is specified, the log entries are limited to that guild.

    Arguments
    ---------
    user_id: int
    command: str
    timeframe: timedelta object with the amount of time that should be covered, starting from UTC now
    guild_id: Optional[int]

    Returns
    -------
    Tuple[LogEntry]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = 'get_log_entries'
    sql = (
        f'SELECT * FROM {table} WHERE user_id=? AND date_time>=? AND command=?'
    )
    date_time = datetime.utcnow() - timeframe
    if guild_id is not None: sql = f'{sql} AND guild_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        if guild_id is None:
            cur.execute(sql, (user_id, date_time, command))
        else:
            cur.execute(sql, (user_id, date_time, command, guild_id))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        error_message = f'No log data found in database for timeframe "{str(timeframe)}".'
        if guild_id is not None: error_message = f'{error_message} Guild: {guild_id}'
        raise exceptions.NoDataFoundError(error_message)
    log_entries = []
    for record in records:
        log_entry = await _dict_to_log_entry(dict(record))
        log_entries.append(log_entry)

    return tuple(log_entries)


async def get_all_log_entries(user_id: int) -> Tuple[LogEntry]:
    """Gets ALL log entries for a user.

    Arguments
    ---------
    user_id: int

    Returns
    -------
    Tuple[LogEntry]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = 'get_all_log_entries'
    sql = (
        f'SELECT * FROM {table} WHERE user_id=?'
    )
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        error_message = f'No log data found in database for user {user_id}".'
        raise exceptions.NoDataFoundError(error_message)
    log_entries = []
    for record in records:
        log_entry = await _dict_to_log_entry(dict(record))
        log_entries.append(log_entry)

    return tuple(log_entries)


async def get_old_log_entries(days: int) -> Tuple[LogEntry]:
    """Gets all single log entries older than a certain amount of days.

    Arguments
    ---------
    user_id: int
    days: amount of days that should be kept as single entries
    guild_id: Optional[int]

    Returns
    -------
    Tuple[LogEntry]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = 'get_old_log_entries'
    sql = (
        f'SELECT * FROM {table} WHERE date_time<? AND type=?'
    )
    date_time = datetime.utcnow() - timedelta(days=days)
    date_time = date_time.replace(hour=0, minute=0, second=0)
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (date_time, 'single'))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        error_message = f'No log data found in database older than {days} days".'
        raise exceptions.NoDataFoundError(error_message)
    log_entries = []
    for record in records:
        log_entry = await _dict_to_log_entry(dict(record))
        log_entries.append(log_entry)

    return tuple(log_entries)


async def get_log_report(user_id: int, timeframe: timedelta,
                         guild_id: Optional[int] = None) -> LogReport:
    """Gets a summary log report for all commands for a certain amount of time from a user id.
    If the guild_id is specified, the report is limited to that guild.

    Returns
    -------
    LogReport object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = 'get_log_report'
    sql = f'SELECT command, SUM(command_count) FROM {table} WHERE user_id=? AND date_time>=?'
    date_time = datetime.utcnow() - timeframe
    if guild_id is not None: sql = f'{sql} AND guild_id=?'
    sql = f'{sql} GROUP BY command'
    try:
        cur = settings.NAVI_DB.cursor()
        if guild_id is None:
            cur.execute(sql, (user_id, date_time))
        else:
            cur.execute(sql, (user_id, date_time, guild_id))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    records_data = {
        'adventure': 0,
        'epic guard': 0,
        'farm': 0,
        'hunt': 0,
        'training': 0,
        'ultraining': 0,
        'work': 0,
    }
    for record in records:
        record = dict(record)
        records_data[record['command']] = record['SUM(command_count)']
    log_report = LogReport(
        adventure_amount = records_data['adventure'],
        epic_guard_amount = records_data['epic guard'],
        farm_amount = records_data['farm'],
        hunt_amount = records_data['hunt'],
        training_amount = records_data['training'],
        ultraining_amount = records_data['ultraining'],
        work_amount = records_data['work'],
        guild_id = guild_id,
        timeframe = timeframe,
        user_id = user_id
    )
    return log_report


async def get_log_leaderboard_user(user_id: int, guild_id: int, command: str) -> LogLeaderboardUser:
    """Gets a guild or global leaderboard.

    Arguments
    ---------
    command: str
    guild_id: Optional[int]

    Returns
    -------
    Tuple[LogEntry]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_leaderboard'
    function_name = 'get_log_leaderboard_user'
    sql = f'SELECT * FROM {table} WHERE user_id=? AND guild_id=? AND command=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, guild_id, command))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        error_message = (
            f'No leaderboard data found in database for user "{user_id}", guild "{guild_id}" and command "{command}".'
        )
        raise exceptions.NoDataFoundError(error_message)
    log_leaderboard_user = await _dict_to_leaderboard_user(dict(record))

    return log_leaderboard_user


async def get_log_leaderboard(command: str, guild_id: Optional[int] = None) -> Tuple[LogLeaderboardUser]:
    """Gets a certain record from table "tracking_leaderboard".

    Arguments
    ---------
    command: str
    guild_id: Optional[int]

    Returns
    -------
    Tuple[LogEntry]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'tracking_leaderboard'
    function_name = 'get_log_leaderboard'
    sql = f'SELECT * FROM {table} WHERE command=?'
    if guild_id is not None: sql = f'{sql} AND guild_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (command,)) if guild_id is None else cur.execute(sql, (command, guild_id))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        error_message = f'No leaderboard data found in database for command "{command}".'
        if guild_id is not None: error_message = f'{error_message} Guild: {guild_id}'
        raise exceptions.NoDataFoundError(error_message)
    log_leaderboard = []
    for record in records:
        log_entry = await _dict_to_leaderboard_user(dict(record))
        log_leaderboard.append(log_entry)

    return tuple(log_leaderboard)


# Write Data
async def _delete_log_entry(log_entry: LogEntry) -> None:
    """Deletes a log entry. Use LogEntry.delete() to trigger this function.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = '_delete_log_entry'
    sql = f'DELETE FROM {table} WHERE user_id=? AND guild_id=? AND command=? AND date_time=? AND type=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (log_entry.user_id, log_entry.guild_id, log_entry.command, log_entry.date_time,
                          log_entry.entry_type))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def _update_log_leaderboard_user(log_leaderboard_user: LogLeaderboardUser, **kwargs) -> None:
    """Updates log_leaderboard record. Use LogLeaderboardUser.update() to trigger this function.

    Arguments
    ---------
    log_leaderboard_user: LogLeaderboardUser
    kwargs (column=value):
        user_id: int
        guild_id: int
        command: str
        last_1h: int
        last_12h: int
        last_24h: int
        last_7d: int
        last_4w: int
        last_1y: int
        all_time: int
        updated: datetime UTC - If not specified, will be set to current time

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'log_leaderboard'
    function_name = '_update_log_leaderboard_user'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    current_time = datetime.utcnow().replace(microsecond=0)
    if 'updated' not in kwargs:
        kwargs['updated'] = current_time
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['user_id_old'] = log_leaderboard_user.user_id
        kwargs['guild_id_old'] = log_leaderboard_user.guild_id
        kwargs['command_old'] = log_leaderboard_user.command
        sql = f'{sql} WHERE user_id = :user_id_old AND guild_id = :guild_id_old AND command = :command_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def _update_log_entry(log_entry: LogEntry, **kwargs) -> None:
    """Updates tracking_log record. Use LogEntry.update() to trigger this function.

    Arguments
    ---------
    user_id: int
    kwargs (column=value):
        command: str
        command_count: int
        date_time: datetime
        entry_type: Literal['single', 'summary']
        guild_id: int
        user_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = '_update_log_entry'
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
        kwargs['user_id_old'] = log_entry.user_id
        kwargs['command_old'] = log_entry.command
        kwargs['date_time_old'] = log_entry.date_time
        kwargs['entry_type_old'] = log_entry.entry_type
        sql = (
            f'{sql} WHERE user_id = :user_id_old AND type = :entry_type_old AND command = :command_old '
            f'AND date_time = :date_time_old'
        )
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_log_entry(user_id: int, guild_id: int,
                           command: str, date_time: datetime) -> LogEntry:
    """Inserts a single record to the table "tracking_log".

    Returns
    -------
    LogEntry object with the newly created log entry.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_log_entry'
    table = 'tracking_log'
    sql = (
        f'INSERT INTO {table} (user_id, guild_id, command, command_count, date_time) VALUES (?, ?, ?, ?, ?)'
    )
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, guild_id, command, 1, date_time))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    log_entry = await get_log_entry(user_id, guild_id, command, date_time)

    return log_entry


async def insert_log_summary(user_id: int, guild_id: int, command: str, date_time: datetime, amount: int) -> LogEntry:
    """Inserts a summary record to the table "tracking_log". If record already exists, count is increased by one instead.

    Returns
    -------
    LogEntry object with the newly created log entry.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_log_summary'
    table = 'tracking_log'
    log_entry = None
    try:
        log_entry = await get_log_entry(user_id, guild_id, command, date_time, 'summary')
    except exceptions.NoDataFoundError:
        pass
    if log_entry is not None:
        await log_entry.update(command_count=log_entry.command_count + amount)
    else:
        sql = (
            f'INSERT INTO {table} (user_id, guild_id, command, command_count, date_time, type) VALUES (?, ?, ?, ?, ?, ?)'
        )
        try:
            cur = settings.NAVI_DB.cursor()
            cur.execute(sql, (user_id, guild_id, command, amount, date_time, 'summary'))
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
        log_entry = await get_log_entry(user_id, guild_id, command, date_time, 'summary')

    return log_entry


async def insert_log_leaderboard_user(user_id: int, guild_id: int, command: str, all_time: int, last_1h: int,
                                      last_12h: int, last_24h: int, last_7d: int, last_4w: int, last_12m: int,
                                      updated: datetime,) -> LogEntry:
    """Inserts a a record to the table "tracking_leaderboard".
    This function first checks if a record exists. If yes, the existing record will be updated instead and
    no new record is inserted.

    Returns
    -------
    LogLeaderBoardUser object with the newly created entry.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_log_leaderboard_user'
    table = 'tracking_leaderboard'
    log_leaderboard_user = None
    try:
        log_leaderboard_user = await get_log_leaderboard_user(user_id, guild_id, command)
    except exceptions.NoDataFoundError:
        pass
    if log_leaderboard_user is not None:
        await log_leaderboard_user.update(all_time=all_time, last_1h=last_1h, last_12h=last_12h, last_24h=last_24h,
                                          last_7d=last_7d, last_4w=last_4w, last_12m=last_12m, updated=updated)
    else:
        sql = (
            f'INSERT INTO {table} (user_id, guild_id, command, command_count, date_time) VALUES (?, ?, ?, ?, ?)'
        )
        try:
            cur = settings.NAVI_DB.cursor()
            cur.execute(sql, (user_id, guild_id, command, all_time, last_1h, last_12h, last_24h, last_7d, last_4w,
                            last_12h, updated))
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
        log_leaderboard_user = await get_log_leaderboard_user(user_id, guild_id, command)

    return log_leaderboard_user


async def delete_log_entries(user_id: int, guild_id: int, command: str, date_time_min: datetime,
                             date_time_max: datetime) -> None:
    """Deletes all single log entries between two datetimes.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'tracking_log'
    function_name = '_delete_log_entries'
    sql = f'DELETE FROM {table} WHERE user_id=? AND guild_id=? AND command=? AND type=? AND date_time BETWEEN ? AND ?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, guild_id, command, 'single', date_time_min, date_time_max))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise