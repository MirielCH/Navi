# fun.py
"""Contains some nonsense"""

import discord
from discord.ext import commands


class FunCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('listen',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def hey(self, ctx: commands.Context) -> None:
        """Hey! Listen!"""
        if ctx.prefix.lower() == 'rpg ':
            return
        await ctx.reply('https://tenor.com/view/navi-hey-listen-gif-4837431')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""

        if not message.embeds and not message.author.bot:
            message_content = message.content
            if message_content.lower() == 'navi lit':
                await message.reply('https://tenor.com/view/betty-white-dab-mood-gif-5044603')

# Initialization
def setup(bot):
    bot.add_cog(FunCog(bot))