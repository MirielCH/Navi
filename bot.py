# bot.py

from datetime import datetime
import sqlite3
import sys
import traceback

import discord
from discord import utils
from discord.ext import bridge

from database import errors, guilds, update_database
from database import settings as settings_db
from resources import functions, logs, settings


intents: discord.Intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection
intents.members = True  # to be able to look up user info
intents.message_content = True # for command detection

allowed_mentions: discord.AllowedMentions = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)
member_cache_flags = discord.MemberCacheFlags(joined=True, voice=False, interaction=False)
bot_activity: discord.Activity = discord.Activity(type=discord.ActivityType.watching, name='your commands')

if settings.DEBUG_MODE:
    bot: bridge.AutoShardedBot = bridge.AutoShardedBot(command_prefix=guilds.get_all_prefixes, help_command=None,
                                                       case_insensitive=True, intents=intents, owner_id=settings.OWNER_ID,
                                                       allowed_mentions=allowed_mentions, debug_guilds=settings.DEV_GUILDS,
                                                       activity=bot_activity, member_cache_flags=member_cache_flags)
else:
    bot: bridge.AutoShardedBot = bridge.AutoShardedBot(command_prefix=guilds.get_all_prefixes, help_command=None,
                                                       case_insensitive=True, intents=intents, allowed_mentions=allowed_mentions,
                                                       owner_id=settings.OWNER_ID, activity=bot_activity,
                                                       member_cache_flags=member_cache_flags)


@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    """Runs when an error outside a command appears.
    All errors get written to the database for further review.
    """
    message: discord.Message
    embed: discord.Embed
    if event == 'on_message':
        message, = args
        if message.channel.type.name == 'private': return
        embed = discord.Embed(title='An error occured')
        error: sys._OptExcInfo = sys.exc_info()
        if isinstance(error[1], discord.errors.Forbidden): return
        traceback_str: str = "".join(traceback.format_tb(error[2]))
        traceback_message: str = f'{error[1]}\n{traceback_str}'
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
        error: sys._OptExcInfo = sys.exc_info()
        if isinstance(error[1], discord.errors.Forbidden): return
        traceback_str: str = "".join(traceback.format_tb(error[2]))
        traceback_message: str = f'{error[1]}\n{traceback_str}'
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


EXTENSIONS: list[str] = [
        'cogs.adventure',
        'cogs.arena',
        'cogs.artifacts',
        'cogs.ascension',
        'cogs.auto_flex',
        'cogs.boosts',
        'cogs.cards',
        'cogs.celebration',
        'cogs.cooldowns',
        'cogs.cache',
        'cogs.clan',
        'cogs.current_area',
        'cogs.daily',
        'cogs.dev',
        'cogs.duel',
        'cogs.dungeon_miniboss',
        'cogs.epic_items',
        'cogs.epic_shop',
        'cogs.event_pings',
        'cogs.events',
        'cogs.farm',
        'cogs.fun',
        'cogs.halloween',
        'cogs.helper_context',
        'cogs.helper_farm',
        'cogs.helper_heal',
        'cogs.helper_pets',
        'cogs.helper_ruby',
        'cogs.helper_training',
        'cogs.horse',
        'cogs.horse_festival',
        'cogs.horse_race',
        'cogs.hunt',
        'cogs.leaderboards',
        'cogs.lootbox',
        'cogs.lottery',
        'cogs.main',
        'cogs.maintenance',
        'cogs.misc',
        'cogs.nsmb_bigarena',
        'cogs.patreon',
        'cogs.pets_tournament',
        'cogs.pets',
        'cogs.portals',
        'cogs.profile',
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
        'cogs.trade',
        'cogs.training',
        'cogs.valentine',
        'cogs.vote',
        'cogs.weekly',
        'cogs.work',
        'cogs.xmas',
]

if settings.COMPLAINT_CHANNEL_ID and settings.SUGGESTION_CHANNEL_ID:
    EXTENSIONS += ['cogs.feedback',]

if __name__ == '__main__':

    # Check if python version is new enough
    python_version: float = float(f'{sys.version_info.major}.{sys.version_info.minor}')
    if python_version < settings.PYTHON_VERSION:
        error_message: str = (
            f'Navi requires Python {settings.PYTHON_VERSION} or higher to run.\n'
            f'Your current version is {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}.'
        )
        print(error_message)
        logs.logger.error(error_message)
        sys.exit()

    # Check if database is up to date
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        db_version: int = update_database.get_user_version()
        if db_version != settings.NAVI_DB_VERSION:
            logs.logger.info('Database: Database structure is outdated. Running update...')
            correct_version: bool = update_database.update_database()
            if not correct_version:
                db_version: int = update_database.get_user_version()
                error_message: str = f'Database: Database version mismatch after update, should be {settings.NAVI_DB_VERSION}, '
                f'is {db_version}. Exiting. Please check the database manually.'
                logs.logger.error(error_message)
                print(error_message)
                sys.exit()
            logs.logger.info('Database: Database updated.')
    except sqlite3.Error as error:
        error_message: str = f'Database: Got an error while trying to determine database version and/or updating the database: {error}'
        print(error_message)
        logs.logger.error(error_message)
        sys.exit()

    # Write startup time to database
    startup_time: datetime = datetime.isoformat(utils.utcnow(), sep=' ')
    functions.await_coroutine(settings_db.update_setting('startup_time', startup_time))

    # Load cogs
    for extension in EXTENSIONS:
        bot.load_extension(extension)

    # Run bot
    bot.run(settings.TOKEN)