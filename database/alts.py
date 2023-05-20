# alts.py
"""Provides access to the table "alts" in the database"""


import sqlite3
from typing import Tuple

from database import errors
from resources import settings, strings


# Read data
async def get_alts(user_id: int) -> Tuple[int]:
    """Gets all alts of a user

    Returns
    -------
    Tuple with all alts or an empty tuple if no alts were found.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table = 'alts'
    function_name = 'get_alts'
    sql = f'SELECT user1_id, user2_id FROM {table} WHERE user1_id=? OR user2_id=? ORDER BY sort_index ASC'
    try:
        cur=settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, user_id))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
    alts = []
    for record in records:
        record = dict(record)
        alt = record['user1_id'] if int(record['user2_id']) == user_id else record['user2_id']
        alts.append(int(alt))
        
    return tuple(alts)


# Write data
async def insert_alt(user_id: int, alt_id: int) -> None:
    """Inserts a record in the table "alts". Does NOT check if user-alt combination exists, so check that beforehand.

    Raises
    ------
    sqlite3.Error if something happened within the database or the unique user-alt combination already exists.
    Also logs all errors to the database.
    """
    function_name = 'insert_alt'
    table = 'alts'
    sql = f'INSERT INTO {table} (user1_id, user2_id) VALUES (?, ?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, alt_id))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def delete_alt(user_id: int, alt_id: int) -> None:
    """Deletes alt record.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    table = 'alts'
    function_name = 'delete_alt'
    sql = f'DELETE FROM {table} WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, alt_id, alt_id, user_id))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise