# pets.py
"""Provides access to the table "pets" in the database"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from typing import Optional

from database import errors
from resources import exceptions, functions, settings, strings


# Containers
@dataclass()
class Pet():
    """Object that represents a record from the table "pets"."""
    last_update: datetime
    pet_id: int
    pet_id_str: str
    pet_tier: int
    pet_type: str
    skill_clever: int
    skill_digger: int
    skill_epic: int
    skill_fast: int
    skill_faster: int
    skill_happy: int
    skill_lucky: int
    skill_tt: int
    user_id: int

    async def refresh(self) -> None:
        """Refreshes pets data from the database.
        If the record doesn't exist anymore, "record_exists" will be set to False.
        All other values will stay on their old values before deletion (!).
        """
        try:
            new_pet = await get_pet(self.user_id, self.pet_id)
        except exceptions.NoDataFoundError as error:
            return
        self.last_update = new_pet.last_update
        self.pet_id = new_pet.pet_id
        self.pet_id_str = new_pet.pet_id_str
        self.pet_tier = new_pet.pet_tier
        self.pet_type = new_pet.pet_type
        self.skill_clever = new_pet.skill_clever
        self.skill_digger = new_pet.skill_digger
        self.skill_epic = new_pet.skill_epic
        self.skill_fast = new_pet.skill_fast
        self.skill_faster = new_pet.skill_faster
        self.skill_happy = new_pet.skill_happy
        self.skill_lucky = new_pet.skill_lucky
        self.skill_tt = new_pet.skill_tt
        self.user_id = new_pet.user_id

    def get_reminder_time(self) -> timedelta:
        """Returns the time the pet spends on an adventure, based on its fast(er) skill"""
        reminder_time = timedelta(hours=4)
        fast_reduction = None
        if self.skill_fast > 0:
            fast_reduction = timedelta(seconds=576) * self.skill_fast
            if self.skill_fast > 0:
                fast_reduction *= 2
        if fast_reduction is not None:
            reminder_time += fast_reduction
        return reminder_time

    async def update(self, **kwargs) -> None:
        """Updates the clan record in the database. Also calls refresh().

        Arguments
        ---------
        kwargs (column=value):
            last_update: datetime
            pet_id: int
            pet_tier: int
            pet_type: str
            skill_clever: int
            skill_digger: int
            skill_epic: int
            skill_fast: int
            skill_faster: int
            skill_happy: int
            skill_lucky: int
            skill_tt: int
            user_id: int
        """
        await _update_pet(self, **kwargs)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_pets(record: dict) -> Pet:
    """Creates a pets object from a database record

    Arguments
    ---------
    record: Database record from table "pets" as a dict.

    Returns
    -------
    Pet object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name = '_dict_to_pets'
    try:
        pet = Pet(
            last_update = datetime.fromisoformat(record['last_update']),
            pet_id = record['pet_id'],
            pet_id_str = await functions.convert_pet_id_to_str(record['pet_id']),
            pet_tier = record['pet_tier'],
            pet_type = record['pet_type'],
            skill_clever = record['skill_clever'],
            skill_digger = record['skill_digger'],
            skill_epic = record['skill_epic'],
            skill_fast = record['skill_fast'],
            skill_faster = record['skill_faster'],
            skill_happy = record['skill_happy'],
            skill_lucky = record['skill_lucky'],
            skill_tt = record['skill_tt'],
            user_id = record['user_id'],
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return pet


# Read Data
async def get_pet(user_id: int, pet_id: int) -> Pet:
    """Gets a specific pets of a user.

    Arguments
    ---------
    user_id: int
    pet_id: int

    Returns
    -------
    Pet object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no data was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'pets'
    function_name = 'get_pet'
    sql = f'SELECT * FROM {table} WHERE user_id=? AND pet_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id, pet_id))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.NoDataFoundError(
            f'No pets found in database for user "{user_id}".'
        )
    pet = await _dict_to_pets(dict(record))
    return pet


async def get_pets(user_id: int, page: Optional[int] = None, **kwargs) -> Pet:
    """Gets pets of a user. To return all pets of a user, omit all kwargs.

    Arguments
    ---------
    user_id: int
    page: Optional[int] - limits pets looked up to one page
    kwargs (column=value):
        last_update: datetime
        pet_id: int
        pet_tier: int
        pet_type: int
        skill_clever: int
        skill_digger: int
        skill_epic: int
        skill_fast: int
        skill_faster: int
        skill_happy: int
        skill_lucky: int
        skill_tt: int
        user_id: int

    Returns
    -------
    List with Pet objects

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no data was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table = 'pets'
    function_name = 'get_pets'
    kwargs['user_id'] = user_id
    sql = f'SELECT * FROM {table} WHERE user_id = :user_id'
    if page is not None:
        sql = f'{sql} AND pet_id > {(page-1)*6} and pet_id <= {page*6}'
    for kwarg in kwargs:
        sql = f'{sql} AND {kwarg} = :{kwarg}'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, kwargs)
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        raise exceptions.NoDataFoundError(
            f'No pets found in database with the following arguments: {kwargs}.'
        )
    pets = []
    for record in records:
        pet = await _dict_to_pets(dict(record))
        pets.append(pet)

    return pets


# Write Data
async def _update_pet(pet: Pet, **kwargs) -> None:
    """Updates pets record. Use Pet.update() to trigger this function.

    Arguments
    ---------
    pet: Pet object
    kwargs (column=value):
        last_update: datetime
        pet_id: int
        pet_tier: int
        pet_type: int
        skill_clever: int
        skill_digger: int
        skill_epic: int
        skill_fast: int
        skill_faster: int
        skill_happy: int
        skill_lucky: int
        skill_tt: int
        user_id: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'pets'
    function_name = '_update_pet'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    current_time = datetime.utcnow().replace(microsecond=0)
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['last_update'] = current_time.isoformat(sep=' ')
        kwargs['user_id_old'] = pet.user_id
        sql = f'{sql} AND user_id = :user_id_old'
        cur.execute(sql, kwargs)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_pet(user_id: int, pet_id: int, tier: int, skill_clever: Optional[int] = 0, skill_digger: Optional[int] = 0,
                     skill_epic: Optional[int] = 0, skill_fast: Optional[int] = 0, skill_faster: Optional[int] = 0,
                     skill_happy: Optional[int] = 0, skill_lucky: Optional[int] = 0, skill_tt: Optional[int] = 0) -> Pet:
    """Inserts a pet record.
    This function first checks if a pet record exists. If yes, no new record is inserted.

    Arguments
    ---------
    user_id: int

    Returns
    -------
    Pet object with the existing or newly created record for the user.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name = 'insert_pet'
    table = 'pets'
    cur = settings.NAVI_DB.cursor()
    try:
        pet = await get_pet(user_id, pet_id)
    except exceptions.NoDataFoundError:
        pets_data = None
    if pets_data is None:
        current_time = datetime.utcnow().replace(microsecond=0)
        sql = (
            f'INSERT INTO {table} (user_id, last_update, pet_id, pet_tier, pet_type, skill_clever, skill_digger, '
            f'skill_epic, skill_fast, skill_faster, skill_happy, skill_lucky, skill_tt) '
            f'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )
        try:
            cur.execute(
                sql,
                (
                    user_id, current_time.isoformat(sep=' '), pet_id, skill_clever, skill_digger, skill_epic,
                    skill_fast, skill_faster, skill_happy, skill_lucky, skill_tt, tier
                )
            )
        except sqlite3.Error as error:
            await errors.log_error(
                strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
            )
            raise
        pet = await get_pet(user_id, pet_id)

    return pet