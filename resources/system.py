# system.py
"""Creates the bot object"""

import discord
from discord.ext import commands

from database import guilds


intents = discord.Intents.none()
intents.guilds = True   # for on_guild_join() and all guild objects
intents.messages = True   # for command detection
intents.members = True  # To be able to look up user info

bot = commands.Bot(command_prefix=guilds.get_all_prefixes, help_command=None, case_insensitive=True, intents=intents)