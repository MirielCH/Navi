# feddback.py
"""Contains feedback commands

To enable this cog, you need to set COMPLAINT_CHANNEL_ID and SUGGESTION_CHANNEL_ID in the .env file.
"""

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from resources import functions, settings, views


class FeedbackCog(commands.Cog):
    """Cog with feedback commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot        

    # Commands
    @slash_command()
    async def complaint(
        self,
        ctx: discord.ApplicationContext,
        message: Option(str, 'Complaint you want to send', max_length=2000),
    ) -> None:
        """Sends a complaint about Navi to the dev."""
        embed = discord.Embed(
            title = f'**{ctx.author.name}** has a complaint',
            description = message
        )

        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            'Send the following complaint to the dev?',
            view=view,
            embed=embed
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        elif view.value == 'confirm':
            await self.bot.wait_until_ready()
            complaint_channel = await self.bot.fetch_channel(settings.COMPLAINT_CHANNEL_ID)
            if complaint_channel is None:
                await ctx.followup.send('Whoops, can\'t reach the complaint channel. Please tell the dev.')
                return
            try:
                await complaint_channel.send(embed=embed)
            except:
                await ctx.followup.send('Whoops, can\'t reach the complaint channel. Please tell the dev.')
                return
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Complaint sent.')
        else:
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Complaining aborted. Can\'t have been that important then, heh.')
            
    @slash_command()
    async def suggestion(
        self,
        ctx: discord.ApplicationContext,
        message: Option(str, 'Suggestion you want to send', max_length=2000),
    ) -> None:
        """Sends a suggestion about Navi to the dev."""
        embed = discord.Embed(
            title = f'**{ctx.author.name}** has a suggestion',
            description = message
        )

        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            'Send the following suggestion to the dev?',
            view=view,
            embed=embed
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        elif view.value == 'confirm':
            await self.bot.wait_until_ready()
            suggestion_channel = await self.bot.fetch_channel(settings.SUGGESTION_CHANNEL_ID)
            if suggestion_channel is None:
                await ctx.followup.send('Whoops, can\'t reach the suggestion channel. Please tell the dev.')
                return
            try:
                await suggestion_channel.send(embed=embed)
            except:
                await ctx.followup.send('Whoops, can\'t reach the suggestion channel. Please tell the dev.')
                return
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Suggestion sent.')
        else:
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Sending suggestion aborted. Can\'t have been that important then, heh.')


# Initialization
def setup(bot):
    bot.add_cog(FeedbackCog(bot))