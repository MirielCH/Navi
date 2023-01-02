# functions.py

from argparse import ArgumentError
from datetime import datetime, timedelta
import re
from typing import List, Optional, Union

import discord
from discord.ext import commands
from discord.utils import MISSING

from database import cooldowns, errors, reminders, users
from database import settings as settings_db
from resources import emojis, exceptions, settings, strings


# --- Get discord data ---
async def get_interaction(message: discord.Message) -> discord.Interaction:
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


async def get_message_from_channel_history(channel: discord.channel, regex: Union[str, re.Pattern] = None,
                                           limit: int  = 50,
                                           user: Optional[discord.User] = None, user_name: Optional[str] = None,
                                           no_prefix: Optional[bool] = False) -> discord.Message:
    """Looks through the last 50 messages in the channel history. If a message that matches regex is found, it returns
    both the message and the matched string. If user is defined, only messages from that user are returned.

    Arguments
    ---------
    channel: Channel to look through.
    regex: String with the regex the content has to match. If no regex is defined, the first message with the given user
    or user name is returned.
    limit: Amount of messages to check in the history. Defaults to 50.
    user: User object the message author has to match.
    user_name: User name the message author has to match. If user is also defined, this is ignored.
    If both user and user_name are None, this function returns the first message that matches the regex is not from a bot.
    no_prefix: Set to True if the message you want to pick up does not include the rpg prefix or the bot mention

    Returns
    -------
    Tuple with the found message and the matched string. Returns (None, None) if no message was found.
    Note: The returned string always combines multiple spaces into one.

    Raises
    ------
    ArgumentError if regex, user AND user_name are None.
    """
    if regex is None and user is None and user_name is None:
        raise ArgumentError('At least one of these arguments has to be defined: regex, user, user_name.')
    message_history = await channel.history(limit=limit).flatten()
    for message in message_history:
        if message.content is not None:
            if message.author.bot: continue
            correct_mention = False
            if (not no_prefix and not message.content.lower().startswith('rpg ')
                and not message.content.lower().startswith('testy ')):
                if not message.mentions: continue
                for mentioned_user in message.mentions:
                    if mentioned_user.id == settings.EPIC_RPG_ID:
                        correct_mention = True
                        break
                if not correct_mention: continue
            if (not no_prefix and not message.content.lower().startswith('rpg ')
                and not message.content.lower().startswith('testy ') and not correct_mention):
                    continue
            if user is not None and message.author != user: continue
            if user_name is not None and await encode_text(user_name) != await encode_text(message.author.name): continue
            if regex is None:
                return message
            else:
                message_content = re.sub(rf'<@!?{settings.EPIC_RPG_ID}>', '', message.content.lower())
                match = re.search(regex, message_content)
                if match: return message
    return None


async def get_discord_user(bot: discord.Bot, user_id: int) -> discord.User:
    """Checks the user cache for a user and makes an additional API call if not found. Returns None if user not found."""
    await bot.wait_until_ready()
    user = bot.get_user(user_id)
    if user is None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            pass
    return user


async def get_discord_channel(bot: discord.Bot, channel_id: int) -> discord.User:
    """Checks the channel cache for a channel and makes an additional API call if not found. Returns None if channel not found."""
    if channel_id is None: return None
    await bot.wait_until_ready()
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            pass
        except discord.Forbidden:
            raise
    return channel


# --- Reactions
async def add_reminder_reaction(message: discord.Message, reminder: reminders.Reminder,  user_settings: users.User) -> None:
    """Adds a Navi reaction if the reminder was created, otherwise add a warning and send the error if debug mode is on"""
    if reminder.record_exists:
        if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
    else:
        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
            await message.add_reaction(emojis.WARNING)
            await message.channel.send(strings.MSG_ERROR)


async def add_warning_reaction(message: discord.Message) -> None:
    """Adds a warning reaction if debug mode is on or the guild is a dev guild"""
    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
        await message.add_reaction(emojis.WARNING)


# --- Regex ---
async def get_match_from_patterns(patterns: List[str], string: str) -> re.Match:
    """Searches a string for a regex patterns out of a list of patterns and returns the first match.
    Returns None if no match is found.
    """
    for pattern in patterns:
        match = re.search(pattern, string, re.IGNORECASE)
        if match: break
    return match


