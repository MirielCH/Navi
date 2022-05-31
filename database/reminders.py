# reminders.py
"""Provides access to the tables "reminders_users" and "reminders_clans" in the database"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from typing import Optional, Tuple

from discord.ext import tasks

from database import errors
from resources import exceptions, settings, strings


# Reminders scheduled for task creation / deletion
scheduled_for_tasks = {}
scheduled_for_deletion = {}


# Containers
@dataclass()
class Reminder():
    """Object that represents a record from the table "reminders_users" or "reminders_clans.
    The attribute "reminder_type" is set accordingly. If it is a user reminder, "clan_name" is None and vice versa."""
    activity: str
    channel_id: int
    clan_name: str
    custom_id: int
    end_time: datetime
    message: str
    reminder_type: str  # "clan" or "user"
    task_name: str # Unique Task name for scheduling tasks (<user_id>-<activity>)
    triggered: bool
    user_id: int
    record_exists: bool = True

    async def delete(self) -> None:
        """Deletes the reminder record from the database. Also calls refresh().
        Also cancels and deletes an active task for this reminder.

        Raises
        ------
        RecordExistsError if there was no error but the record was not deleted.
        Also logs all errors to the database.
        """
        await _delete_reminder(self)
        await self.refresh()
        if self.record_exists:
            error_message = f'Reminder got deleted but record still exists.\n{self}'
            await errors.log_error(error_message)
            raise exceptions.RecordExistsError(error_message)

    async def refresh(self) -> None:
        """Refreshes clan data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            if self.reminder_type == 'clan':
                new_settings = await get_clan_reminder(self.clan_name)
            else:
                new_settings = await get_user_reminder(self.user_id, self.activity, self.custom_id)
        except exceptions.NoDataFoundError as error:
            self.record_exists = False
            return
        self.activity = new_settings.activity
        self.channel_id = new_settings.channel_id
        self.clan_name = new_settings.clan_name
        self.custom_id = new_settings.custom_id
        self.end_time = new_settings.end_time
        self.message = new_settings.message
        self.reminder_type = new_settings.reminder_type
        self.task_name = new_settings.task_name
        self.triggered = new_settings.triggered
        self.user_id = new_settings.user_id

    async def update(self, **kwargs) -> None:
        """Updates the clan record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            activity: str
            channel_id: int
            clan_name: str
            custom_id: int
            end_time: datetime UTC
            message: str
            reminder_type: str  # "clan" or "user"
            triggered: bool
            user_id: int
        """
        await _update_reminder(self, **kwargs)
        await self.refresh()


# Tasks
@tasks.loop(seconds=10.0)
async def schedule_reminders():
    """Task that reads all due reminders from the database and schedules them for task creation"""
    try:
        due_user_reminders = await get_due_user_reminders()
    except exceptions.NoDataFoundError:
        due_user_reminders = ()
    try:
        due_clan_reminders = await get_due_clan_reminders()
    except exceptions.NoDataFoundError:
        due_clan_reminders = ()
    due_reminders = list(due_user_reminders) + list(due_clan_reminders)
    for reminder in due_reminders:
        try:
            scheduled_for_tasks[reminder.task_name] = reminder
            await reminder.update(triggered=True)
        except Exception as error:
            await errors.log_error(
                f'Error scheduling a reminder.\nFunction: schedule_reminders\nReminder: {reminder}\nError: {error}'
        )


