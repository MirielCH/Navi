# reminders_custom.py

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from content import reminders_custom
from database import reminders, users
from resources import emojis, functions, strings


class RemindersCustomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """Cog that contains custom reminder commands"""

    # Slash commands
    @slash_command(name='custom-reminder')
    async def custom_reminder(
        self,
        ctx: discord.ApplicationContext,
        timestring: Option(str, 'Timestring (e.g. 1h20m10s'),
        text: Option(str, 'Text of the reminder', max_length=1500),
    ) -> None:
        """Adds a custom reminder"""
        await reminders_custom.command_custom_reminder(ctx, timestring, text)

    # Prefix commands
    @commands.command(aliases=('rm','remind'))
    @commands.bot_has_permissions(send_messages=True)
    async def reminder(self, ctx: commands.Context, *args: str) -> None:
        """Adds a custom reminder (prefix version)"""
        prefix = ctx.prefix
        syntax_add = (
            f'The syntax is `{prefix}rm [time] [text]`\n'
            f'Supported time codes: `w`, `d`, `h`, `m`, `s`\n\n'
            f'Example: `{prefix}rm 1h30m Coffee time!`'
        )
        if not args:
            await ctx.reply(
                f'This command lets you add a custom reminder.\n'
                f'{syntax_add}\n\n'
                f'You can delete custom reminders in {await functions.get_navi_slash_command(self.bot, "list")}.\n'
            )
            return
        args = list(args)
        timestring = args[0].lower()
        args.pop(0)
        reminder_text = ' '.join(args) if args else 'idk, something?'
        await reminders_custom.command_custom_reminder(ctx, timestring, reminder_text)


# Initialization
def setup(bot):
    bot.add_cog(RemindersCustomCog(bot))