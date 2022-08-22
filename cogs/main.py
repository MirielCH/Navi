# main.py
"""Contains error handling and the help and about commands"""

import discord
from discord.ext import commands
from discord.commands import slash_command

from content import main
from database import errors, guilds
from resources import exceptions, logs, settings, strings


class MainCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @slash_command(description='Main help command')
    async def help(self,ctx: discord.ApplicationContext) -> None:
        """Main help command"""
        await main.command_help(ctx)

    @slash_command(description='Some info and links about Navi')
    async def about(self, ctx: discord.ApplicationContext) -> None:
        """About command"""
        await main.command_about(self.bot, ctx)

     # Events
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception) -> None:
        """Runs when an error occurs and handles them accordingly.
        Interesting errors get written to the database for further review.
        """
        command_name = f'{ctx.command.full_parent_name} {ctx.command.name}'.strip()
        command_name = strings.SLASH_COMMANDS_NAVI.get(command_name, f'`/{command_name}`')
        async def send_error() -> None:
            """Sends error message as embed"""
            embed = discord.Embed(title='An error occured')
            embed.add_field(name='Command', value=f'`{command_name}`', inline=False)
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
                    f'To allow this, the server admin needs to reinvite me with the necessary permissions.\n',
                    ephemeral=True
                )
        elif isinstance(error, (commands.MissingPermissions, commands.MissingRequiredArgument,
                                commands.TooManyArguments, commands.BadArgument)):
            await send_error()
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.respond(
                f'You can\'t use this command in this channel.\n'
                f'To enable this, I need the permission `View Channel` / '
                f'`Read Messages` in this channel.',
                ephemeral=True
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                f'Hold your horses, wait another {error.retry_after:.1f}s before using this again.',
                ephemeral=True
            )
        elif isinstance(error, exceptions.FirstTimeUserError):
            await ctx.respond(
                f'Hey! **{ctx.author.name}**, looks like I don\'t know you yet.\n'
                f'Use {strings.SLASH_COMMANDS_NAVI["on"]} to activate me first.',
                ephemeral=True
            )
        elif isinstance(error, commands.NotOwner):
            await ctx.respond(
                f'As you might have guessed, you are not allowed to use this command.',
                ephemeral=True
            )
        else:
            await errors.log_error(error, ctx)
            if settings.DEBUG_MODE or ctx.author.id in settings.DEV_IDS:
                await send_error()
            else:
                await ctx.respond(
                    'Well shit, something went wrong here. Sorry about that.',
                    ephemeral=True
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.bot: return
        if (
            self.bot.user.mentioned_in(message)
            and (message.content.lower().replace('<@!','').replace('<@','').replace('>','')
                 .replace(str(self.bot.user.id),'')) == ''
        ):
            await self.main_help(message)

    # Events
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when bot has finished starting"""
        startup_info = f'{self.bot.user.name} has connected to Discord!'
        print(startup_info)
        logs.logger.info(startup_info)
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                  name='your commands'))
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Fires when bot joins a guild. Sends a welcome message to the system channel."""
        try:
            guild_settings: guilds.Guild = guilds.get_guild(guild.id)
            welcome_message = (
                f'Hey! **{guild.name}**! I\'m here to remind you to do your EPIC RPG commands!\n\n'
                f'Note that reminders are off by default. If you want to get reminded, please use '
                f'{strings.SLASH_COMMANDS_NAVI["on"]} to activate me.'
            )
            await guild.system_channel.send(welcome_message)
        except:
            return


# Initialization
def setup(bot):
    bot.add_cog(MainCog(bot))