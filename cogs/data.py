# data.py
"""Contains commands related to data"""

import discord
from discord.ext import bridge, commands
from discord.ext.bridge import BridgeOption

from content import data


class DataCog(commands.Cog):
    """Cog with data commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot


    # Bridge commands
    @bridge.bridge_command(name='data', description='Shows your EPIC RPG data Navi tracks', aliases=('p',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def data(
        self,
        ctx: bridge.BridgeContext,
        user: BridgeOption(discord.User, description='User to view the data of', default=None)
    ) -> None:
        """Shows your EPIC RPG data Navi tracks"""
        if not user:
            user = ctx.author
        if user.bot:
            await ctx.respond('Imagine trying to check the data of a bot.')
            return
        await data.command_data(self.bot, ctx, user)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(DataCog(bot))