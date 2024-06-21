# feedback.py
# pyright: reportInvalidTypeForm=false
"""Contains feedback commands

To enable this cog, you need to set COMPLAINT_CHANNEL_ID and SUGGESTION_CHANNEL_ID in the .env file.
"""

import discord
from discord.ext import bridge, commands
from discord.ext.bridge import BridgeOption

from resources import settings, views


class FeedbackCog(commands.Cog):
    """Cog with feedback commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot        

    # Commands
    @bridge.bridge_command(name='complaint', aliases=('complain',), description='Sends a complaint about Navi to the owner.')
    async def complaint(
        self,
        ctx: bridge.BridgeContext,
        *,
        message: BridgeOption(str, description='Complaint you want to send', max_length=2000)
    ) -> None:
        """Sends a complaint about Navi to the owner."""
        ctx_author_name = ctx.author.global_name if ctx.author.global_name is not None else ctx.author.name
        embed = discord.Embed(
            title = f'**{ctx.author.name}** has a complaint',
            description = message
        )
        embed.set_footer(text=f'Sent from server {ctx.guild.name}')

        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            'Send the following complaint to the dev?',
            view=view,
            embed=embed,
            ephemeral=True
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx_author_name}**, you didn\'t answer in time.', ephemeral=True)
        elif view.value == 'confirm':
            await self.bot.wait_until_ready()
            complaint_channel = await self.bot.fetch_channel(settings.COMPLAINT_CHANNEL_ID)
            if complaint_channel is None:
                answer = 'Whoops, can\'t reach the complaint channel. Please tell the dev.'
                if ctx.is_app:
                    await ctx.followup.send(answer, ephemeral=True)
                else:
                    await ctx.send(answer)
                return
            try:
                await complaint_channel.send(embed=embed)
            except:
                answer = 'Whoops, can\'t reach the complaint channel. Please tell the dev.'
                if ctx.is_app:
                    await ctx.followup.send(answer, ephemeral=True)
                else:
                    await ctx.send(answer)
                return
            await interaction.edit( view=None)
            answer = 'Complaint sent.'
        else:
            await interaction.edit(view=None)
            answer = 'Complaining aborted. Can\'t have been that important then, heh.'
        if ctx.is_app:
            await ctx.followup.send(answer, ephemeral=True)
        else:
            await ctx.send(answer)
            
    @bridge.bridge_command(name='suggestion', aliases=('suggest',), description='Sends a suggestion about Navi to the owner.')
    async def suggestion(
        self,
        ctx: bridge.BridgeContext,
        *,
        message: BridgeOption(str, description='Suggestion you want to send', max_length=2000),
    ) -> None:
        """Sends a suggestion about Navi to the dev."""
        ctx_author_name = ctx.author.global_name if ctx.author.global_name is not None else ctx.author.name
        embed = discord.Embed(
            title = f'**{ctx.author.name}** has a suggestion',
            description = message
        )
        embed.set_footer(text=f'Sent from server {ctx.guild.name}')

        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            'Send the following suggestion to the dev?',
            view=view,
            embed=embed,
            ephemeral=True
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx_author_name}**, you didn\'t answer in time.', ephemeral=True)
        elif view.value == 'confirm':
            await self.bot.wait_until_ready()
            suggestion_channel = await self.bot.fetch_channel(settings.SUGGESTION_CHANNEL_ID)
            if suggestion_channel is None:
                answer = 'Whoops, can\'t reach the suggestion channel. Please tell the dev.'
                if ctx.is_app:
                    await ctx.followup.send(answer, ephemeral=True)
                else:
                    await ctx.send(answer)
                return
            try:
                await suggestion_channel.send(embed=embed)
            except:
                answer = 'Whoops, can\'t reach the suggestion channel. Please tell the dev.'
                if ctx.is_app:
                    await ctx.followup.send(answer, ephemeral=True)
                else:
                    await ctx.send(answer)
                return
            await interaction.edit(view=None)
            answer = 'Suggestion sent.'
        else:
            await interaction.edit(view=None)
            answer = 'Sending suggestion aborted. Can\'t have been that important then, heh.'
        if ctx.is_app:
            await ctx.followup.send(answer, ephemeral=True)
        else:
            await ctx.send(answer)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(FeedbackCog(bot))