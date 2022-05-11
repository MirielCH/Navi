# functions.py

from datetime import datetime, timedelta

import discord

from database import errors
from database import settings as settings_db
from resources import emojis, exceptions


# --- Misc ---
async def get_interaction(message: discord.Message) -> discord.User:
    """Returns the interaction object if the message was triggered by a slash command. Returns None if no user was found."""
    if message.reference is not None:
        if message.reference.cached_message is not None:
            message = message.reference.cached_message
        else:
            message = await message.channel.fetch_message(message.reference.message_id)
    return message.interaction

async def get_interaction_user(message: discord.Message) -> discord.User:
    """Returns the user object if the message was triggered by a slash command. Returns None if no user was found."""
    interaction = await get_interaction(message)
    return interaction.user if interaction is not None else None


# --- Parsing ---
async def check_timestring(string: str) -> str:
    """Checks if a string is a valid timestring. Returns itself it valid.

    Raises
    ------
    ErrorInvalidTime if timestring is not a valid timestring.
    """
    last_time_code = None
    last_char_was_number = False
    timestring = ''
    current_number = ''
    pos = 0
    while not pos == len(string):
        slice = string[pos:pos+1]
        pos = pos+1
        allowedcharacters_numbers = set('1234567890')
        allowedcharacters_timecode = set('wdhms')
        if set(slice).issubset(allowedcharacters_numbers):
            timestring = f'{timestring}{slice}'
            current_number = f'{current_number}{slice}'
            last_char_was_number = True
        elif set(slice).issubset(allowedcharacters_timecode) and last_char_was_number:
            if slice == 'w':
                if last_time_code is None:
                    timestring = f'{timestring}w'
                    try:
                        current_number_numeric = int(current_number)
                    except:
                        raise exceptions.InvalidTimestringError('Invalid timestring.')
                    last_time_code = 'weeks'
                    last_char_was_number = False
                    current_number = ''
                else:
                    raise exceptions.InvalidTimestringError('Invalid timestring.')
            elif slice == 'd':
                if last_time_code in ('weeks',None):
                    timestring = f'{timestring}d'
                    try:
                        current_number_numeric = int(current_number)
                    except:
                        raise exceptions.InvalidTimestringError('Invalid timestring.')
                    last_time_code = 'days'
                    last_char_was_number = False
                    current_number = ''
                else:
                    raise exceptions.InvalidTimestringError('Invalid timestring.')
            elif slice == 'h':
                if last_time_code in ('weeks','days',None):
                    timestring = f'{timestring}h'
                    try:
                        current_number_numeric = int(current_number)
                    except:
                        raise exceptions.InvalidTimestringError('Invalid timestring.')
                    last_time_code = 'hours'
                    last_char_was_number = False
                    current_number = ''
                else:
                    raise exceptions.InvalidTimestringError('Invalid timestring.')
            elif slice == 'm':
                if last_time_code in ('weeks','days','hours',None):
                    timestring = f'{timestring}m'
                    try:
                        current_number_numeric = int(current_number)
                    except:
                        raise exceptions.InvalidTimestringError('Invalid timestring.')
                    last_time_code = 'minutes'
                    last_char_was_number = False
                    current_number = ''
                else:
                    raise exceptions.InvalidTimestringError('Invalid timestring.')
            elif slice == 's':
                if last_time_code in ('weeks','days','hours','minutes',None):
                    timestring = f'{timestring}s'
                    try:
                        current_number_numeric = int(current_number)
                    except:
                        raise exceptions.InvalidTimestringError('Invalid timestring.')
                    last_time_code = 'seconds'
                    last_char_was_number = False
                    current_number = ''
                else:
                    raise exceptions.InvalidTimestringError('Invalid timestring.')
            else:
                raise exceptions.InvalidTimestringError('Invalid timestring.')
        else:
            raise exceptions.InvalidTimestringError('Invalid timestring.')
    if last_char_was_number:
        raise exceptions.InvalidTimestringError('Invalid timestring.')

    return timestring


