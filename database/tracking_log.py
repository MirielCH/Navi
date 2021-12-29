# tracking_log.py
"""Provides access to the table "tracking_log" in the database"""


from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from typing import List, NamedTuple, Optional, Tuple, Union

from discord.ext import commands

from database import errors
from resources import exceptions, settings, strings


# Containers
@dataclass()
class LogEntry():
    """Object that represents a record from table "tracking_log"."""
    command: str
    command_count: int
    date_time: datetime
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
        """Refreshes clan data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_settings = await get_log_entry(self.user_id, self.command, self.date_time)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.command = new_settings.command
        self.command_count = new_settings.command_count
        self.date_time = new_settings.date_time
        self.guild_id = new_settings.guild_id
        self.user_id = new_settings.user_id

class LogReport(NamedTuple):
    """Object that represents a report based on a certain amount of log entries."""
    command: str
    command_count: int
    guild_id: int # Set to None if report_type is 'global'
    report_type: str # Either 'guild' or 'global'
    timeframe: timedelta
    user_id: int


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
            command = record['commmand'],
            command_count = record['command_count'],
            date_time = datetime.fromisoformat(record['date_time']),
            guild_id = record['guild_id'],
            user_id = record['user_id'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return log_entry


# Read Data
async def get_log_entry(user_id: int, command: str, date_time: datetime) -> LogEntry:
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
    sql = f'SELECT * FROM {table} WHERE user_id=? AND command=? AND date_time>=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, command, date_time))
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
        error_message = f'No log data found in database for timeframe "{str(timedelta)}".'
        if guild_id is not None: error_message = f'{error_message} Guild: {guild_id}'
        raise exceptions.NoDataFoundError(error_message)
    log_entries = []
    for record in records:
        log_entry = await _dict_to_log_entry(dict(record))
        log_entries.append(log_entry)

    return tuple(log_entries)


async def get_log_report(user_id: int, command: str, timeframe: timedelta,
                         guild_id: Optional[int] = None) -> LogReport:
    """Gets a summary log report for one command for a certain amount of time from a user id.
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
    log_entries = await get_log_entries(user_id, command, timeframe, guild_id)
    total_command_count = 0
    for log_entry in log_entries:
        total_command_count += log_entry['command_count']
    log_report = LogReport(
        command = command,
        command_count = total_command_count,
        guild_id = guild_id,
        report_type = 'guild' if guild_id is not None else 'global',
        timeframe = timeframe,
        user_id = user_id
    )

    return log_report


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
    sql = f'DELETE FROM {table} WHERE user_id=? AND command=? AND date_time=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (log_entry.user_id, log_entry.command, log_entry.date_time))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_log_entry(user_id: int, guild_id: int,
                           command: str, date_time: datetime) -> LogEntry:
    """Inserts a a record to the table "tracking_log".

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
    log_entry = await get_log_entry(user_id, command, date_time)

    return log_entry