# Miscellaneous functions
async def _dict_to_reminder(record: dict) -> Reminder:
    """Creates a Reminder object from a database record

    Arguments
    ---------
    record: Database record from table "reminders_users" or "reminders_clans" as a dict.

    Returns
    -------
    Reminder object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_reminder'
    try:
        user_id = record.get('user_id', None)
        custom_id = record.get('custom_id', None)
        if user_id is None:
            reminder_type = 'clan'
            task_name = f"{record['clan_name']}-{record['activity']}"
        else:
            reminder_type = 'user'
            if custom_id is not None:
                task_name = f"{user_id}-{record['activity']}-{custom_id}"
            else:
                task_name = f"{user_id}-{record['activity']}"
        reminder = Reminder(
            activity = record['activity'],
            channel_id = record['channel_id'],
            clan_name = record.get('clan_name', None),
            custom_id = record.get('custom_id', None),
            end_time = datetime.fromisoformat(record['end_time'], ),
            message = record['message'],
            reminder_type = reminder_type,
            task_name = task_name,
            triggered = bool(record['triggered']),
            user_id = record.get('user_id', None),
            record_exists = True,
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return reminder


# Read Data
async def get_user_reminder(user_id: int, activity: str, custom_id: Optional[int] = None) -> Reminder:
    """Gets all settings for a user reminder from a user id and an activity.

    Arguments
    ---------
    user_id: int
    activity: str
    custom_id: int - Only necessary if activity is "custom".

    Returns
    -------
    Reminder object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no reminder was found.
    LookupError if something goes wrong reading the dict.
    ValueError if activity is "custom" and custom_id is None.
    Also logs all errors to the database.
    """
    table = 'reminders_users'
    function_name = 'get_user_reminder'
    if activity == 'custom' and custom_id is None:
        raise ValueError('Activity "custom" given but custom_id is None.')
    sql = f'SELECT * FROM {table} WHERE user_id=? AND activity=?'
    if custom_id is not None: sql = f'{sql} AND custom_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, activity)) if custom_id is None else cur.execute(sql, (user_id, activity, custom_id))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(
            f'No reminder data found in database for user "{user_id}" and activity "{activity}".'
        )
    reminder = await _dict_to_reminder(dict(record))

    return reminder


async def get_clan_reminder(clan_name: str) -> Reminder:
    """Gets all settings for a clan reminder from a clan name and an activity.

    Returns
    -------
    Reminder object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_clans'
    function_name = 'get_clan_reminder'
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
        raise exceptions.NoDataFoundError(
            f'No reminder data found in database for clan "{clan_name}".'
        )
    reminder = await _dict_to_reminder(dict(record))

    return reminder


async def get_active_user_reminders(user_id: Optional[int] = None, activity: Optional[str] = None,
                                    end_time: Optional[datetime] = None) -> Tuple[Reminder]:
    """Gets all active reminders for all users or - if the argument user_id is set - for one user.

    Arguments
    ---------
    user_id: int - Limits reminders to this user if set.
    activity: str - Limits reminders to an activity that starts with this text.
    end_time: datetime - Sets the threshold. If set, only selects reminders > this time. If not set, uses current time.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no reminder was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_users'
    function_name = 'get_active_user_reminders'
    sql = f'SELECT * FROM {table} WHERE end_time>?'
    if end_time is None:
        current_time = datetime.utcnow().replace(microsecond=0)
        end_time_str = current_time.isoformat(sep=' ')
    else:
        end_time_str = end_time.isoformat(sep=' ')
    queries = [end_time_str,]
    if user_id is not None:
        sql = f'{sql} AND user_id=?'
        queries.append(user_id)
    if activity is not None:
        sql = f"{sql} AND activity LIKE ?"
        queries.append(f'{activity}%')
    sql = f'{sql} ORDER BY end_time'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, queries)
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No active user reminders found in database.'
        if user_id is not None: error_message = f'{error_message} User: {user_id}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


async def get_active_clan_reminders(clan_name: Optional[str] = None) -> Tuple[Reminder]:
    """Gets all active reminders for all clans or - if the argument clan_name is set - for one clan.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_clans'
    function_name = 'get_active_clan_reminders'
    if clan_name is None:
        sql = f'SELECT * FROM {table} WHERE end_time>? ORDER BY end_time'
    else:
        sql = f'SELECT * FROM {table} WHERE clan_name=? AND end_time>? ORDER BY end_time'
    try:
        cur = settings.NAVI_DB.cursor()
        current_time = datetime.utcnow().replace(microsecond=0)
        current_time_str = current_time.isoformat(sep=' ')
        cur.execute(sql, (current_time_str,)) if clan_name is None else cur.execute(sql, (clan_name, current_time_str))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No active clan reminders found in database.'
        if clan_name is not None: error_message = f'{error_message} Clan: {clan_name}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


