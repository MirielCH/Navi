# slashboard.py
"""Contains the slashboard command"""

import discord
from discord.commands import slash_command
from discord.ext import commands

from content import slashboard


class SlashboardCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash commands
    @slash_command(description='A list of useful EPIC RPG slash commands')
    async def slashboard(self, ctx: discord.ApplicationContext) -> None:
        """Slashboard command"""
        await slashboard.command_slashboard(ctx)

    #Prefix commands
    @commands.command(name='slashboard')
    @commands.bot_has_permissions(send_messages=True)
    async def prefix_slashboard(self, ctx: commands.Context, *args: str) -> None:
        """Slashboard command (prefix version)"""
        await slashboard.command_slashboard(ctx)


# Initialization
def setup(bot):
    bot.add_cog(SlashboardCog(bot))