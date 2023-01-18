# portals.py
"""Provides access to the tables "users_portals" in the database"""

from dataclasses import dataclass
import sqlite3
from typing import Tuple

from database import errors
from resources import exceptions, settings, strings


# Containers
@dataclass()
class Portal():
    """Object that represents a record from the table "users_portals"."""
    user_id: int
    channel_id: int

    async def delete(self) -> None:
        """Deletes the portal record from the database. Also calls refresh().

        Raises
        ------
        RecordExistsError if there was no error but the record was not deleted.
        Also logs all errors to the database.
        """
        await _delete_portal(self)
        await self.refresh()

    async def refresh(self) -> None:
        """Refreshes portal from the database."""
        try:
            new_portal = await get_portal(self.user_id, self.channel_id)
        except exceptions.NoDataFoundError as error:
            return
        self.user_id = new_portal.user_id
        self.channel_id = new_portal.channel_id

    async def update(self, **kwargs) -> None:
        """Updates the portal in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            channel_id: int
            user_id: int
        """
        await _update_portal(self, **kwargs)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_portal(record: dict) -> Portal:
    """Creates a Portal object from a database record

    Arguments
    ---------
    record: Database record from table "users_portals" as a dict.

    Returns
    -------
    Portal object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_portal'
    try:
        portal = Portal(
            channel_id = record['channel_id'],
            user_id = record['user_id'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return portal


# Read Data
async def get_portal(user_id: int, channel_id: int) -> Portal:
    """Gets a portal.

    Arguments
    ---------
    user_id: int
    channel_id: int

    Returns
    -------
    Portal object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no reminder was found.
    LookupError if something goes wrong reading the dict.
    ValueError if activity is "custom" and custom_id is None.
    Also logs all errors to the database.
    """
    table = 'users_portals'
    function_name = 'get_portal'
    sql = f'SELECT * FROM {table} WHERE user_id=? AND channel_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, channel_id))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(
            f'No portal found in database with user id "{user_id}" and channel id "{channel_id}".'
        )
    portal = await _dict_to_portal(dict(record))

    return portal


async def get_portals(user_id: int) -> Tuple[Portal]:
    """Gets all portals for a user.

    Arguments
    ---------
    user_id: int

    Returns
    -------
    Tuple[Portal]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no reminder was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'users_portals'
    function_name = 'get_portals'
    sql = f'SELECT * FROM {table} WHERE user_id=? ORDER BY sort_index ASC'
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
        raise exceptions.NoDataFoundError(f'No portals found in database with user id {user_id}.')
    user_portals = []
    for record in records:
        portal = await _dict_to_portal(dict(record))
        user_portals.append(portal)

    return tuple(user_portals)


# Write Data
async def _delete_portal(portal: Portal) -> None:
    """Deletes a portal record. Use Portal.delete() to trigger this function.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    function_name = '_delete_portal'
    table = 'users_portals'
    sql = f'DELETE FROM {table} WHERE user_id=? AND channel_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (portal.user_id, portal.channel_id))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def _update_portal(portal: Portal, **kwargs) -> None:
    """Updates portal record. Use Portal.update() to trigger this function.

    Arguments
    ---------
    portal: Portal
    kwargs (column=value):
        channel_id: int
        user_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'users_portals'
    function_name = '_update_portal'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    kwargs['user_id_old'] = portal.user_id
    kwargs['channel_id_old'] = portal.channel_id
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = f'{sql} WHERE user_id = :user_id_old AND channel_id = :channel_id_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_portal(user_id: int, channel_id: int) -> Portal:
    """Inserts a portal record.
    This function first checks if a portal exists. If yes, no new record is inserted.

    Arguments
    ---------
    user_id: int
    channel_id: int

    Returns
    -------
    Portal object with the newly created portal.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_portal'
    table = 'users_portals'
    cur = settings.NAVI_DB.cursor()
    sql = f'INSERT INTO {table} (user_id, channel_id) VALUES (?, ?)'
    try:
        cur.execute(sql, (user_id, channel_id))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    portal = await get_portal(user_id, channel_id)

    return portal