async def get_due_user_reminders(user_id: Optional[int] = None) -> Tuple[Reminder]:
    """Gets all reminders for all users or - if the argument user_id is set - for one user that are due within
    the next 15 seconds.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_users'
    function_name = 'get_due_user_reminders'
    if user_id is None:
        sql = f'SELECT * FROM {table} WHERE triggered=? AND end_time BETWEEN ? AND ?'
    else:
        sql = f'SELECT * FROM {table} WHERE user_id=? AND triggered=? AND end_time BETWEEN ? AND ?'
    try:
        cur = settings.NAVI_DB.cursor()
        current_time = datetime.utcnow().replace(microsecond=0)
        end_time = current_time + timedelta(seconds=15)
        current_time_str = current_time.isoformat(sep=' ')
        end_time_str = end_time.isoformat(sep=' ')
        triggered = False
        if user_id is None:
            cur.execute(sql, (triggered, current_time_str, end_time_str))
        else:
            cur.execute(sql, (user_id, triggered, current_time_str, end_time_str))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No due user reminders found in database.'
        if user_id is not None: error_message = f'{error_message} User: {user_id}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


async def get_due_clan_reminders(clan_name: Optional[str] = None) -> Tuple[Reminder]:
    """Gets all reminders for all clans or - if the argument clan_name is set - for one clan that are due within
    the next 15 seconds.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_clans'
    function_name = 'get_due_clan_reminders'
    if clan_name is None:
        sql = f'SELECT * FROM {table} WHERE triggered=? AND end_time BETWEEN ? AND ?'
    else:
        sql = f'SELECT * FROM {table} WHERE clan_name=? AND triggered=? AND end_time BETWEEN ? AND ?'
    try:
        cur = settings.NAVI_DB.cursor()
        current_time = datetime.utcnow().replace(microsecond=0)
        end_time  = current_time + timedelta(seconds=15)
        current_time_str = current_time.isoformat(sep=' ')
        end_time_str = end_time.isoformat(sep=' ')
        triggered = False
        if clan_name is None:
            cur.execute(sql, (triggered, current_time_str, end_time_str))
        else:
            cur.execute(sql, (clan_name, triggered, current_time_str, end_time_str))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No due user reminders found in database.'
        if clan_name is not None: error_message = f'{error_message} Clan: {clan_name}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


async def get_old_user_reminders(user_id: Optional[int] = None) -> Tuple[Reminder]:
    """Gets all reminders for all users or - if the argument user_id is set - for one user that are have an end time
    more than 20 seconds in the past.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_users'
    function_name = 'get_old_user_reminders'
    if user_id is None:
        sql = f'SELECT * FROM {table} WHERE end_time < ?'
    else:
        sql = f'SELECT * FROM {table} WHERE user_id=? AND end_time < ?'
    try:
        cur = settings.NAVI_DB.cursor()
        current_time = datetime.utcnow().replace(microsecond=0)
        end_time  = current_time - timedelta(seconds=20)
        end_time_str = end_time.isoformat(sep=' ')
        cur.execute(sql, (end_time_str,)) if user_id is None else cur.execute(sql, (user_id, end_time_str))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No old user reminders found in database.'
        if user_id is not None: error_message = f'{error_message} User: {user_id}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


async def get_old_clan_reminders(clan_name: Optional[str] = None) -> Tuple[Reminder]:
    """Gets all reminders for all clans or - if the argument clan_name is set - for one clan that are have an end time
    more than 20 seconds in the past.

    Returns
    -------
    Tuple[Reminder]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'reminders_clans'
    function_name = 'get_old_clan_reminders'
    if clan_name is None:
        sql = f'SELECT * FROM {table} WHERE end_time < ?'
    else:
        sql = f'SELECT * FROM {table} WHERE clan_name=? AND end_time < ?'
    try:
        cur = settings.NAVI_DB.cursor()
        current_time = datetime.utcnow().replace(microsecond=0)
        end_time  = current_time - timedelta(seconds=20)
        end_time_str = end_time.isoformat(sep=' ')
        cur.execute(sql, (end_time_str,)) if clan_name is None else cur.execute(sql, (clan_name, end_time_str))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise

    if not records:
        error_message = 'No old user reminders found in database.'
        if clan_name is not None: error_message = f'{error_message} Clan: {clan_name}'
        raise exceptions.NoDataFoundError(error_message)
    reminders = []
    for record in records:
        reminder = await _dict_to_reminder(dict(record))
        reminders.append(reminder)

    return tuple(reminders)


# Write Data
async def _delete_reminder(reminder: Reminder) -> None:
    """Deletes reminder record. Use Reminder.delete() to trigger this function.
    Also cancels and deletes an active task for this reminder.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    function_name = '_delete_reminder'
    if reminder.reminder_type == 'user':
        table = 'reminders_users'
        sql = f'DELETE FROM {table} WHERE user_id=? AND activity=?'
    else:
        table = 'reminders_clans'
        sql = f'DELETE FROM {table} WHERE clan_name=? AND activity=?'
    if reminder.activity == 'custom': sql = f'{sql} AND custom_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        reminder_id = reminder.user_id if reminder.reminder_type == 'user' else reminder.clan_name
        if reminder.activity == 'custom':
            cur.execute(sql, (reminder_id, reminder.activity, reminder.custom_id))
        else:
            cur.execute(sql, (reminder_id, reminder.activity))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def _update_reminder(reminder: Reminder, **kwargs) -> None:
    """Updates reminder record. Use Reminder.update() to trigger this function.

    Arguments
    ---------
    reminder: Reminder
    kwargs (column=value):
        activity: str
        channel_id: int
        clan_name: str
        custom_id: int
        end_time: datetime UTC
        message: str
        reminder_type: str  # "clan" or "user"
        triggered: bool
        user_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'reminders_users' if reminder.reminder_type == 'user' else 'reminders_clans'
    function_name = '_update_reminder'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    current_time = datetime.utcnow().replace(microsecond=0)
    end_time = kwargs['end_time'] if 'end_time' in kwargs else reminder.end_time
    time_left = end_time - current_time
    triggered = False if time_left.total_seconds() > 15 else True
    if 'triggered' not in kwargs: kwargs['triggered'] = triggered
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['activity_old'] = reminder.activity
        sql = f'{sql} WHERE activity = :activity_old'
        if reminder.reminder_type == 'user':
            kwargs['user_id_old'] = reminder.user_id
            sql = f'{sql} AND user_id = :user_id_old'
        else:
            kwargs['clan_name_old'] = reminder.clan_name
            sql = f'{sql} AND clan_name = :clan_name_old'
        if reminder.activity == 'custom':
            kwargs['custom_id_old'] = reminder.custom_id
            sql = f'{sql} AND custom_id = :custom_id_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if triggered: scheduled_for_tasks[reminder.task_name] = reminder


