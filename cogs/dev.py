# dev.py
"""Internal dev commands"""

import importlib
import sys

import discord
from discord.commands import SlashCommandGroup, Option
from discord.ext import commands

from database import cooldowns
from resources import emojis, exceptions, functions, logs, settings, strings, views


EVENT_REDUCTION_TYPES = [
    'Text commands',
    'Slash commands',
]


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

    # Commands
    @dev.command()
    async def reload(
        self,
        ctx: discord.ApplicationContext,
        modules: Option(str, 'Cogs or modules to reload'),
    ) -> None:
        """Reloads cogs or modules"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
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
    async def event_reduction(
        self,
        ctx: discord.ApplicationContext,
        command_type: Option(str, 'Reduction type', choices=EVENT_REDUCTION_TYPES),
        activities: Option(str, 'Activities to update', default=''),
        event_reduction: Option(float, 'Event reduction in percent', min_value=0, max_value=99, default=None),
    ) -> None:
        """Changes the event reduction for activities"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
        attribute_name = 'event_reduction_slash' if 'slash' in command_type.lower() else 'event_reduction_mention'
        activities = activities.split()
        if not activities and event_reduction is None:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = f'Current event reductions for {command_type.lower()}:'
            for cooldown in all_cooldowns:
                event_reduction = getattr(cooldown, attribute_name)
                actual_cooldown = cooldown.actual_cooldown_mention() if command_type == 'Mention' else cooldown.actual_cooldown_slash()
                cooldown_message = (
                    f'{emojis.BP} {cooldown.activity}: {event_reduction}% '
                    f'({actual_cooldown:,}s)'
                )
                answer = f'{answer}\n**{cooldown_message}**' if event_reduction > 0 else f'{answer}\n{cooldown_message}'
            await ctx.respond(answer)
            return
        if not activities or event_reduction is None:
            await ctx.respond(
                f'You need to set both activity _and_ event_reduction. If you want to see the current reductions, '
                f'leave both options empty.',
                ephemeral=True
            )
            return
        for index, activity in enumerate(activities):
            if activity in strings.ACTIVITIES_ALIASES: activities[index] = strings.ACTIVITIES_ALIASES[activity]

        if 'all' in activities:
            activities += strings.ACTIVITIES_WITH_COOLDOWN
            activities.remove('all')
        updated_activities = []
        ignored_activities = []
        for activity in activities:
            if activity in strings.ACTIVITIES_WITH_COOLDOWN:
                updated_activities.append(activity)
            else:
                ignored_activities.append(activity)
        all_cooldowns = await cooldowns.get_all_cooldowns()
        answer = ''
        if updated_activities:
            answer = f'Updated event reductions for {command_type.lower()} commands as follows:'
            for activity in updated_activities:
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
                kwarg = {
                    attribute_name: event_reduction,
                }
                await cooldown.update(**kwarg)
                answer = f'{answer}\n{emojis.BP} `{cooldown.activity}` to **{event_reduction}%**'
        if ignored_activities:
            answer = f'{answer}\n\nDidn\'t find the following activities:'
            for ignored_activity in ignored_activities:
                answer = f'{answer}\n{emojis.BP} `{ignored_activity}`'
        await ctx.respond(answer)

    @dev.command(name='base-cooldown')
    async def base_cooldown(
        self,
        ctx: discord.ApplicationContext,
        activity: Option(str, 'Activity to update', choices=strings.ACTIVITIES_WITH_COOLDOWN, default=None),
        base_cooldown: Option(int, 'Base cooldown in seconds', min_value=1, max_value=604_200, default=None),
    ) -> None:
        """Changes the base cooldown for activities"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
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
    async def post_message(
        self,
        ctx: discord.ApplicationContext,
        message_id: Option(str, 'Message ID of the message IN THIS CHANNEL with the content'),
        channel_id: Option(str, 'Channel ID of the channel where the message is sent to'),
        embed_title: Option(str, 'Title of the embed', max_length=256),
    ) -> None:
        """Sends the content of a message to a channel in an embed"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
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
        view.interaction_message = interaction
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
    async def support(self, ctx: discord.ApplicationContext):
        """Link to the dev support server"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
        await ctx.respond(
            f'Got some issues or questions running Navi? Feel free to join the Navi dev support server:\n'
            f'https://discord.gg/Kz2Vz2K4gy'
        )

    @dev.command()
    async def shutdown(self, ctx: discord.ApplicationContext):
        """Shuts down the bot"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
        interaction = await ctx.respond(f'**{ctx.author.name}**, are you **SURE**?', view=view)
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(interaction, content=f'**{ctx.author.name}**, you didn\'t answer in time.',
                                             view=None)
        elif view.value == 'confirm':
            await functions.edit_interaction(interaction, content='Shutting down.', view=None)
            await self.bot.close()
        else:
            await functions.edit_interaction(interaction, content='Shutdown aborted.', view=None)

    @dev.command()
    @commands.is_owner()
    async def consolidate(self, ctx: discord.ApplicationContext):
        """Miriel test command. Consolidates tracking records older than 28 days manually"""
        await ctx.defer()
        from datetime import datetime
        import asyncio
        from humanfriendly import format_timespan
        from database import tracking, users
        start_time = datetime.utcnow().replace(microsecond=0)
        log_entry_count = 0
        try:
            old_log_entries = await tracking.get_old_log_entries(28)
        except exceptions.NoDataFoundError:
            await ctx.respond('Nothing to do.')
            return
        entries = {}
        for log_entry in old_log_entries:
            date_time = log_entry.date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            key = (log_entry.user_id, log_entry.guild_id, log_entry.command, date_time)
            amount = entries.get(key, 0)
            entries[key] = amount + 1
            log_entry_count += 1
        for key, amount in entries.items():
            user_id, guild_id, command, date_time = key
            summary_log_entry = await tracking.insert_log_summary(user_id, guild_id, command, date_time, amount)
            date_time_min = date_time.replace(hour=0, minute=0, second=0, microsecond=0)
            date_time_max = date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            await tracking.delete_log_entries(user_id, guild_id, command, date_time_min, date_time_max)
            await asyncio.sleep(0.01)
        cur = settings.NAVI_DB.cursor()
        cur.execute('VACUUM')
        end_time = datetime.utcnow().replace(microsecond=0)
        time_passed = end_time - start_time
        logs.logger.info(f'Consolidated {log_entry_count:,} log entries in {format_timespan(time_passed)} manually.')
        await ctx.respond(f'Consolidated {log_entry_count:,} log entries in {format_timespan(time_passed)}.')

    @dev.command()
    @commands.is_owner()
    async def delete_old(self, ctx: discord.ApplicationContext):
        """Miriel test command. Deletes single tracking records older than 28 days"""
        await ctx.defer()
        from datetime import datetime, timedelta
        from humanfriendly import format_timespan
        import sqlite3
        start_time = datetime.utcnow().replace(microsecond=0)
        date_time = datetime.utcnow() - timedelta(days=28)
        date_time = date_time.replace(hour=0, minute=0, second=0)
        sql = 'DELETE FROM tracking_log WHERE date_time<? AND type=?'
        try:
            cur = settings.NAVI_DB.cursor()
            cur.execute(sql, (date_time, 'single'))
        except sqlite3.Error as error:
            raise
        end_time = datetime.utcnow().replace(microsecond=0)
        time_passed = end_time - start_time
        await ctx.respond(f'Completed in {format_timespan(time_passed)}.')


    @dev.command()
    @commands.is_owner()
    async def pet_commands(self, ctx: discord.ApplicationContext):
        """Miriel test command. Just ignore"""
        field = f'FEED FEED PAT PAT'
        embed1 = discord.Embed(
            title = 'LOWEST RISK',
            description = field
        )
        embed2 = discord.Embed(
            title = 'CHANCE AT SKILL',
            description = field
        )
        embed1.set_footer(text='Catch chance: 67.06 - 85.88%')
        embed2.set_footer(text='Catch chance: 57.65 - 71.76%')
        await ctx.respond(embeds=[embed1, embed2])


def setup(bot):
    bot.add_cog(DevCog(bot))