async def parse_timestring_to_timedelta(timestring: str) -> timedelta:
    """Parses a time string and returns the time as timedelta."""
    time_left_seconds = 0

    if timestring.find('w') > -1:
        weeks_start = 0
        weeks_end = timestring.find('w')
        weeks = timestring[weeks_start:weeks_end]
        timestring = timestring[weeks_end+1:].strip()
        try:
            time_left_seconds = time_left_seconds + (int(weeks) * 604800)
        except:
            await errors.log_error(
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{weeks}\' to an integer'
            )
    if timestring.find('d') > -1:
        days_start = 0
        days_end = timestring.find('d')
        days = timestring[days_start:days_end]
        timestring = timestring[days_end+1:].strip()
        try:
            time_left_seconds = time_left_seconds + (int(days) * 86400)
        except:
            await errors.log_error(
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{days}\' to an integer'
            )
    if timestring.find('h') > -1:
        hours_start = 0
        hours_end = timestring.find('h')
        hours = timestring[hours_start:hours_end]
        timestring = timestring[hours_end+1:].strip()
        try:
            time_left_seconds = time_left_seconds + (int(hours) * 3600)
        except:
            await errors.log_error(
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{hours}\' to an integer'
            )
    if timestring.find('m') > -1:
        minutes_start = 0
        minutes_end = timestring.find('m')
        minutes = timestring[minutes_start:minutes_end]
        timestring = timestring[minutes_end+1:].strip()
        try:
            time_left_seconds = time_left_seconds + (int(minutes) * 60)
        except:
            await errors.log_error(
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{minutes}\' to an integer'
            )
    if timestring.find('s') > -1:
        seconds_start = 0
        seconds_end = timestring.find('s')
        seconds = timestring[seconds_start:seconds_end]
        timestring = timestring[seconds_end+1:].strip()
        try:
            time_left_seconds = time_left_seconds + int(seconds)
        except:
            await errors.log_error(
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{seconds}\' to an integer'
            )

    if time_left_seconds > 999_999_999:
        raise OverflowError('Timestring out of valid range. Stop hacking.')

    return timedelta(seconds=time_left_seconds)


async def parse_timedelta_to_timestring(time_left: timedelta) -> str:
    """Creates a time string from a timedelta."""
    weeks = time_left.total_seconds() // 604800
    weeks = int(weeks)
    days = (time_left.total_seconds() % 604800) // 86400
    days = int(days)
    hours = (time_left.total_seconds() % 86400) // 3600
    hours = int(hours)
    minutes = (time_left.total_seconds() % 3600) // 60
    minutes = int(minutes)
    seconds = time_left.total_seconds() % 60
    seconds = int(seconds)

    timestring = ''
    if not weeks == 0:
        timestring = f'{timestring}{weeks}w '
    if not days == 0:
        timestring = f'{timestring}{days}d '
    if not hours == 0:
        timestring = f'{timestring}{hours}h '
    timestring = f'{timestring}{minutes}m {seconds}s'

    return timestring


# --- Message processing ---
async def encode_text(text: str) -> str:
    """Encodes all unicode characters in a text in a way that is consistent on both Windows and Linux"""
    text = (
        text
        .encode('unicode-escape',errors='ignore')
        .decode('ASCII')
        .replace('\\','')
    )

    return text


def encode_text_non_async(text: str) -> str:
    """Encodes all unicode characters in a text in a way that is consistent on both Windows and Linux (non async)"""
    text = (
        text
        .encode('unicode-escape',errors='ignore')
        .decode('ASCII')
        .replace('\\','')
    )

    return text


