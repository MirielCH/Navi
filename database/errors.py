# cooldowns.py
"""Provides access to the table "cooldowns" in the database"""

from datetime import datetime
import sqlite3
from typing import Optional, Union

from discord.ext import commands

from resources import exceptions, logs, settings, strings


async def log_error(error: Union[Exception, str], ctx: Optional[commands.Context] = None) -> None:
    """Logs an error to the database and the logfile

    Arguments
    ---------
    error: Exception or a simple string.
    ctx: If context is available, the function will log the user input, the message timestamp
    and the user settings. If not, current time is used, settings and input are logged as "N/A".

    Raises
    ------
    sqlite3.Error when something goes wrong in the database. Also logs this error to the log file.
    """
    table = 'errors'
    function_name = 'log_error'
    sql = f'INSERT INTO {table} (date_time, user_input, error, user_settings) VALUES (?, ?, ?, ?)'
    if isinstance(ctx, commands.Context):
        date_time = ctx.message.created_at
        user_input = ctx.message.content
        try:
            from database import users
            user: users.User = await users.get_user(ctx.author.id)
            user_settings = str(user)
        except exceptions.FirstTimeUserError:
            user_settings = 'N/A'
    else:
        date_time = datetime.utcnow()
        user_input = 'N/A'
        user_settings = 'N/A'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (date_time, user_input, str(error), user_settings))
        logs.logger.error(
            f'Time: {date_time}. User input: {user_input}. Error: {error}. User settings: {user_settings}'
        )
    except sqlite3.Error as error:
        if ctx is not None:
            logs.logger.error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql),
                ctx
            )
        else:
            logs.logger.error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
        raise