# --- Time calculations ---
async def get_guild_member_by_name(guild: discord.Guild, user_name: str) -> List[discord.Member]:
    """Returns all guild members found by the given name"""
    members = []
    for member in guild.members:
        if await encode_text(member.name) == await encode_text(user_name) and not member.bot:
            try:
                await users.get_user(member.id)
            except exceptions.FirstTimeUserError:
                continue
            members.append(member)
    return members


async def calculate_time_left_from_cooldown(message: discord.Message, user_settings: users.User, activity: str) -> timedelta:
    """Returns the time left for a reminder based on a cooldown."""
    slash_command = True if message.interaction is not None else False
    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
    bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
    current_time = datetime.utcnow().replace(microsecond=0)
    time_elapsed = current_time - bot_answer_time
    user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
    actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
    if cooldown.donor_affected:
        time_left_seconds = (actual_cooldown
                             * settings.DONOR_COOLDOWNS[user_donor_tier]
                             - time_elapsed.total_seconds())
    else:
        time_left_seconds = actual_cooldown - time_elapsed.total_seconds()
    if activity in strings.XMAS_AREA_AFFECTED_ACTIVITIES and user_settings.christmas_area_enabled:
        time_left_seconds *= 0.9
    alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
    return timedelta(seconds=time_left_seconds * alert_settings.multiplier)


async def calculate_time_left_from_timestring(message: discord.Message, timestring: str) -> timedelta:
    """Returns the time left for a reminder based on a timestring."""
    time_left = await parse_timestring_to_timedelta(timestring.lower())
    bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
    current_time = datetime.utcnow().replace(microsecond=0)
    time_elapsed = current_time - bot_answer_time
    return time_left - time_elapsed


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
        .strip('*')
    )

    return text


