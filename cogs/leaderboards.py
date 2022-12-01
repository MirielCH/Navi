# leaderboards.py
"""Contains clan leaderboard"""

import discord
from discord.commands import SlashCommandGroup
from discord.ext import commands

from content import leaderboards
from resources import functions


class LeaderboardsCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    cmd_leaderboard = SlashCommandGroup(
        "leaderboard",
        "Leaderboard commands",
    )

    @cmd_leaderboard.command()
    async def guild(self, ctx: discord.ApplicationContext) -> None:
        """Clan leaderboard"""
        await leaderboards.command_leaderboard_clan(ctx)

    #Prefix commands
    @commands.command(name='guild')
    @commands.bot_has_permissions(send_messages=True)
    async def prefix_leaderboard_clan(self, ctx: commands.Context, *args: str) -> None:
        """Clan command (prefix version)"""
        arg = args[0] if args else ''
        if arg in ('lb','leaderboard'):
            await leaderboards.command_leaderboard_clan(ctx)
        else:
            await ctx.reply(
                f'Hey! Please use {await functions.get_navi_slash_command(self.bot, "settings guild")} '
                f'to change guild settings.'
            )


# Initialization
def setup(bot):
    bot.add_cog(LeaderboardsCog(bot))