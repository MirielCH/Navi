# global_data.py

from datetime import timedelta
import discord
from discord.ext import commands

from database import errors


# --- Parsing ---
async def parse_timestring_to_timedelta(ctx: commands.Context, timestring: str) -> timedelta:
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
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{weeks}\' to an integer',
                ctx
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
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{days}\' to an integer',
                ctx
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
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{hours}\' to an integer',
                ctx
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
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{minutes}\' to an integer',
                ctx
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
                f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{seconds}\' to an integer',
                ctx
            )

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


def get_training_answer(message_content: str) -> str:
    """Returns the answer to a training question based on the message content."""
    answer = None
    if 'river!' in message_content:
        if '<:epicfish' in message_content:
            answer = '3'
        elif '<:goldenfish' in message_content:
            answer = '2'
        elif '<:normiefish' in message_content:
            answer = '1'
    elif 'field!' in message_content:
        if '<:apple' in message_content:
            if '**first**' in message_content:
                answer = 'A'
            elif '**second**' in message_content:
                answer = 'P'
            elif '**third**' in message_content:
                answer = 'P'
            elif '**fourth**' in message_content:
                answer = 'L'
            elif '**fifth**' in message_content:
                answer = 'E'
        elif '<:banana' in message_content:
            if '**first**' in message_content:
                answer = 'B'
            elif '**second**' in message_content:
                answer = 'A'
            elif '**third**' in message_content:
                answer = 'N'
            elif '**fourth**' in message_content:
                answer = 'A'
            elif '**fifth**' in message_content:
                answer = 'N'
            elif '**sixth**' in message_content:
                answer = 'A'
    elif 'casino?' in message_content:
        if ':gem:' in message_content and '**diamond**' in message_content:
            answer = 'YES'
        elif ':gift:' in message_content and '**gift**' in message_content:
            answer = 'YES'
        elif ':game_die:' in message_content and '**dice**' in message_content:
            answer = 'YES'
        elif ':coin:' in message_content and '**coin**' in message_content:
            answer = 'YES'
        elif ':four_leaf_clover:' in message_content and '**four leaf clover**' in message_content:
            answer = 'YES'
        else:
            answer = 'NO'
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
        answer = message_content_list.count(emoji)

    return answer