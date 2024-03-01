# slashboard.py
"""Contains the slashboard command"""

from discord.ext import bridge, commands

from content import slashboard


class SlashboardCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Bridge commands
    @bridge.bridge_command(name='slashboard', aliases=('sb',), description='A list of useful EPIC RPG slash commands')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def slashboard(self, ctx: bridge.BridgeContext) -> None:
        """Slashboard command"""
        await slashboard.command_slashboard(ctx)


# Initialization
def setup(bot):
    bot.add_cog(SlashboardCog(bot))