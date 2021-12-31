# bot.py

import discord
from discord.ext import commands

from database import guilds
from resources import settings

intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection
intents.members = True  # To be able to look up user info

bot = commands.Bot(command_prefix=guilds.get_all_prefixes, help_command=None, case_insensitive=True, intents=intents)

EXTENSIONS = [
        'cogs.adventure',
        'cogs.arena',
        'cogs.buy',
        'cogs.cooldowns',
        'cogs.custom-reminders',
        'cogs.daily',
        'cogs.duel',
        'cogs.dungeon-miniboss',
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
        'cogs.sleepy-potion',
        'cogs.trade',
        'cogs.training',
        'cogs.weekly',
        'cogs.work',
        'cogs.dev',
        'cogs.main',
        'cogs.settings_user',
        'cogs.settings_guild',
        'cogs.settings_partner',
        'cogs.settings_clan',
        'cogs.fun',
        'cogs.tasks',
        'cogs.tracking'
    ]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)

bot.run(settings.TOKEN)