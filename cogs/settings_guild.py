# settings_guild.py
"""Contains guild settings commands"""

from discord.ext import bridge, commands

from database import guilds
from resources import strings


class SettingsGuildCog(commands.Cog):
    """Cog with guild settings commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.command(aliases=('setprefix',))
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True)
    async def prefix(self, ctx: commands.Context, *args: str) -> None:
        """Gets/sets new server prefix"""
        guild: guilds.Guild = await guilds.get_guild(ctx.guild.id)
        prefix = guild.prefix
        syntax = f'{prefix}prefix <prefix>'
        message_syntax = (
            f'{strings.MSG_SYNTAX.format(syntax=syntax)}\n\n'
            f'{"Tip: If you want to include a space, use quotation marks."}\n'
            f'Examples:\n• `{prefix}prefix "navi "`\n• `{prefix}prefix &`'
        )
        if args:
            if len(args) > 1:
                await ctx.reply(message_syntax)
                return
            (new_prefix,) = args
            await guild.update(prefix=new_prefix)
            await ctx.reply(f'Prefix changed to `{guild.prefix}`')
        else:
            await ctx.reply(
                f'The prefix for this server is `{guild.prefix}`\nTo change the prefix use `{syntax}`'
            )


# Initialization
def setup(bot):
    bot.add_cog(SettingsGuildCog(bot))
