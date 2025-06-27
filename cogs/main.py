# main.py
"""Contains error handling and the help and about commands"""

from typing import TYPE_CHECKING

import discord
from discord import slash_command
from discord.ext import bridge, commands

from content import main
from database import errors, guilds
from resources import exceptions, functions, logs, settings, strings

if TYPE_CHECKING:
    from discord.ext.commands import Command
        

class MainCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Bridge commands
    @bridge.bridge_command(name='event-reductions', description='Shows currently active event reductions',
                           aliases=('event','er','events','reductions'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def event_reductions(self, ctx: bridge.BridgeContext) -> None:
        """Shows currently active event reductions"""
        await main.command_event_reduction(self.bot, ctx)
        
    @bridge.bridge_command(name='help', description='Main help command', aliases=('h',))
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def help(self, ctx: bridge.BridgeContext) -> None:
        """Main help command"""
        await main.command_help(self.bot, ctx)

    @bridge.bridge_command(name='about', description='Some info and links about Navi', aliases=('info','ping'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def about(self, ctx: bridge.BridgeContext) -> None:
        """About command"""
        await main.command_about(self.bot, ctx)

    # Slash commands
    if settings.LINK_INVITE:
        @slash_command(name='invite', description='Invite Navi to your server!')
        async def invite(self, ctx: discord.ApplicationContext) -> None:
            """Sends an invite link"""
            await ctx.respond(f'Click [here]({settings.LINK_INVITE}) to invite me!')

    # Text commands
    @commands.command(name='invite', aliases=('inv',))
    @commands.bot_has_permissions(send_messages=True)
    async def invite_prefix(self, ctx: commands.Context) -> None:
        """Text invite command"""
        if settings.LINK_INVITE:
            answer: str = (
                f'Click [here]({settings.LINK_INVITE}) to invite me!'
            )
        else:
            navi_lite_invite: str = 'https://canary.discord.com/api/oauth2/authorize?client_id=1213487623688167494&permissions=378944&scope=bot'
            answer: str = (
                f'Sorry, you can\'t invite this Navi.\n\n'
                f'However, you can:\n'
                f'1. [Invite Navi Lite]({navi_lite_invite}), a global version of Navi with a few limitations.\n'
                f'2. [Run Navi yourself](https://github.com/MirielCH/Navi). Navi is free and open source.\n'
            )
        await ctx.reply(answer)

     # Events
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception) -> None:
        """Runs when an error occurs and handles them accordingly.
        Interesting errors get written to the database for further review.
        """
        command_name: str = f'{ctx.command.full_parent_name} {ctx.command.name}'.strip()
        command_name = await functions.get_navi_slash_command(self.bot, command_name)
        async def send_error() -> None:
            """Sends error message as embed"""
            embed: discord.Embed = discord.Embed(title='An error occured')
            embed.add_field(name='Command', value=f'{command_name}', inline=False)
            embed.add_field(name='Error', value=f'```py\n{error}\n```', inline=False)
            await ctx.respond(embed=embed, ephemeral=True)

        error = getattr(error, 'original', error)
        if isinstance(error, commands.NoPrivateMessage):
            if ctx.guild_id is None:
                await ctx.respond(
                    f'I\'m sorry, this command is not available in DMs.',
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    f'I\'m sorry, this command is not available in this server.\n\n'
                    f'To allow this, a server admin needs to reinvite me with the necessary permissions.\n',
                    ephemeral=True
                )
        elif isinstance(error, (commands.MissingPermissions, commands.MissingRequiredArgument,
                                commands.TooManyArguments, commands.BadArgument)):
            await send_error()
        elif isinstance(error, commands.BotMissingPermissions):
            missing_permissions = ', '.join([permission.title().replace('_',' ') for permission in error.missing_permissions])
            await ctx.respond(
                f'You can\'t use this command in this channel.\n'
                f'To enable this, I need the permission(s) `{missing_permissions}` in this channel.',
                ephemeral=True
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                f'Hold your horses, wait another {error.retry_after:.1f}s before using this again.',
                ephemeral=True
            )
        elif isinstance(error, exceptions.FirstTimeUserError):
            ctx_author_name: str = ctx.author.global_name if ctx.author.global_name else ctx.author.name
            await ctx.respond(
                f'Hey! **{ctx_author_name}**, looks like I don\'t know you yet.\n'
                f'Use {await functions.get_navi_slash_command(self.bot, "on")} or `{ctx.prefix}on` to activate me first.',
                ephemeral=True
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.respond(
                f'As you might have guessed, you are not allowed to use this command.',
                ephemeral=True
            )
            await errors.log_error(error, ctx)
        elif isinstance(error, discord.errors.Forbidden):
            return
        else:
            await errors.log_error(error, ctx)
            if settings.DEBUG_MODE or ctx.guild.id in settings.DEV_GUILDS: await send_error()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Runs when an error occurs and handles them accordingly.
        Interesting errors get written to the database for further review.
        """
        async def send_error() -> None:
            """Sends error message as embed"""
            embed: discord.Embed = discord.Embed(title='An error occured')
            embed.add_field(name='Command', value=f'`{ctx.command.qualified_name}`', inline=False)
            embed.add_field(name='Error', value=f'```py\n{error}\n```', inline=False)
            await ctx.reply(embed=embed)

        error = getattr(error, 'original', error)
        ctx_author_name: str = ctx.author.global_name if ctx.author.global_name else ctx.author.name
        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f'**{ctx_author_name}**, you can only use this command every '
                f'{int(error.cooldown.per)} seconds.\n'
                f'You have to wait another **{error.retry_after:.1f}s**.'
            )
        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply(f'Command `{ctx.command.qualified_name}` is temporarily disabled.')
        elif isinstance(error, (commands.MissingPermissions,
                                commands.TooManyArguments, commands.BadArgument)):
            await send_error()
        elif isinstance(error, commands.BotMissingPermissions):
            if 'send_messages' in error.missing_permissions:
                return
            if 'embed_links' in error.missing_perms:
                await ctx.reply(error)
            else:
                await send_error()
        elif isinstance(error, commands.MissingRequiredArgument):
            parameters: str = ''
            full_command_name: str = f'{ctx.command.full_parent_name} {ctx.invoked_with}'.strip()
            for param_name in ctx.command.clean_params.keys():
                parameters = f'{parameters} <{param_name}>'
            answer: str = (
                f'**{ctx_author_name}**, this command is missing the parameter `<{error.param.name}>`.\n\n'
                f'Syntax: `{ctx.clean_prefix}{full_command_name} {parameters.strip()}`'
            )
            await ctx.reply(answer)
        elif isinstance(error, exceptions.FirstTimeUserError):
            await ctx.reply(
                f'**{ctx_author_name}**, looks like I don\'t know you yet.\n'
                f'Use {await functions.get_navi_slash_command(self.bot, "on")} or `{ctx.prefix}on` to activate me first.',
            )
        elif isinstance(error, (commands.UnexpectedQuoteError, commands.InvalidEndOfQuotedStringError,
                                commands.ExpectedClosingQuoteError)):
            await ctx.reply(
                f'**{ctx_author_name}**, whatever you just entered contained invalid characters I can\'t process.\n'
                f'Please try that again.'
            )
            await errors.log_error(error, ctx)
        elif isinstance(error, commands.CheckFailure):
            await ctx.respond(
                await ctx.respond('As you might have guessed, you are not allowed to use this command.',
                ephemeral=True)
            )
        elif isinstance(error, exceptions.NoClanLeaderFoundError):
            await ctx.reply(
                f'**{ctx_author_name}**, there is no leader registered for this guild.\n'
                f'Use {strings.SLASH_COMMANDS["guild list"]} or `rpg guild list` to update your guild.',
            )
        elif isinstance(error, discord.errors.Forbidden):
            return
        else:
            await errors.log_error(error, ctx)
            if settings.DEBUG_MODE or ctx.guild.id in settings.DEV_GUILDS: await send_error()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.bot: return
        if (
            self.bot.user.mentioned_in(message)
            and (message.content.lower().replace('<@!','').replace('<@','').replace('>','')
                 .replace(str(self.bot.user.id),'')) == ''
        ):
            command: Command = self.bot.get_command(name='help')
            if command is not None: await command.callback(command.cog, message)

    # Events
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when bot has finished starting"""
        startup_info: str = f'{self.bot.user.name} has connected to Discord!'
        print(startup_info)
        logs.logger.info(startup_info)
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Fires when bot joins a guild. Sends a welcome message to the system channel."""
        try:
            guild_settings: guilds.Guild = await guilds.get_guild(guild.id)
            welcome_message: str = (
                f'Hey! **{guild.name}**! I\'m here to remind you to do your EPIC RPG commands!\n\n'
                f'Note that reminders are off by default. If you want to get reminded, please use '
                f'{await functions.get_navi_slash_command(self.bot, "on")} or `{guild_settings.prefix}on` to activate me.'
            )
            await guild.system_channel.send(welcome_message)
        except:
            return


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(MainCog(bot))