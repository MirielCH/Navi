# alts.py
"""Provides access to the table "alts" in the database"""


import sqlite3

from database import errors
from resources import functions, settings, strings


# Read data
async def get_alts(user_id: int) -> tuple[int, ...]:
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
    sql = f'SELECT user1_id_hash, user2_id_hash FROM {table} WHERE user1_id_hash=? OR user2_id_hash=? ORDER BY sort_index ASC'
    try:
        cur=settings.NAVI_DB.cursor()
        cur.execute(sql, (functions.create_hash(user_id), functions.create_hash(user_id)))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
    alts = []
    for record in records:
        record = dict(record)
        try:
            user1_id = user2_id = None
            sql = f'SELECT user_id_token FROM users WHERE user_id_hash=?'
            cur = settings.NAVI_DB.cursor()
            cur.execute(sql, (record['user2_id_hash'],))
            user2_id = int(functions.decrypt(dict(cur.fetchone())['user_id_token'])) # pyright: ignore
            if user_id == user2_id:
                sql = f'SELECT user_id_token FROM users WHERE user_id_hash=?'
                cur = settings.NAVI_DB.cursor()
                cur.execute(sql, (record['user1_id_hash'],))
                user1_id = int(functions.decrypt(dict(cur.fetchone())['user_id_token'])) # pyright: ignore
        except Exception as error:
            sql = f'DELETE FROM {table} WHERE (user1_id_hash=? AND user2_id_hash=?) OR (user1_id_hash=? AND user2_id_hash=?)'
            try:
                cur = settings.NAVI_DB.cursor()
                cur.execute(sql, (record['user1_id_hash'], record['user2_id_hash'],
                                  record['user2_id_hash'], record['user1_id_hash']))
            except sqlite3.Error as error:
                await errors.log_error(
                    strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
                )
                raise
        alt = int(user1_id) if int(user2_id) == user_id else int(user2_id) # pyright: ignore
        alts.append(alt)
        
    return tuple(alts)


# Write data
async def insert_alt(user_id: int, alt_id: int) -> None:
    """Inserts a record in the table "alts". Does NOT check if user-alt combination exists, so check that beforehand.
up
    Raises
    ------
    sqlite3.Error if something happened within the database or the unique user-alt combination already exists.
    Also logs all errors to the database.
    """
    function_name = 'insert_alt'
    table = 'alts'
    sql = f'INSERT INTO {table} (user1_id_hash, user2_id_hash) VALUES (?, ?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (functions.create_hash(user_id), functions.create_hash(alt_id)))
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
    sql = f'DELETE FROM {table} WHERE (user1_id_hash=? AND user2_id_hash=?) OR (user1_id_hash=? AND user2_id_hash=?)'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (functions.create_hash(user_id), functions.create_hash(alt_id),
                          functions.create_hash(alt_id), functions.create_hash(user_id)))
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise