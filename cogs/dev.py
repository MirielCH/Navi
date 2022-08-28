# dev.py
"""Internal dev commands"""

import importlib
import sys

import discord
from discord.commands import SlashCommandGroup, Option
from discord.ext import commands

from database import cooldowns
from resources import emojis, functions, settings, strings, views


class DevCog(commands.Cog):
    """Cog class containing internal dev commands"""
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    dev = SlashCommandGroup(
        "dev",
        "Development commands",
        guild_ids=settings.DEV_GUILDS,
        default_member_permissions=discord.Permissions(administrator=True)
    )

    test = SlashCommandGroup(
        "test",
        "Test commands",
        guild_ids=settings.DEV_GUILDS,
        default_member_permissions=discord.Permissions(administrator=True)
    )

    # Commands
    @dev.command()
    @commands.is_owner()
    async def reload(
        self,
        ctx: discord.ApplicationContext,
        modules: Option(str, 'Cogs or modules to reload'),
    ) -> None:
        """Reloads cogs or modules"""
        modules = modules.split(' ')
        actions = []
        for module in modules:
            name_found = False
            cog_name = f'cogs.{module}' if not 'cogs.' in module else module
            try:
                cog_status = self.bot.reload_extension(cog_name)
            except:
                cog_status = 'Error'
            if cog_status is None:
                actions.append(f'+ Extension \'{cog_name}\' reloaded.')
                name_found = True
            if not name_found:
                for module_name in sys.modules.copy():
                    if module == module_name:
                        module = sys.modules.get(module_name)
                        if module is not None:
                            importlib.reload(module)
                            actions.append(f'+ Module \'{module_name}\' reloaded.')
                            name_found = True
            if not name_found:
                actions.append(f'- No loaded cog or module with the name \'{module}\' found.')

        message = ''
        for action in actions:
            message = f'{message}\n{action}'
        await ctx.respond(f'```diff\n{message}\n```')

    @dev.command(name='event-reduction')
    @commands.is_owner()
    async def event_reduction(
        self,
        ctx: discord.ApplicationContext,
        activity: Option(str, 'Activity to update', choices=strings.ACTIVITIES_WITH_COOLDOWN_ALL, default=None),
        event_reduction: Option(float, 'Event reduction in percent', min_value=0, max_value=99, default=None),
    ) -> None:
        """Changes the event reduction for activities"""
        if activity is None and event_reduction is None:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = 'Current event reductions:'
            for cooldown in all_cooldowns:
                cooldown_message = (
                    f'{emojis.BP} {cooldown.activity}: {cooldown.event_reduction}% '
                    f'({cooldown.actual_cooldown():,}s)'
                )
                answer = f'{answer}\n**{cooldown_message}**' if cooldown.event_reduction > 0 else f'{answer}\n{cooldown_message}'
            await ctx.respond(answer)
            return
        if activity is None or event_reduction is None:
            await ctx.respond(
                'You need to set both options. If you want to see the current reductions, leave both options empty.',
                ephemeral=True
            )
            return
        if activity.lower() == 'all':
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = 'Changed event reduction for all activites as follows:'
            for cooldown in all_cooldowns:
                await cooldown.update(event_reduction=event_reduction)
                if cooldown.event_reduction == event_reduction:
                    answer = f'{answer}\n{emojis.BP} `{cooldown.activity}` to **{cooldown.event_reduction}%**'
        else:
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
            await cooldown.update(event_reduction=event_reduction)
        if cooldown.event_reduction == event_reduction:
            answer =  f'Changed event reduction for activity `{cooldown.activity}` to **{cooldown.event_reduction}%**.'
        await ctx.respond(answer)

    @dev.command(name='base-cooldown')
    @commands.is_owner()
    async def base_cooldown(
        self,
        ctx: discord.ApplicationContext,
        activity: Option(str, 'Activity to update', choices=strings.ACTIVITIES_WITH_COOLDOWN, default=None),
        base_cooldown: Option(int, 'Base cooldown in seconds', min_value=1, max_value=604_200, default=None),
    ) -> None:
        """Changes the base cooldown for activities"""
        if activity is None and base_cooldown is None:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = 'Current base cooldowns:'
            for cooldown in all_cooldowns:
                answer = f'{answer}\n{emojis.BP} {cooldown.activity}: {cooldown.base_cooldown}s'
            await ctx.respond(answer)
            return
        if activity is None or base_cooldown is None:
            await ctx.resond(
                'You need to set both options. If you want to see the current cooldowns, leave both options empty.',
                ephemeral=True
            )
            return
        cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
        await cooldown.update(cooldown=base_cooldown)
        if cooldown.base_cooldown == base_cooldown:
            answer =  f'Changed base cooldown for activity `{cooldown.activity}` to **{cooldown.base_cooldown}s**.'
        await ctx.respond(answer)

    @dev.command(name='post-message')
    @commands.is_owner()
    async def post_message(
        self,
        ctx: discord.ApplicationContext,
        message_id: Option(str, 'Message ID of the message IN THIS CHANNEL with the content'),
        channel_id: Option(str, 'Channel ID of the channel where the message is sent to'),
        embed_title: Option(str, 'Title of the embed', max_length=256),
    ) -> None:
        """Sends the content of a message to a channel in an embed"""
        await self.bot.wait_until_ready()
        try:
            message_id = int(message_id)
        except ValueError:
            await ctx.respond('The message ID is not a valid number.', ephemeral=True)
            return
        try:
            channel_id = int(channel_id)
        except ValueError:
            await ctx.respond('The channel ID is not a valid number.', ephemeral=True)
            return
        try:
            message = await ctx.channel.fetch_message(message_id)
        except:
            await ctx.respond(
                f'No message with that message ID found.\n'
                f'Note that the message needs to be in **this** channel!',
                ephemeral=True
            )
            return
        try:
            channel = await self.bot.fetch_channel(channel_id)
        except:
            await ctx.respond('No channel with that channel ID found.', ephemeral=True)
            return
        embed = discord.Embed(
            title = embed_title,
            description = message.content
        )
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            f'I will send the following embed to the channel `{channel.name}`. Proceed?',
            view=view,
            embed=embed
        )
        view.interaction = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        elif view.value == 'confirm':
            await channel.send(embed=embed)
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Message sent.')
        else:
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Sending aborted.')


    @dev.command()
    @commands.is_owner()
    async def test(self, ctx: discord.ApplicationContext):
        """Test test"""
        cmd_settings_user = self.bot.get_application_command('settings', type=discord.commands.SlashCommandGroup)
        pass


    @dev.command()
    @commands.is_owner()
    async def shutdown(self, ctx: discord.ApplicationContext):
        """Shuts down the bot"""
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
        interaction = await ctx.respond(f'**{ctx.author.name}**, are you **SURE**?', view=view)
        view.interaction = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(interaction, content=f'**{ctx.author.name}**, you didn\'t answer in time.',
                                             view=None)
        elif view.value == 'confirm':
            await functions.edit_interaction(interaction, content='Shutting down.', view=None)
            await self.bot.close()
        else:
            await functions.edit_interaction(interaction, content='Shutdown aborted.', view=None)


def setup(bot):
    bot.add_cog(DevCog(bot))