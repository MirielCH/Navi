# bot.py

import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

from database import guilds


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = True if os.getenv('DEBUG_MODE) == 'ON' else False


intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection


bot = commands.Bot(command_prefix=guilds.get_all_prefixes, help_command=None, case_insensitive=True, intents=intents)
EXTENSIONS = [
    'cogs.adventure',
    'cogs.arena',
    'cogs.buy',
    'cogs.cooldowns',
    'cogs.custom-reminders',
    'cogs.daily',
    'cogs.duel',
    'cogs.dung-mb',
    'cogs.events',
    'cogs.farm',
    'cogs.clan',
    'cogs.horse',
    'cogs.hunt',
    'cogs.inventory',
    'cogs.lottery',
    'cogs.nsmb-bigarena',
    'cogs.open',
    'cogs.pets',
    'cogs.quest',
    'cogs.sleepypotion',
    'cogs.trade',
    'cogs.training',
    'cogs.weekly',
    'cogs.work',
    'cogs.dev',
    'cogs.main',
    'cogs.settings_user',
    'cogs.settings_guild',
    'cogs.settings_partner',
    'cogs.fun'
]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)


bot.run(TOKEN)