async def encode_message(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters (async)"""
    if not bot_message.embeds:
        message = await encode_text(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_title = ''
        if embed.author: message_author = await encode_text(str(embed.author))
        if embed.description: message_description = await encode_text(str(embed.description))
        if embed.title: message_title = str(embed.title)
        if embed.fields: message_fields = str(embed.fields)
        message = f'{message_author}{message_description}{message_fields}{message_title}'

    return message


def encode_message_non_async(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters (non async)"""
    if not bot_message.embeds:
        message = encode_text_non_async(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_title = ''
        if embed.author: message_author = encode_text_non_async(str(embed.author))
        if embed.description: message_description = encode_text_non_async(str(embed.description))
        if embed.title: message_title = str(embed.title)
        if embed.fields: message_fields = str(embed.fields)
        message = f'{message_author}{message_description}{message_fields}{message_title}'

    return message


async def encode_message_clan(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters (async, clan)"""
    if not bot_message.embeds:
        message = await encode_text(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_footer = message_title = ''
        if embed.author: message_author = await encode_text(str(embed.author))
        if embed.description: message_description = await encode_text(str(embed.description))
        if embed.title: message_title = await encode_text(str(embed.title))
        if embed.footer: message_footer = await encode_text(str(embed.footer))
        if embed.fields: message_fields = str(embed.fields)
        message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'

    return message


async def encode_message_with_fields(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters
    (async, fields encoded)"""
    if not bot_message.embeds:
        message = await encode_text(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_title = ''
        if embed.author: message_author = await encode_text(str(embed.author))
        if embed.description: message_description = await encode_text(str(embed.description))
        if embed.title: message_title = str(embed.title)
        if embed.fields: message_fields = await encode_text(str(embed.fields))
        message = f'{message_author}{message_description}{message_fields}{message_title}'

    return message


def encode_message_clan_non_async(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters
    (non async, clan)"""
    if not bot_message.embeds:
        message = encode_text_non_async(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_footer = message_title = ''
        if embed.author: message_author = encode_text_non_async(str(embed.author))
        if embed.description: message_description = encode_text_non_async(str(embed.description))
        if embed.title: message_title = encode_text_non_async(str(embed.title))
        if embed.footer: message_footer = encode_text_non_async(str(embed.footer))
        if embed.fields: message_fields = str(embed.fields)
        message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'

    return message


def encode_message_with_fields_non_async(bot_message: discord.Message) -> str:
    """Encodes a message to a version that converts all potentionally problematic unicode characters
    (non async, fields encoded)"""
    if not bot_message.embeds:
        message = encode_text_non_async(bot_message.content)
    else:
        embed: discord.Embed = bot_message.embeds[0]
        message_author = message_description = message_fields = message_title = ''
        if embed.author: message_author = encode_text_non_async(str(embed.author))
        if embed.description: message_description = encode_text_non_async(str(embed.description))
        if embed.title: message_title = str(embed.title)
        if embed.fields: message_fields = encode_text_non_async(str(embed.fields))
        message = f'{message_author}{message_description}{message_fields}{message_title}'

    return message


async def get_training_answer(message_content: str) -> str:
    """Returns the answer to a training question based on the message content."""
    answer = None
    if 'river!' in message_content:
        if '<:epicfish' in message_content:
            answer = '`3` / `EPIC fish`'
        elif '<:goldenfish' in message_content:
            answer = '`2` / `golden fish`'
        elif '<:normiefish' in message_content:
            answer = '`1` / `normie fish`'
    elif 'field!' in message_content:
        if '<:apple' in message_content:
            if '**first**' in message_content:
                answer = '`A`'
            elif '**second**' in message_content:
                answer = '`P`'
            elif '**third**' in message_content:
                answer = '`P`'
            elif '**fourth**' in message_content:
                answer = '`L`'
            elif '**fifth**' in message_content:
                answer = '`E`'
        elif '<:banana' in message_content:
            if '**first**' in message_content:
                answer = '`B`'
            elif '**second**' in message_content:
                answer = '`A`'
            elif '**third**' in message_content:
                answer = '`N`'
            elif '**fourth**' in message_content:
                answer = '`A`'
            elif '**fifth**' in message_content:
                answer = '`N`'
            elif '**sixth**' in message_content:
                answer = '`A`'
    elif 'casino?' in message_content:
        if ':gem:' in message_content and '**diamond**' in message_content:
            answer = '`YES`'
        elif ':gift:' in message_content and '**gift**' in message_content:
            answer = '`YES`'
        elif ':game_die:' in message_content and '**dice**' in message_content:
            answer = '`YES`'
        elif ':coin:' in message_content and '**coin**' in message_content:
            answer = '`YES`'
        elif ':four_leaf_clover:' in message_content and '**four leaf clover**' in message_content:
            answer = '`YES`'
        else:
            answer = '`NO`'
    elif 'forest!' in message_content:
        if 'many <:wooden' in message_content:
            emoji = '<:wooden'
        elif 'many <:epic' in message_content:
            emoji = '<:epic'
        elif 'many <:super' in message_content:
            emoji = '<:super'
        elif 'many <:mega' in message_content:
            emoji = '<:mega'
        elif 'many <:hyper' in message_content:
            emoji = '<:hyper'
        start_question = message_content.find('how many ')
        message_content_list = message_content[0:start_question]
        answer = f'`{message_content_list.count(emoji)}`'
    elif 'void' in message_content:
        all_settings = await settings_db.get_settings()
        answer = ''
        a16_seal_time = all_settings.get('a16_seal_time', None)
        a17_seal_time = all_settings.get('a17_seal_time', None)
        a18_seal_time = all_settings.get('a18_seal_time', None)
        a19_seal_time = all_settings.get('a19_seal_time', None)
        a20_seal_time = all_settings.get('a20_seal_time', None)
        seal_times = [a16_seal_time, a17_seal_time, a18_seal_time, a19_seal_time, a20_seal_time]
        current_time = datetime.utcnow().replace(microsecond=0)
        for area_no, seal_time in enumerate(seal_times, 16):
            if seal_time is not None:
                seal_time = datetime.fromisoformat(seal_time, )
                if seal_time > current_time:
                    time_left = seal_time - current_time
                    answer = f'{answer}\nArea {area_no} will close in {time_left.days} days.'.strip()
        if answer == '':
            answer = (
                f'No idea, lol.\n'
                f'Please use {emojis.EPIC_RPG_LOGO_SMALL}`/void areas` before your next training.'
            )

    return answer