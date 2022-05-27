# settings.py
"""Provides access to the table "settings" in the database"""


from argparse import ArgumentError
import sqlite3

from database import errors
from resources import exceptions, settings, strings


# Read Data
async def get_settings() -> dict:
    """Returns all setting from table "settings".

    Returns:
       dict with all settings.

    Raises:
        sqlite3.Error if something goes wrong.
        NoDataFound if no data was found.
    """
    table = 'settings'
    function_name = 'get_settings'
    sql = f'SELECT * FROM {table}'
    try:
        cur=settings.NAVI_DB.cursor()
        cur.execute(sql)
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_DATA_FOUND.format(table=table, function=function_name, sql=sql)
        )
        raise exceptions.NoDataFoundError('No settings not found in database.')

    return dict(records)


# Write Data
async def update_setting(name: str, value: str) -> None:
    """Updates a setting record.

    Arguments
    ---------
    name: str
    value: str

    Raises
    ------
    sqlite3.Error if something happened within the database.
    ArgumentError if value is None
    Also logs all errors to the database.
    """
    table = 'settings'
    function_name = 'update_setting'
    if name is None or value is None:
        await errors.log_error(
            strings.INTERNAL_ERROR_INVALID_ARGUMENTS.format(
                value=f'value: {value}, name: {name}', argument='name / value', table=table, function=function_name
            )
        )
        raise ArgumentError('Arguments can\'t be None.')
    cur = settings.NAVI_DB.cursor()
    all_settings = await get_settings()
    setting = all_settings.get(name, 'No record')
    try:
        if setting == 'No record':
            sql = f'INSERT INTO {table} (name, value) VALUES (?, ?)'
            cur.execute(sql, (name, value))
        else:
            sql = f'UPDATE {table} SET value = ? WHERE name = ?'
            cur.execute(sql, (value, name))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise