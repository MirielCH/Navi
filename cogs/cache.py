# cache.py
"""Collects messages containing rpg and mention commands for the local cache"""

import discord
from discord.ext import bridge, commands

from cache import messages
from resources import settings


class CacheCog(commands.Cog):
    """Cog that contains the cache commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.bot: return
        if message.embeds or message.content is None: return
        correct_mention = False
        if message.content.lower().startswith(('rpg ', 'testy ')):
            await messages.store_message(message)
            return
        if message.mentions:
            for mentioned_user in message.mentions:
                if mentioned_user.id == settings.EPIC_RPG_ID:
                    correct_mention = True
                    break
            if correct_mention:
                await messages.store_message(message)

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(CacheCog(bot))