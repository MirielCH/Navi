# custom-reminders.py

import re
from typing import Union

import discord
from discord.ext import commands
from humanfriendly import format_timespan

from database import reminders, users
from resources import emojis, exceptions, functions, strings


# --- Commands ---
async def command_custom_reminder(ctx: Union[discord.ApplicationContext, commands.Context],
                                  timestring: str, message: str) -> None:
    """Add custom reminder"""
    user_settings: users.User = await users.get_user(ctx.author.id) # Only to stop if user is not registered
    timestring_guide = (
        f'Supported time codes are `w`, `d`, `h`, `m`, `s`\n\n'
        f'Examples:\n'
        f'{emojis.BP} `1h30m15s`\n'
        f'{emojis.BP} `1w 4d`\n'
        f'{emojis.BP} `40m`\n'
        f'{emojis.BP} `31650s`\n'
    )
    try:
        timestring = await functions.check_timestring(timestring.replace(' ', ''))
    except exceptions.InvalidTimestringError as error:
        await functions.reply_or_respond(ctx, f'{error}\n{timestring_guide}', True)
        return
    try:
        time_left = await functions.parse_timestring_to_timedelta(timestring)
    except OverflowError as error:
        await ctx.reply(error)
        return
    if time_left.total_seconds() > 31_536_000:
        await functions.reply_or_respond(
            ctx,
            (
                'The maximum time is one year.\n'
                'Which means you just tried to make a reminder that is longer.\n'
                'You DO feel at least a bit silly, right?\n'
            ),
            True
        )
        return
    user_id_match = re.search(r'<@!?[0-9]+>', message)
    if user_id_match:
        await functions.reply_or_respond(ctx, 'Nice try.', True)
        return
    reminder: reminders.Reminder = (
        await reminders.insert_user_reminder(ctx.author.id, 'custom', time_left,
                                             ctx.channel.id, message)
    )
    if reminder.record_exists:
        if isinstance(ctx, commands.Context):
            await functions.add_reminder_reaction(ctx.message, reminder, user_settings)
        else:
            await ctx.respond(f'Done. I will remind you in {format_timespan(time_left)} for **{message}**.')