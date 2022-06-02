# main.py
"""Contains error handling and the help and about commands"""

from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import errors

from database import errors, guilds, users
from resources import emojis, exceptions, logs, settings


class MainCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @commands.command(name='help', aliases=('h',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def main_help(self, ctx: commands.Context) -> None:
        """Main help command"""
        if ctx.prefix.lower() == 'rpg ':
            return
        embed = await embed_main_help(ctx)
        await ctx.reply(embed=embed)

    @commands.command(aliases=('inv',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def invite(self, ctx: commands.Context) -> None:
        """Invite command"""
        if ctx.prefix.lower() == 'rpg ':
            return
        message = (
            f'Sorry, you can\'t invite me.\n'
            f'However, I am fully open source on an MIT license, so feel free to run me yourself.\n'
            f'https://github.com/Miriel-py/Navi'
        )
        await ctx.reply(message)

    @commands.command(aliases=('ping','info'))
    async def about(self, ctx: commands.Context) -> None:
        """Shows some info about Navi"""
        if ctx.prefix.lower() == 'rpg ':
            return
        start_time = datetime.utcnow()
        message = await ctx.send('Testing API latency...')
        end_time = datetime.utcnow()
        api_latency = end_time - start_time
        embed = await embed_about(self.bot, api_latency)
        await message.edit(content=None, embed=embed)


     # Events
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Runs when an error occurs and handles them accordingly.
        Interesting errors get written to the database for further review.
        """
        async def send_error() -> None:
            """Sends error message as embed"""
            embed = discord.Embed(title='An error occured')
            embed.add_field(name='Command', value=f'`{ctx.command.qualified_name}`', inline=False)
            embed.add_field(name='Error', value=f'```py\n{error}\n```', inline=False)
            await ctx.reply(embed=embed)

        error = getattr(error, 'original', error)
        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f'**{ctx.author.name}**, you can only use this command every '
                f'{int(error.cooldown.per)} seconds.\n'
                f'You have to wait another **{error.retry_after:.1f}s**.'
            )
        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply(f'Command `{ctx.command.qualified_name}` is temporarily disabled.')
        elif isinstance(error, (commands.MissingPermissions, commands.MissingRequiredArgument,
                                commands.TooManyArguments, commands.BadArgument)):
            await send_error()
        elif isinstance(error, commands.BotMissingPermissions):
            if 'send_messages' in error.missing_permissions:
                return
            if 'embed_links' in error.missing_perms:
                await ctx.reply(error)
            else:
                await send_error()
        elif isinstance(error, exceptions.FirstTimeUserError):
            await ctx.reply(
                f'**{ctx.author.name}**, looks like I don\'t know you yet.\n'
                f'Use `{ctx.prefix}on` to activate me first.'
            )
        elif isinstance(error, (commands.UnexpectedQuoteError, commands.InvalidEndOfQuotedStringError,
                                commands.ExpectedClosingQuoteError)):
            await ctx.reply(
                f'**{ctx.author.name}**, whatever you just entered contained invalid characters I can\'t process.\n'
                f'Please try that again.'
            )
            await errors.log_error(error, ctx)
        else:
            await errors.log_error(error, ctx)
            if settings.DEBUG_MODE or ctx.guild.id in settings.DEV_GUILDS: await send_error()


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
                f'Hey! **{guild.name}**! I\'m here to remind you to do your Epic RPG commands!\n\n'
                f'Note that reminders are off by default. If you want to get reminded, please use '
                f'`{guild_settings.prefix}on` to activate me.\n'
                f'If you don\'t like this prefix, use `{guild_settings.prefix}setprefix` to change it.\n\n'
                f'Tip: If you ever forget the prefix, simply ping me with a command.'
            )
            await guild.system_channel.send(welcome_message)
        except:
            return


# Initialization
def setup(bot):
    bot.add_cog(MainCog(bot))


# --- Embeds ---
async def embed_main_help(ctx: commands.Context) -> discord.Embed:
    """Main menu embed"""
    guild = await guilds.get_guild(ctx.guild.id)
    prefix = guild.prefix

    reminder_management = (
        f'{emojis.BP} `{prefix}list` : List all your active reminders\n'
        f'{emojis.BP} `{prefix}rm` : Manage custom reminders'
    )

    stats = (
        f'{emojis.BP} `{prefix}stats` : Shows your command stats\n'
    )

    user_settings = (
        f'{emojis.BP} `{prefix}on` / `off` : Turn the bot on/off\n'
        f'{emojis.BP} `{prefix}settings` : Check your settings\n'
        f'{emojis.BP} `{prefix}donor` : Set your EPIC RPG donor tier\n'
        f'{emojis.BP} `{prefix}enable` / `disable` : Enable/disable specific reminders\n'
        f'{emojis.BP} `{prefix}dnd on` / `off` : Turn DND mode on/off (disables pings)\n'
        f'{emojis.BP} `{prefix}hardmode on` / `off` : Turn hardmode mode on/off (tells your partner to hunt solo)\n'
        f'{emojis.BP} `{prefix}message` : Change the reminder messages\n'
        f'{emojis.BP} `{prefix}reactions on` / `off` : Turn reactions on/off\n'
        f'{emojis.BP} `{prefix}last-tt` : Manually change your last TT time\n'
    )

    helper_settings = (
        f'{emojis.BP} `{prefix}heal on` / `off` : Turn heal warning on/off\n'
        f'{emojis.BP} `{prefix}pet-helper on` / `off` : Turn the pet catch helper on/off\n'
        f'{emojis.BP} `{prefix}ruby` : Check your current ruby count\n'
        f'{emojis.BP} `{prefix}ruby on` / `off` : Turn the ruby counter on/off\n'
        f'{emojis.BP} `{prefix}tr-helper on` / `off` : Turn the training helper on/off\n'
    )

    partner_settings = (
        f'{emojis.BP} `{prefix}partner` : Set your marriage partner\n'
        f'{emojis.BP} `{prefix}partner donor` : Set your partner\'s EPIC RPG donor tier\n'
        f'{emojis.BP} `{prefix}partner channel` : Set the channel for incoming lootbox alerts'
    )

    guild_settings = (
        f'{emojis.BP} `{prefix}guild` : See how to set up guild reminders\n'
        f'{emojis.BP} `rpg guild list` : Add/update your guild\n'
        f'{emojis.BP} `{prefix}guild channel` : Set the channel for guild reminders\n'
        f'{emojis.BP} `{prefix}guild leaderboard` : Check the weekly raid leaderboard\n'
        f'{emojis.BP} `{prefix}guild reminders on` / `off` : Turn guild reminders on or off\n'
        f'{emojis.BP} `{prefix}guild stealth` : Set your stealth threshold\n'
        f'{emojis.BP} `{prefix}guild upgrade-quests on` / `off` : Allow/deny quests below threshold\n'
    )

    server_settings = (
        f'{emojis.BP} `{prefix}prefix` : Check / set the bot prefix'
    )

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'NAVI',
        description =   f'Hey! **{ctx.author.name}**! Hello!'
    )
    embed.add_field(name='REMINDERS', value=reminder_management, inline=False)
    embed.add_field(name='COMMAND TRACKING', value=stats, inline=False)
    embed.add_field(name='USER SETTINGS', value=user_settings, inline=False)
    embed.add_field(name='HELPER SETTINGS', value=helper_settings, inline=False)
    embed.add_field(name='PARTNER SETTINGS', value=partner_settings, inline=False)
    embed.add_field(name='GUILD SETTINGS', value=guild_settings, inline=False)
    embed.add_field(name='SERVER SETTINGS', value=server_settings, inline=False)

    return embed


async def embed_about(bot: commands.Bot, api_latency: datetime) -> discord.Embed:
    """Bot info embed"""
    user_count = await users.get_user_count()
    general = (
        f'{emojis.BP} {len(bot.guilds):,} servers\n'
        f'{emojis.BP} {user_count:,} users\n'
        f'{emojis.BP} {round(bot.latency * 1000):,} ms bot latency\n'
        f'{emojis.BP} {round(api_latency.total_seconds() * 1000):,} ms API latency'
    )
    creator = f'{emojis.BP} Miriel#0001'
    github = f'{emojis.BP} [https://github.com/Miriel-py/Navi](https://github.com/Miriel-py/Navi)'
    embed = discord.Embed(color = settings.EMBED_COLOR, title = 'ABOUT NAVI')
    embed.add_field(name='BOT STATS', value=general, inline=False)
    embed.add_field(name='CREATOR', value=creator, inline=False)
    embed.add_field(name='GITHUB', value=github, inline=False)
    embed.add_field(name='SPECIAL THANKS TO', value=f'{emojis.BP} Swiss cheese', inline=False)

    return embed