def encode_text_non_async(text: str) -> str:
    """Encodes all unicode characters in a text in a way that is consistent on both Windows and Linux (non async)"""
    text = (
        text
        .encode('unicode-escape',errors='ignore')
        .decode('ASCII')
        .replace('\\','')
        .strip('*')
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


# Helper functions
async def get_training_answer_buttons(message: discord.Message) -> str:
    """Returns the buttons for the TrainingAnswerView to a slash training question based on the message content."""
    buttons = {}
    message_content = message.content.lower()
    search_strings_river = [
        'river!', #English
        'río!', #Spanish
        'rio!', #Portuguese
    ]
    search_strings_field = [
        'field!', #English
        'campo!', #Spanish, Portuguese
    ]
    search_strings_casino = [
        'casino?', #English & Spanish
        'cassino?', #Portuguese
    ]
    search_strings_forest = [
        'forest!', #English
        'bosque!', #Spanish, Portuguese
    ]
    if any(search_string in message_content for search_string in search_strings_river):
        if '<:normiefish' in message_content:
            correct_button = 'training_1'
        elif '<:goldenfish' in message_content:
            correct_button = 'training_2'
        elif '<:epicfish' in message_content:
            correct_button = 'training_3'
    elif any(search_string in message_content for search_string in search_strings_field):
        search_strings_first = [
            '**first**', #English
            '**primera**', #Spanish
            '**primeira**', #Portuguese
        ]
        search_strings_second = [
            '**second**', #English
            '**segunda**', #Spanish, Portuguese
        ]
        search_strings_third = [
            '**third**', #English
            '**tercera**', #Spanish
            '**terceira**', #Portuguese
        ]
        search_strings_fourth = [
            '**fourth**', #English
            '**cuarta**', #Spanish
            '**quarta**', #Portuguese
        ]
        search_strings_fifth = [
            '**fifth**', #English
            '**quinta**', #Spanish, Portuguese
        ]
        search_strings_sixth = [
            '**sixth**', #English
            '**sexta**', #Spanish, Portuguese
        ]
        banana = 'banana'
        apple = 'apple'
        if any(search_string in message_content for search_string in search_strings_first):
            letter = 1
        elif any(search_string in message_content for search_string in search_strings_second):
            letter = 2
        elif any(search_string in message_content for search_string in search_strings_third):
            letter = 3
        elif any(search_string in message_content for search_string in search_strings_fourth):
            letter = 4
        elif any(search_string in message_content for search_string in search_strings_fifth):
            letter = 5
        elif any(search_string in message_content for search_string in search_strings_sixth):
            letter = 6
        if '<:apple' in message_content:
            correct_button = f'training_{apple[letter-1]}'
        elif '<:banana' in message_content:
            correct_button = f'training_{banana[letter-1]}'
    elif any(search_string in message_content for search_string in search_strings_casino):
        search_strings_diamond = [
            '**diamond**',  #English
            '**diamante**',  #Spanish, Portuguese
        ]
        search_strings_gift = [
            '**gift**',  #English
            '**regalo**',  #Spanish
            '**presente**',  #Portuguese
        ]
        search_strings_dice = [
            '**dice**',  #English
            '**dado**',  #Spanish, Portuguese
        ]
        search_strings_coin = [
            '**coin**',  #English
            '**moneda**',  #Spanish, UNCONFIRMED
            '**moeda**',  #Portuguese, UNCONFIRMED
        ]
        search_strings_clover = [
            '**four leaf clover**',  #English
            '**trébol de cuatro hojas**',  #Spanish
            '**trevo de quatro folhas**',  #Portuguese
        ]
        if (':gem:' in message_content
            and any(search_string in message_content for search_string in search_strings_diamond)):
            correct_button = 'training_yes'
        elif (':gift:' in message_content
              and any(search_string in message_content for search_string in search_strings_gift)):
            correct_button = 'training_yes'
        elif (':game_die:' in message_content
              and any(search_string in message_content for search_string in search_strings_dice)):
            correct_button = 'training_yes'
        elif (':coin:' in message_content
              and any(search_string in message_content for search_string in search_strings_coin)):
            correct_button = 'training_yes'
        elif (':four_leaf_clover:' in message_content
              and any(search_string in message_content for search_string in search_strings_clover)):
            correct_button = 'training_yes'
        else:
            correct_button = 'training_no'
    elif any(search_string in message_content for search_string in search_strings_forest):
        search_patterns = [
            r'many (.+?) do', #English
            r'cuantos (.+?) ves', #Spanish
            r'quantas (.+?) você', #Portuguese
        ]
        emoji_match = await get_match_from_patterns(search_patterns, message_content)
        try:
            emoji = emoji_match.group(1)
        except:
            await errors.log_error(f'Log emoji not found in training answer function: {message_content}')
            return
        search_strings = [
            'how many ', #English
            'cuantos ', #Spanish
            'quantas ', #Portuguese
        ]
        for search_string in search_strings:
            start_question = message_content.find(search_string)
            if start_question != -1: break
        message_content_list = message_content[0:start_question]
        emoji_amount = message_content_list.count(emoji)
        correct_button = f'training_{emoji_amount}'

    for row, action_row in enumerate(message.components, start=1):
        buttons[row] = {}
        for button in action_row.children:
            if button.custom_id == correct_button:
                buttons[row][button.custom_id] = (button.label, button.emoji, True)
            else:
                buttons[row][button.custom_id] = (button.label, button.emoji, False)
    return buttons


async def get_training_answer_text(message: discord.Message) -> str:
    """Returns the answer to a training question based on the message content."""
    message_content = message.content.lower()
    answer = None
    search_strings_river = [
        'river!', #English
        'río!', #Spanish
        'rio!', #Portuguese
    ]
    search_strings_field = [
        'field!', #English
        'campo!', #Spanish, Portuguese
    ]
    search_strings_casino = [
        'casino?', #English & Spanish
        'cassino?', #Portuguese
    ]
    search_strings_forest = [
        'forest!', #English
        'bosque!', #Spanish, Portuguese
    ]
    search_strings_void = [
        'void', #English
        'vacío', #Spanish, UNCONFIRMED
        'vazio', #Portuguese, UNCONFIRMED
    ]
    if any(search_string in message_content for search_string in search_strings_river):
        if '<:epicfish' in message_content:
            answer = '`EPIC fish` (`3`)'
        elif '<:goldenfish' in message_content:
            answer = '`golden fish` (`2`)'
        elif '<:normiefish' in message_content:
            answer = '`normie fish` (`1`)'
    elif any(search_string in message_content for search_string in search_strings_field):
        search_strings_first = [
            '**first**', #English
            '**primera**', #Spanish
            '**primeira**', #Portuguese
        ]
        search_strings_second = [
            '**second**', #English
            '**segunda**', #Spanish, Portuguese
        ]
        search_strings_third = [
            '**third**', #English
            '**tercera**', #Spanish
            '**terceira**', #Portuguese
        ]
        search_strings_fourth = [
            '**fourth**', #English
            '**cuarta**', #Spanish
            '**quarta**', #Portuguese
        ]
        search_strings_fifth = [
            '**fifth**', #English
            '**quinta**', #Spanish, Portuguese
        ]
        search_strings_sixth = [
            '**sixth**', #English
            '**sexta**', #Spanish, Portuguese
        ]
        banana = 'BANANA'
        apple = 'APPLE'
        if any(search_string in message_content for search_string in search_strings_first):
            letter = 1
        elif any(search_string in message_content for search_string in search_strings_second):
            letter = 2
        elif any(search_string in message_content for search_string in search_strings_third):
            letter = 3
        elif any(search_string in message_content for search_string in search_strings_fourth):
            letter = 4
        elif any(search_string in message_content for search_string in search_strings_fifth):
            letter = 5
        elif any(search_string in message_content for search_string in search_strings_sixth):
            letter = 6
        if '<:apple' in message_content:
            return f'`{apple[letter-1]}`'
        elif '<:banana' in message_content:
            return f'`{banana[letter-1]}`'
    elif any(search_string in message_content for search_string in search_strings_casino):
        search_strings_diamond = [
            '**diamond**',  #English
            '**diamante**',  #Spanish, Portuguese
        ]
        search_strings_gift = [
            '**gift**',  #English
            '**regalo**',  #Spanish
            '**presente**',  #Portuguese
        ]
        search_strings_dice = [
            '**dice**',  #English
            '**dado**',  #Spanish, Portuguese
        ]
        search_strings_coin = [
            '**coin**',  #English
            '**moneda**',  #Spanish, UNCONFIRMED
            '**moeda**',  #Portuguese, UNCONFIRMED
        ]
        search_strings_clover = [
            '**four leaf clover**',  #English
            '**trébol de cuatro hojas**',  #Spanish
            '**trevo de quatro folhas**',  #Portuguese
        ]
        if (':gem:' in message_content
            and any(search_string in message_content for search_string in search_strings_diamond)):
            answer = '`YES`'
        elif (':gift:' in message_content
              and any(search_string in message_content for search_string in search_strings_gift)):
            answer = '`YES`'
        elif (':game_die:' in message_content
              and any(search_string in message_content for search_string in search_strings_dice)):
            answer = '`YES`'
        elif (':coin:' in message_content
              and any(search_string in message_content for search_string in search_strings_coin)):
            answer = '`YES`'
        elif (':four_leaf_clover:' in message_content
              and any(search_string in message_content for search_string in search_strings_clover)):
            answer = '`YES`'
        else:
            answer = '`NO`'
    elif any(search_string in message_content for search_string in search_strings_forest):
        search_patterns = [
            r'many (.+?) do', #English
            r'cuantos (.+?) ves', #Spanish
            r'quantas (.+?) você', #Portuguese
        ]
        emoji_match = await get_match_from_patterns(search_patterns, message_content)
        try:
            emoji = emoji_match.group(1)
        except:
            await errors.log_error(f'Log emoji not found in training answer function: {message_content}')
            return
        search_strings = [
            'how many ', #English
            'cuantos ', #Spanish
            'quantas ', #Portuguese
        ]
        for search_string in search_strings:
            start_question = message_content.find(search_string)
            if start_question != -1: break
        message_content_list = message_content[0:start_question]
        answer = f'`{message_content_list.count(emoji)}`'

    return answer


async def get_void_training_answer_buttons(message: discord.Message, user_settings: users.User) -> str:
    """Returns the answer to a void training question."""
    all_settings = await settings_db.get_settings()
    answer = ''
    current_time = datetime.utcnow().replace(microsecond=0)
    a16_seal_time = all_settings.get('a16_seal_time', None)
    a17_seal_time = all_settings.get('a17_seal_time', None)
    a18_seal_time = all_settings.get('a18_seal_time', None)
    a19_seal_time = all_settings.get('a19_seal_time', None)
    a20_seal_time = all_settings.get('a20_seal_time', None)
    seal_times = [a16_seal_time, a17_seal_time, a18_seal_time, a19_seal_time, a20_seal_time]
    seal_times_days = []
    for seal_time in seal_times:
        if seal_time is not None:
            seal_time = datetime.fromisoformat(seal_time, )
            time_left = seal_time - current_time
            if seal_time > current_time:
                seal_times_days.append(str(time_left.days))
    matches = []
    for row, action_row in enumerate(message.components, start=1):
        for button in action_row.children:
            if button.label in seal_times_days:
                matches.append(button.label)
    buttons = {}
    if len(matches) == 1:
        for row, action_row in enumerate(message.components, start=1):
            buttons[row] = {}
            for button in action_row.children:
                if button.label == matches[0]:
                    buttons[row][button.custom_id] = (button.label, button.emoji, True)
                else:
                    buttons[row][button.custom_id] = (button.label, button.emoji, False)
    for area_no, days in enumerate(seal_times_days, 16):
            answer = f'{answer}\n{emojis.BP}Area **{area_no}** will close in **{days}** days.'.strip()
    if answer == '':
        command_void_areas = await get_slash_command(user_settings, 'void areas')
        answer = (
            f'No idea, lol.\n'
            f'Please use {command_void_areas} before your next training.'
        )

    return (answer, buttons)


async def get_void_training_answer_text(message: discord.Message, user_settings: users.User) -> str:
    """Returns the answer to a void training question."""
    all_settings = await settings_db.get_settings()
    answer = ''
    current_time = datetime.utcnow().replace(microsecond=0)
    a16_seal_time = all_settings.get('a16_seal_time', None)
    a17_seal_time = all_settings.get('a17_seal_time', None)
    a18_seal_time = all_settings.get('a18_seal_time', None)
    a19_seal_time = all_settings.get('a19_seal_time', None)
    a20_seal_time = all_settings.get('a20_seal_time', None)
    seal_times = [a16_seal_time, a17_seal_time, a18_seal_time, a19_seal_time, a20_seal_time]
    seal_times_days = []
    for seal_time in seal_times:
        if seal_time is not None:
            seal_time = datetime.fromisoformat(seal_time, )
            time_left = seal_time - current_time
            if seal_time > current_time:
                seal_times_days.append(str(time_left.days))
    matches = []
    for row, action_row in enumerate(message.components, start=1):
        for button in action_row.children:
            if button.label in seal_times_days:
                matches.append(button.label)
    if len(matches) == 1: answer = f'`{matches[0]}`'
    if answer == '':
        for area_no, days in enumerate(seal_times_days, 16):
            answer = f'{answer}\n{emojis.BP}Area **{area_no}** will close in **{days}** days.'.strip()
    if answer == '':
        command_void_areas = await get_slash_command(user_settings, 'void areas')
        answer = (
            f'No idea, lol.\n'
            f'Please use {command_void_areas} before your next training.'
        )
    return answer


async def get_megarace_answer(message: discord.Message, slash_command: bool = False) -> str:
    """Returns the answer to a megarace question based on the message content."""
    embed = message.embeds[0]
    field_name = answer = None
    for field in embed.fields:
        if '/3' in field.name:
            field_name = field.name
            break
    if field_name is None: return None
    event_answers = {
        'ancient racer': ('C', 'C'),
        'annoying racer': ('B', 'C'),
        'asteroid': ('A', 'C'),
        'black hole': ('C', 'A'),
        'bottleneck': ('C', 'C'),
        'cliff': ('B', 'B'),
        'cooldown': ('A', 'A'),
        'dinosaur': ('C', 'C'),
        'epic dealer': ('C', 'A'),
        'epic guards': ('A', 'B'),
        'epic horse trainer': ('A', 'A'),
        'epic npc': ('C', 'C'),
        'giant life potion': ('C', 'C'),
        'horseless racer': ('B', 'B'),
        'hot air balloons': ('B', 'B'),
        'injured racers': ('C', 'C'),
        'racer ^ -1': ('A', 'C'),
        'legendary boss': ('A', 'C'),
        'many horses': ('B', 'B'),
        'mountains': ('C', 'C'),
        'mysterious racer': ('A', 'A'),
        'nothing': ('A', 'A'),
        'party': ('B', 'A'),
        'plane': ('A', 'B'),
        'quicksand': ('C', 'C'),
        'rainy': ('A', 'A'),
        'sandstorm': ('B', 'B'),
        'snowy': ('C', 'C'),
        'suspicious horse': ('B', 'B'),
        'sus': ('B', 'A'),
        'sleepy': ('A', 'B'),
        'team': ('B', 'A'),
        'waterfall': ('A', 'B'),
        'world border': ('A', 'A'),
        'zombie horde': ('B', 'B'),
    }

    for event, answers in event_answers.items():
        if event in field_name.lower():
            answer_safe, answer_lucky = answers
            answer = f'`{answer_safe}`'
            if answer_safe != answer_lucky:
                answer = (
                    f'{answer} (`{answer_lucky}` for gamblers with a {emojis.HORSE_ARMOR} horse armor)'
                )
    return answer


# Miscellaneous
async def call_ready_command(bot: commands.Bot, message: discord.Message, user: discord.User) -> None:
    """Calls the ready command as a reply to the current message"""
    command = bot.get_application_command(name='ready')
    if command is not None: await command.callback(command.cog, message, user=user)


async def get_slash_command(user_settings: users.User, command_name: str, include_prefix: Optional[bool] = True) -> None:
    """Gets a slash command string or mention depending on user setting"""
    if user_settings.slash_mentions_enabled:
        return strings.SLASH_COMMANDS.get(command_name, None)
    else:
        command = strings.RPG_COMMANDS.get(command_name, None)
        if command is None: return None
        return f'`{command}`' if include_prefix else f'`{command.replace("rpg ", "")}`'


async def get_navi_slash_command(bot: discord.Bot, command_name: str) -> None:
    """Gets a slash command from Navi. If found, returns the slash mention. If not found, just returns /command.
    Note that slash mentions only work with GLOBAL commands."""
    main_command, *sub_commands = command_name.lower().split(' ')
    for command in bot.application_commands:
        if command.name == main_command:
            return f'</{command_name}:{command.id}>'
    return f'`/{command_name}`'


async def get_area(mob_name: str) -> None:
    """Gets the area from a mob name"""
    for area, monsters in strings.MONSTERS_AREA.items():
        monsters = [monster.lower() for monster in monsters]
        if mob_name.lower() in monsters:
            return area
    return None


def await_coroutine(coro):
    """Function to call a coroutine outside of an async function"""
    while True:
        try:
            coro.send(None)
        except StopIteration as error:
            return error.value


async def edit_interaction(interaction: Union[discord.Interaction, discord.WebhookMessage], **kwargs) -> None:
    """Edits a reponse. The response can either be an interaction OR a WebhookMessage"""
    content = kwargs.get('content', MISSING)
    embed = kwargs.get('embed', MISSING)
    embeds = kwargs.get('embeds', MISSING)
    view = kwargs.get('view', MISSING)
    file = kwargs.get('file', MISSING)
    if isinstance(interaction, discord.WebhookMessage):
        await interaction.edit(content=content, embed=embed, embeds=embeds, view=view)
    else:
        await interaction.edit_original_response(content=content, file=file, embed=embed, embeds=embeds, view=view)


async def bool_to_text(boolean: bool) -> str:
        return f'{emojis.GREENTICK}`Enabled`' if boolean else f'{emojis.REDTICK}`Disabled`'


async def reply_or_respond(ctx: Union[discord.ApplicationContext, commands.Context], answer: str,
                           ephemeral: Optional[bool] = False) -> Union[discord.Message, discord.Integration]:
    """Sends a reply or reponse, depending on the context type"""
    if isinstance(ctx, commands.Context):
        return await ctx.reply(answer)
    else:
        return await ctx.respond(answer, ephemeral=ephemeral)