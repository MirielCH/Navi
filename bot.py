# bot.py

import sys
import traceback

import discord
from discord.ext import commands

from database import errors, guilds
from resources import settings

intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection
intents.members = True  # To be able to look up user info
intents.message_content = True # for command detection

allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)

bot = commands.Bot(command_prefix=guilds.get_all_prefixes, help_command=None, case_insensitive=True,
                   intents=intents, allowed_mentions=allowed_mentions)


@bot.event
async def on_error(event: str, message: discord.Message) -> None:
    """Runs when an error in an event occurs and sends a message.
    All errors get written to the database for further review.
    """
    error = sys.exc_info()
    traceback_str = "".join(traceback.format_tb(error[2]))
    traceback_message = traceback_str if settings.DEBUG_MODE else ''
    await errors.log_error(
        f'Got an error in event {event}:\nError: {error[1]}\nTraceback: {traceback_str}',
        message
    )
    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
        embed = discord.Embed(title='An error occured')
        embed.add_field(name='Event', value=f'`{event}`', inline=False)
        embed.add_field(name='Error', value=f'```py\n{error[1]}\n{traceback_message}\n```', inline=False)
        await message.channel.send(embed=embed)


EXTENSIONS = [
        'cogs.adventure',
        'cogs.arena',
        'cogs.cooldowns',
        'cogs.clan',
        'cogs.custom-reminders',
        'cogs.daily',
        'cogs.dev',
        'cogs.duel',
        'cogs.dungeon-miniboss',
        'cogs.events',
        'cogs.farm',
        'cogs.fun',
        'cogs.heal-warning',
        'cogs.horse',
        'cogs.horse-race',
        'cogs.hunt',
        'cogs.lootbox',
        'cogs.lottery',
        'cogs.main',
        'cogs.nsmb-bigarena',
        'cogs.pet-tournament',
        'cogs.pet-helper',
        'cogs.pets',
        'cogs.quest',
        'cogs.ruby-counter',
        'cogs.settings_clan',
        'cogs.settings_guild',
        'cogs.settings_partner',
        'cogs.settings_user',
        'cogs.sleepy-potion',
        'cogs.tasks',
        'cogs.tracking',
        'cogs.training',
        'cogs.training-helper',
        'cogs.vote',
        'cogs.weekly',
        'cogs.work',
    ]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)


bot.run(settings.TOKEN)