async def insert_user_reminder(user_id: int, activity: str, time_left: timedelta,
                               channel_id: int, message: str, overwrite_message: Optional[bool] = True) -> Reminder:
    """Inserts a user reminder record.
    This function first checks if a reminder exists. If yes, the existing reminder will be updated instead and
    no new record is inserted.
    If end_time is less than 16 seconds in the future, this also creates a background task.

    Arguments
    ---------
    overwrite_message: bool - If a reminder exists, this controls if the message gets updated or not.

    Returns
    -------
    Reminder object with the newly created reminder.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_user_reminder'
    table = 'reminders_users'
    current_time = datetime.utcnow().replace(microsecond=0)
    end_time = current_time + time_left
    custom_id = None
    triggered = False if time_left.total_seconds() > 15 else True
    try:
        cur = settings.NAVI_DB.cursor()
        if activity == 'custom':
            sql = f'SELECT custom_id FROM {table} WHERE user_id = ? AND activity = ? ORDER BY custom_id ASC'
            cur.execute(sql, (user_id, 'custom',))
            record_custom_reminders = cur.fetchall()
            if not record_custom_reminders:
                custom_id = 1
            else:
                highest_custom_id = record_custom_reminders[-1]['custom_id']
                if highest_custom_id is None:
                    custom_id = 1
                else:
                    if highest_custom_id > len(record_custom_reminders):
                        reminder_count = 1
                        for record in record_custom_reminders:
                            if reminder_count == record['custom_id']:
                                custom_id = reminder_count = reminder_count + 1
                            else:
                                custom_id = reminder_count
                                break
                    else:
                        custom_id = highest_custom_id + 1

    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    reminder = None
    if activity != 'custom':
        try:
            reminder = await get_user_reminder(user_id, activity)
        except exceptions.NoDataFoundError:
            pass
    if reminder is not None:
        if overwrite_message:
            await reminder.update(end_time=end_time, channel_id=channel_id, message=message)
        else:
            await reminder.update(end_time=end_time, channel_id=channel_id)
    else:
        sql = (
            f'INSERT INTO {table} (user_id, activity, end_time, channel_id, message, custom_id, triggered) '
            f'VALUES (?, ?, ?, ?, ?, ?, ?)'
        )
        try:
            cur.execute(sql, (user_id, activity, end_time, channel_id, message, custom_id, triggered))
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
        reminder = await get_user_reminder(user_id, activity, custom_id)

    # Create background task if necessary
    if triggered:
        scheduled_for_tasks[reminder.task_name] = reminder
    else:
        scheduled_for_deletion[reminder.task_name] = reminder

    return reminder


async def insert_clan_reminder(clan_name: str, time_left: timedelta, channel_id: int, message: str) -> Reminder:
    """Inserts a clan reminder record.
    This function first checks if a reminder exists. If yes, the existing reminder will be updated instead and
    no new record is inserted.
    If end_time is less than 16 seconds in the future, this also creates a background task.

    Returns
    -------
    Reminder object with the newly created reminder.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_clan_reminder'
    table = 'reminders_clans'
    reminder = None
    try:
        reminder = await get_clan_reminder(clan_name)
    except exceptions.NoDataFoundError:
        pass
    current_time = datetime.utcnow().replace(microsecond=0)
    end_time = current_time + time_left
    triggered = False if time_left.total_seconds() > 15 else True
    if reminder is not None:
        await reminder.update(end_time=end_time, channel_id=channel_id, message=message, triggered=triggered)
    else:
        sql = (
            f'INSERT INTO {table} (clan_name, activity, end_time, channel_id, message, triggered) '
            f'VALUES (?, ?, ?, ?, ?, ?)'
        )
        try:
            cur = settings.NAVI_DB.cursor()
            cur.execute(sql, (clan_name, 'guild', end_time, channel_id, message, triggered))
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
        reminder = await get_clan_reminder(clan_name)
    # Create background task if necessary
    if triggered:
        scheduled_for_tasks[reminder.task_name] = reminder
    else:
        scheduled_for_deletion[reminder.task_name] = reminder
    return reminder


async def reduce_reminder_time(user_id: int, time_reduction: timedelta) -> None:
    """Reduces the end time of all user reminders affected by sleepy potions of one user by a certain amount.
    If the new end time is within the next 15 seconds, the reminder is immediately scheduled.
    If the new end time is in the past, the reminder is deleted."""
    current_time = datetime.utcnow().replace(microsecond=0)
    try:
        reminders = await get_active_user_reminders(user_id)
    except exceptions.NoDataFoundError:
        return
    current_time = datetime.utcnow()
    for reminder in reminders:
        if reminder.activity in strings.SLEEPY_POTION_AFFECTED_ACTIVITIES:
            new_end_time = reminder.end_time - time_reduction
            time_left = new_end_time - current_time
            if time_left.total_seconds() <= 0:
                scheduled_for_deletion[reminder.task_name] = reminder
                await reminder.delete()
            elif 1 <= time_left.total_seconds() <= 15:
                await reminder.update(end_time=new_end_time, triggered=True)
                scheduled_for_tasks[reminder.task_name] = reminder
            else:
                await reminder.update(end_time=new_end_time)