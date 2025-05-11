# cooldowns.py
"""Provides access to the table "cooldowns" in the database"""


from dataclasses import dataclass
from math import ceil
import sqlite3

from database import errors
from resources import exceptions, settings, strings


# Containers
@dataclass()
class Cooldown():
    """Object that represents record from table "cooldowns"."""
    activity: str
    base_cooldown: int
    donor_affected: bool
    event_reduction_mention: float
    event_reduction_slash: float

    def actual_cooldown_mention(self) -> int:
        """Returns the actual mention cooldown, factoring in the event_reduction"""
        return ceil(self.base_cooldown * ((100 - self.event_reduction_mention) / 100))

    def actual_cooldown_slash(self) -> int:
        """Returns the actual slash cooldown, factoring in the event_reduction"""
        return ceil(self.base_cooldown * ((100 - self.event_reduction_slash) / 100))

    async def refresh(self) -> None:
        """Refreshes cooldown data from the database."""
        new_settings = await get_cooldown(self.activity)
        self.base_cooldown = new_settings.base_cooldown
        self.donor_affected = new_settings.donor_affected
        self.event_reduction_mention = new_settings.event_reduction_mention
        self.event_reduction_slash = new_settings.event_reduction_slash

    async def update(self, **updated_settings) -> None:
        """Updates the cooldown record in the database. Also calls refresh().

        Arguments
        ---------
        updated_settings (column=value):
            base_cooldown: int
            donor_affected: bool
            event_reduction_mention: float
            event_reduction_slash: float
        """
        await _update_cooldown(self.activity, **updated_settings)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_cooldown(record: dict) -> Cooldown:
    """Creates a Cooldown object from a database record

    Arguments
    ---------
    record: Database record from table "cooldowns" as a dict.

    Returns
    -------
    Cooldown object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_cooldown'
    try:
        cooldown = Cooldown(
            activity = record['activity'],
            base_cooldown = record['cooldown'],
            donor_affected = bool(record['donor_affected']),
            event_reduction_mention = record['event_reduction_mention'],
            event_reduction_slash = record['event_reduction_slash'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return cooldown


# Read Data
async def get_cooldown(activity: str) -> Cooldown:
    """Gets the cooldown settings for an activity.

    Returns
    -------
    Cooldown object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    Also logs all errors to the database.
    """
    table = 'cooldowns'
    function_name = 'get_cooldown'
    sql = f'SELECT * FROM {table} WHERE activity=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (activity,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_DATA_FOUND.format(table=table, function=function_name, sql=sql)
        )
        raise exceptions.NoDataFoundError(f'No cooldown data found in database for activity "{activity}".')
    cooldown = await _dict_to_cooldown(dict(record))

    return cooldown


async def get_all_cooldowns() -> tuple[Cooldown, ...]:
    """Gets the cooldown settings for all activities.

    Returns
    -------
    Tuple[Cooldown, ...]

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no cooldown was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = f'cooldowns'
    function_name = 'get_all_cooldowns'
    sql = f'SELECT * FROM {table} ORDER BY activity ASC'
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
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_DATA_FOUND.format(table=table, function=function_name, sql=sql)
        )
        raise exceptions.NoDataFoundError('No cooldown data found in database.')
    cooldowns = []
    for record in records:
        cooldown = await _dict_to_cooldown(dict(record))
        cooldowns.append(cooldown)

    return tuple(cooldowns)


# Write Data
async def _update_cooldown(activity: str, **updated_settings) -> None:
    """Updates cooldown record. Use Cooldown.update() to trigger this function.

    Arguments
    ---------
    activity: str
    updated_settings (column=value):
        cooldown: int
        donor_affected: bool
        event_reduction_mention: float
        event_reduction_slash: float

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no updated_settings are passed (need to pass at least one).
    Also logs all errors to the database.
    """
    table = 'cooldowns'
    function_name = '_update_cooldown'
    if not updated_settings:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for updated_setting in updated_settings:
            sql = f'{sql} {updated_setting} = :{updated_setting},'
        sql = sql.strip(",")
        updated_settings['activity'] = activity
        sql = f'{sql} WHERE activity = :activity'
        cur.execute(sql, updated_settings)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise