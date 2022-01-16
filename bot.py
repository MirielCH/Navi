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
        'cogs.horse',
        'cogs.horse-race',
        'cogs.hunt',
        'cogs.lootbox',
        'cogs.lottery',
        'cogs.main',
        'cogs.nsmb-bigarena',
        'cogs.pet-tournament',
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
        'cogs.weekly',
        'cogs.work',
    ]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)

bot.run(settings.TOKEN)