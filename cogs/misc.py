# misc.py
"""Contains error handling and the help and about commands"""

from discord.ext import bridge, commands
from discord.ext.bridge import BridgeOption

from content import misc
        

class MiscCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Bridge commands
    @bridge.bridge_command(name='calculator', description='A basic calculator',
                           aliases=('calc','math',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def calculator(
        self,
        ctx: bridge.BridgeContext,
        *,
        calculation: BridgeOption(str, description='The calculation you want solved'),
    ) -> None:
        """Basic calculator"""
        await misc.command_calculator(self.bot, ctx, calculation)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(MiscCog(bot))