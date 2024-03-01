# link.py
"""Contains the link command"""

from discord.ext import bridge, commands

from content import portals


class PortalsCog(commands.Cog):
    """Cog with the portal command"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Bridge commands
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
    @bridge.bridge_command(name='portals', aliases=aliases, description='A list of your favorite channels')
    async def portals(self, ctx: bridge.BridgeContext) -> None:
        """Portals command"""
        await portals.command_portals(self.bot, ctx)


# Initialization
def setup(bot):
    bot.add_cog(PortalsCog(bot))