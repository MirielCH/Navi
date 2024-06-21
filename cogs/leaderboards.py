# leaderboards.py
"""Contains clan leaderboard"""

from discord.ext import bridge, commands

from content import leaderboards


class LeaderboardsCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @bridge.bridge_group(name='guild', aliases=('g','clan'))
    async def clan_group(self, ctx: bridge.BridgeContext):
        """Guild command group"""

    @clan_group.command(name='leaderboard', aliases=('lb',), description='View guild leaderboard')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def clan_leaderboard(self, ctx: bridge.BridgeContext):
        """Guild settings command"""
        await leaderboards.command_leaderboard_clan(ctx)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(LeaderboardsCog(bot))