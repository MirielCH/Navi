# bot.py

from datetime import datetime
import sys
import traceback

import discord
from discord.ext import commands

from database import errors, guilds
from database import settings as settings_db
from resources import functions, logs, settings


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
    if not settings.DEBUG_MODE: return
    if event == 'on_message':
        message, = args
        if message.channel.type.name == 'private': return
        embed = discord.Embed(title='An error occured')
        error = sys.exc_info()
        traceback_str = "".join(traceback.format_tb(error[2]))
        traceback_message = f'{error[1]}\n{traceback_str}'
        print(traceback_message)
        logs.logger.error(traceback_message)
        embed.add_field(name='Event', value=f'`{event}`', inline=False)
        embed.add_field(name='Error', value=f'```py\n{traceback_message[:1015]}```', inline=False)
        await errors.log_error(f'Got an error in event {event}:\nError: {error[1]}\nTraceback: {traceback_str}')
        await message.channel.send(embed=embed)
    else:
        try:
            message, = args
        except:
            return
        embed = discord.Embed(title='An error occured')
        error = sys.exc_info()
        traceback_str = "".join(traceback.format_tb(error[2]))
        traceback_message = f'{error[1]}\n{traceback_str}'
        print(traceback_message)
        logs.logger.error(traceback_message)
        embed.add_field(name='Error', value=f'```py\n{traceback_message[:1015]}```', inline=False)
        await errors.log_error(f'Got an error:\nError: {error[1]}\nTraceback: {traceback_str}')
        await message.channel.send(embed=embed)
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
        'cogs.cooldowns',
        'cogs.clan',
        'cogs.daily',
        'cogs.dev',
        'cogs.duel',
        'cogs.dungeon_miniboss',
        'cogs.events',
        'cogs.farm',
        'cogs.fun',
        'cogs.helper_context',
        'cogs.helper_heal',
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
        'cogs.helper_pets',
        'cogs.pets',
        'cogs.quest',
        'cogs.reminders_custom',
        'cogs.reminders_lists',
        'cogs.settings',
        'cogs.settings_guild',
        'cogs.slashboard',
        'cogs.sleepy_potion',
        'cogs.tasks',
        'cogs.tracking',
        'cogs.training',
        'cogs.vote',
        'cogs.weekly',
        'cogs.work',
        'cogs.dev_old',
    ]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)


bot.run(settings.TOKEN)