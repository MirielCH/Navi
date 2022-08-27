# settings_clan.py
"""Contains clan settings commands"""

import discord
from discord.commands import SlashCommandGroup, slash_command, Option
from discord.ext import commands

from content import settings as settings_cmd


class SettingsCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command()
    async def on(self, ctx: discord.ApplicationContext) -> None:
        """Turn on Navi"""
        await settings_cmd.command_on(self.bot, ctx)

    @slash_command()
    async def off(self, ctx: discord.ApplicationContext) -> None:
        """Turn off Navi"""
        await settings_cmd.command_off(self.bot, ctx)

    cmd_settings = SlashCommandGroup(
        "settings",
        "Settings commands",
    )

    # Commands
    @cmd_settings.command()
    async def guild(self, ctx: discord.ApplicationContext) -> None:
        """Manage guild settings"""
        await settings_cmd.command_settings_clan(self.bot, ctx)

    @cmd_settings.command()
    async def helpers(self, ctx: discord.ApplicationContext) -> None:
        """Manage helper settings"""
        await settings_cmd.command_settings_helpers(self.bot, ctx)

    @cmd_settings.command()
    async def reminders(self, ctx: discord.ApplicationContext) -> None:
        """Manage reminder settings"""
        await settings_cmd.command_settings_reminders(self.bot, ctx)

    @cmd_settings.command()
    async def user(self, ctx: discord.ApplicationContext) -> None:
        """Manage user settings"""
        await settings_cmd.command_settings_user(self.bot, ctx)


# Initialization
def setup(bot):
    bot.add_cog(SettingsCog(bot))