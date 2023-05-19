# bot.py

from datetime import datetime
import sqlite3
import sys
import traceback

import discord
from discord.ext import commands

from database import errors, guilds
from database import settings as settings_db
from database.update_database import NAVI_DB_VERSION
from resources import functions, settings


#Check if database is up to date
try:
    cur = settings.NAVI_DB.cursor()
    cur.execute('PRAGMA user_version')
    record = cur.fetchone()
    db_version = int(dict(record)['user_version'])
    if db_version != NAVI_DB_VERSION:
        print(
            'Your database structure is outdated. Please run "database/update_database.py" first.'
        )
        sys.exit()
except sqlite3.Error as error:
    print(
        f'Got an error while trying to determine database version: {error}'
    )
    sys.exit()


startup_time = datetime.isoformat(datetime.utcnow().replace(microsecond=0), sep=' ')
functions.await_coroutine(settings_db.update_setting('startup_time', startup_time))

intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection
intents.members = True  # To be able to look up user info
intents.message_content = True # for command detection

allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)


if settings.DEBUG_MODE:
    bot = commands.AutoShardedBot(command_prefix=guilds.get_all_prefixes, help_command=None,
                                  case_insensitive=True, intents=intents, owner_id=settings.OWNER_ID,
                                  allowed_mentions=allowed_mentions, debug_guilds=settings.DEV_GUILDS)
else:
    bot = commands.AutoShardedBot(command_prefix=guilds.get_all_prefixes, help_command=None,
                                  case_insensitive=True, intents=intents, allowed_mentions=allowed_mentions,
                                  owner_id=settings.OWNER_ID)


@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    """Runs when an error outside a command appears.
    All errors get written to the database for further review.
    """
    if event == 'on_message':
        message, = args
        if message.channel.type.name == 'private': return
        embed = discord.Embed(title='An error occured')
        error = sys.exc_info()
        if isinstance(error, discord.errors.Forbidden): return
        traceback_str = "".join(traceback.format_tb(error[2]))
        traceback_message = f'{error[1]}\n{traceback_str}'
        embed.add_field(name='Event', value=f'`{event}`', inline=False)
        embed.add_field(name='Error', value=f'```py\n{traceback_message[:1015]}```', inline=False)
        await errors.log_error(f'- Event: {event}\n- Error: {error[1]}\n- Traceback:\n{traceback_str}', message)
        if settings.DEBUG_MODE: await message.channel.send(embed=embed)
    else:
        try:
            message, = args
        except:
            return
        embed = discord.Embed(title='An error occured')
        error = sys.exc_info()
        if isinstance(error, discord.errors.Forbidden): return
        traceback_str = "".join(traceback.format_tb(error[2]))
        traceback_message = f'{error[1]}\n{traceback_str}'
        embed.add_field(name='Error', value=f'```py\n{traceback_message[:1015]}```', inline=False)
        await errors.log_error(f'- Event: {event}\n- Error: {error[1]}\n- Traceback:\n{traceback_str}', message)
        if settings.DEBUG_MODE: await message.channel.send(embed=embed)
        if event == 'on_reaction_add':
            reaction, user = args
            return
        elif event == 'on_command_error':
            ctx, error = args
            raise
        else:
            return


EXTENSIONS = [
        'cogs.adventure',
        'cogs.arena',
        'cogs.ascension',
        'cogs.auto_flex',
        'cogs.boosts',
        'cogs.cooldowns',
        'cogs.cache',
        'cogs.clan',
        'cogs.current_area',
        'cogs.daily',
        'cogs.dev',
        'cogs.duel',
        'cogs.dungeon_miniboss',
        'cogs.epic_items',
        'cogs.events',
        'cogs.farm',
        'cogs.fun',
        #'cogs.halloween',
        'cogs.helper_context',
        'cogs.helper_farm',
        'cogs.helper_heal',
        'cogs.helper_pets',
        'cogs.helper_ruby',
        'cogs.helper_training',
        'cogs.horse',
        'cogs.horse_race',
        'cogs.hunt',
        'cogs.leaderboards',
        'cogs.lootbox',
        'cogs.lottery',
        'cogs.main',
        'cogs.nsmb_bigarena',
        'cogs.pets_tournament',
        'cogs.pets',
        'cogs.portals',
        'cogs.quest',
        'cogs.reminders_custom',
        'cogs.reminders_lists',
        'cogs.settings',
        'cogs.settings_guild',
        'cogs.slashboard',
        'cogs.sleepy_potion',
        'cogs.tasks',
        'cogs.time_cookie',
        'cogs.tracking',
        'cogs.training',
        'cogs.vote',
        'cogs.weekly',
        'cogs.work',
        'cogs.xmas',
        'cogs.dev_old',
    ]

if settings.COMPLAINT_CHANNEL_ID is not None and settings.SUGGESTION_CHANNEL_ID is not None:
    EXTENSIONS += ['cogs.feedback',]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)


bot.run(settings.TOKEN)