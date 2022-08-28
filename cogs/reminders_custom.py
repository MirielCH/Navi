# reminders_custom.py

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from content import custom_reminders


class RemindersCustomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """Cog that contains custom reminder commands"""

    @slash_command(name='custom-reminder')
    async def help(
        self,
        ctx: discord.ApplicationContext,
        timestring: Option(str, 'Timestring (e.g. 1h20m10s'),
        text: Option(str, 'Text of the reminder', max_length=1500),
    ) -> None:
        """Adds a custom reminder"""
        await custom_reminders.command_custom_reminder(ctx, timestring, text)


# Initialization
def setup(bot):
    bot.add_cog(RemindersCustomCog(bot))