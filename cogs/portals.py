# link.py
"""Contains the link command"""

import discord
from discord.commands import slash_command
from discord.ext import commands

from content import portals


class PortalsCog(commands.Cog):
    """Cog with the link command"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Link commands
    @slash_command(description='A list of your favorite channels')
    async def portals(self, ctx: discord.ApplicationContext) -> None:
        """Link command"""
        await portals.command_portals(self.bot, ctx)

    #Prefix commands
    aliases = (
        'link',
        'links',
        'port',
        'pt',
        'ports',
        'portal',
        'fav',
        'favs',
        'favorite',
        'favorites',
        'favourite',
        'favourites',
        'channel',
        'channels',
    )
    @commands.command(name='portals', aliases=aliases)
    @commands.bot_has_permissions(send_messages=True)
    async def prefix_portals(self, ctx: commands.Context) -> None:
        """Link command (prefix version)"""
        await portals.command_portals(self.bot, ctx)


# Initialization
def setup(bot):
    bot.add_cog(PortalsCog(bot))