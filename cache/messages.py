# messages.py
"""Contains the message cache and access to it. Cache is populated by cogs.cache."""

import asyncio
from argparse import ArgumentError
from datetime import datetime, timedelta
import re
from typing import Optional, Union

import discord

from resources import functions, logs, settings


_MESSAGE_CACHE = {}


async def find_message(channel_id: int, regex: Union[str, re.Pattern] = None,
                      user: Optional[discord.User] = None, user_name: Optional[str] = None) -> discord.Message:
    """Looks through the last 50 messages in the channel history. If a message that matches regex is found, it returns
    the message. If user and/or user_name are defined, only messages from that user are returned.

    Arguments
    ---------
    channel_id: ID of the Channel to look in.
    regex: String with the regex the content has to match. If no regex is defined, the first message with the given user
    or user name is returned.
    user: User object the message author has to match.
    user_name: User name the message author has to match. If user is also defined, this is ignored.
    If both user and user_name are None, this function returns the first message that matches the regex is not from a bot.

    Returns
    -------
    The found message. Returns None if no matching message was found.

    Raises
    ------
    ArgumentError if regex, user AND user_name are None.
    """
    attempts = 1
    while attempts <= 2:
        if regex is None and user is None and user_name is None:
            raise ArgumentError('At least one of these arguments has to be defined: regex, user, user_name.')
        channel_messages = _MESSAGE_CACHE.get(channel_id, None)
        if channel_messages is None: return None
        for message in channel_messages:
            if user is not None and message.author != user: continue
            if (user_name is not None
                and await functions.encode_text(user_name) != await functions.encode_text(message.author.name)):
                continue
            if regex is None:
                return message
            else:
                message_content = re.sub(rf'<@!?{settings.EPIC_RPG_ID}>', '', message.content.lower())
                match = re.search(regex, message_content)
                if match: return message
        await asyncio.sleep(0.5)
        logs.logger.info('Required a second attempt for getting a message from the message cache.')
        attempts += 1
    return None


async def store_message(message: discord.Message) -> discord.Message:
    """Adds a message to the message cache.
    Also keeps the maximum amount of messages stored per channel at 50."""
    channel_message_list = _MESSAGE_CACHE.get(message.channel.id, None)
    if channel_message_list is None:
        channel_message_list = [message,]
    else:
        channel_message_list.insert(0, message)
    if len(channel_message_list) > 50:
        channel_message_list = channel_message_list[:50]
    _MESSAGE_CACHE[message.channel.id] = channel_message_list


async def delete_old_messages(timespan: timedelta) -> int:
    """Deletes messages older than the specified timeframe.

    Returns
    -------
    Amount of messages deleted: int
    """
    current_time = datetime.utcnow()
    message_count = 0
    for channel_id, channel_messages in _MESSAGE_CACHE.items():
        for message in channel_messages:
            if message.created_at.replace(tzinfo=None) < (current_time - timespan):
                _MESSAGE_CACHE[channel_id].remove(message)
                message_count += 1
    if message_count > 0:
        for key in list(_MESSAGE_CACHE.keys()):
            if not _MESSAGE_CACHE[key]: del _MESSAGE_CACHE[key]
    return message_count