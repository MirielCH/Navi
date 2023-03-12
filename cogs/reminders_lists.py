# reminders_lists.py
"""Contains reminders lists commands"""

import discord
from discord.commands import slash_command, Option
from discord.ext import commands

from content import reminders_lists
from resources import functions


class RemindersListsCog(commands.Cog):
    """Cog with reminders lists commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command()
    async def list(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.User, 'User you want to check active reminders for', default=None),
    ) -> None:
        """Lists all active reminders"""
        await reminders_lists.command_list(self.bot, ctx, user)

    @slash_command()
    async def ready(
        self,
        ctx: discord.ApplicationContext,
        user: Option(discord.User, 'User you want to check the ready commands for', default=None),
    ) -> None:
        """Lists all commands off cooldown"""
        if user is None: user = ctx.author
        if user.bot:
            await ctx.respond('Imagine trying to check the commands of a bot.', ephemeral=True)
            return
        await reminders_lists.command_ready(self.bot, ctx, user)

    @commands.command(name='list', aliases=('cd','cooldown','cooldowns'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def prefix_list(self, ctx: commands.Context, *args: str) -> None:
        """Lists all active reminders (prefix version)"""
        for mentioned_user in ctx.message.mentions.copy():
            if mentioned_user == self.bot.user:
                ctx.message.mentions.remove(mentioned_user)
                break
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        if not args:
            user = ctx.author
        else:
            arg = args[0].lower().replace('<@!','').replace('<@','').replace('>','')
            if not arg.isnumeric():
                await ctx.reply('Invalid user.')
                return
            user_id = int(arg)
            user = await functions.get_discord_user(self.bot, user_id)
            if user is None:
                await ctx.reply('This user doesn\'t exist.')
                return
        if user.bot:
            await ctx.reply('Imagine trying to check the reminders of a bot.')
            return
        await reminders_lists.command_list(self.bot, ctx, user)

    @commands.command(name='ready', aliases=('rd',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def prefix_ready(self, ctx: commands.Context, *args: str) -> None:
        """Lists all commands off cooldown (prefix version)"""
        for mentioned_user in ctx.message.mentions.copy():
            if mentioned_user == self.bot.user:
                ctx.message.mentions.remove(mentioned_user)
                break
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        if not args:
            user = ctx.author
        else:
            arg = args[0].lower().replace('<@!','').replace('<@','').replace('>','')
            if not arg.isnumeric():
                await ctx.reply('Invalid user.')
                return
            user_id = int(arg)
            user = await functions.get_discord_user(self.bot, user_id)
            if user is None:
                await ctx.reply('This user doesn\'t exist.')
                return
        if user.bot:
            await ctx.reply('Imagine trying to check the reminders of a bot.')
            return
        await reminders_lists.command_ready(self.bot, ctx, user)


# Initialization
def setup(bot):
    bot.add_cog(RemindersListsCog(bot))