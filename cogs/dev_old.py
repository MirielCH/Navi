# dev.py
"""Internal dev commands"""

import asyncio
from datetime import datetime, timedelta
import importlib
import sys

import discord
from discord.ext import commands

from database import cooldowns
from resources import emojis, settings, strings


class DevOldCog(commands.Cog):
    """Cog class containing internal dev commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dev(self, ctx: commands.Context) -> None:
        """Dev command group"""
        if ctx.prefix.lower() == 'rpg ': return
        if ctx.author.id not in settings.DEV_IDS: return
        subcommands = ''
        for command in self.bot.walk_commands():
            if isinstance(command, commands.Group):
                if command.qualified_name == 'dev':
                    for subcommand in command.walk_commands():
                        if subcommand.parents[0] == command:
                            aliases = f'`{subcommand.qualified_name}`'
                            for alias in subcommand.aliases:
                                aliases = f'{aliases}, `{alias}`'
                            subcommands = f'{subcommands}{emojis.BP} {aliases}\n'
        await ctx.reply(f'Available dev commands:\n{subcommands}')

    @dev.group(name='event-reduction', aliases=('er',), invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dev_event_reduction(self, ctx: commands.Context, *args: str) -> None:
        """Sets event reductions of activities"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        if ctx.author.id not in settings.DEV_IDS: return
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{ctx.prefix}{ctx.command.qualified_name} [activity] [reduction in %]')
        activity_list = 'Possible activities:'
        for activity in strings.ACTIVITIES_WITH_COOLDOWN:
            activity_list = f'{activity_list}\n{emojis.BP} `{activity}`'
        if not args or len(args) != 2:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            message = 'Current event reductions:'
            for cooldown in all_cooldowns:
                cooldown_message = (
                    f'{emojis.BP} {cooldown.activity}: {cooldown.event_reduction}% '
                    f'({cooldown.actual_cooldown():,}s)'
                )
                message = f'{message}\n**{cooldown_message}**' if cooldown.event_reduction > 0 else f'{message}\n{cooldown_message}'
            message = f'{message}\n\n{syntax}'
            await ctx.reply(message)
            return
        activity = args[0].lower()
        reduction = args[1].lower().replace('%','')
        try:
            reduction = float(reduction)
        except:
            try:
                reduction = float(activity)
                activity = args[1]
            except:
                await ctx.reply(f'{syntax}\n\n{activity_list}')
                return
        if not 0 <= reduction <= 99:
            await ctx.reply(f'**{ctx.author.name}**, a reduction of **{reduction}%** doesn\'t make much sense, does it.')
            return
        if activity in strings.ACTIVITIES_ALIASES:
            activity = strings.ACTIVITIES_ALIASES[activity]
        if activity not in strings.ACTIVITIES_WITH_COOLDOWN:
            await ctx.reply(f'**{ctx.author.name}**, couldn\'t find activity `{activity}`.')
            return
        await ctx.reply(
            f'**{ctx.author.name}**, this will change the event reduction of activity `{activity}` to '
            f'**{reduction}%**. Continue? [`yes/no`]'
        )
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if not answer.content.lower() in ['yes','y']:
            await ctx.send('Aborted')
            return
        cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
        await cooldown.update(event_reduction=reduction)
        if cooldown.event_reduction == reduction:
            await ctx.reply(
                f'Changed event reduction for activity `{cooldown.activity}` to **{cooldown.event_reduction}%**.'
            )

    @dev.group(name='post-message', aliases=('pm',), invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def post_message(self, ctx: commands.Context, message_id: int, channel_id: int, *embed_title: str) -> None:
        """Post an embed to a channel"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        if ctx.author.id not in settings.DEV_IDS: return
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(
            syntax=f'{ctx.prefix}{ctx.command.qualified_name} [embed title] [content message ID] [target channel ID]'
        )
        await self.bot.wait_until_ready()
        try:
            message = await ctx.channel.fetch_message(message_id)
        except:
            await ctx.reply(
                f'No message with that ID found.\n'
                f'Command syntax is `{syntax}`\n'
                f'Note that the message needs to be in **this** channel.'
            )
            return
        try:
            channel = await self.bot.fetch_channel(channel_id)
        except:
            await ctx.reply(
                f'No channel with that ID found.\n'
                f'Command syntax is `{syntax}`'
            )
            return
        embed_title_str = " ".join(embed_title)
        if len(embed_title_str) > 256:
            await ctx.reply(
                f'Embed title can\'t be longer than 256 characters.\n'
                f'Command syntax is `{syntax}`'
            )
            return


        embed = discord.Embed(
            title = embed_title_str,
            description = message.content
        )

        await ctx.reply(
            f'Sending the following embed to the channel `{channel.name}`. Proceed? [`yes/no`]',
            embed = embed
        )
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if not answer.content.lower() in ['yes','y']:
            await ctx.send('Aborted')
            return
        await channel.send(embed=embed)
        await ctx.send('Message sent.')

    @dev_event_reduction.command(name='reset')
    @commands.bot_has_permissions(send_messages=True)
    async def dev_event_reduction_reset(self, ctx: commands.Context) -> None:
        """Resets event reductions of all activities"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        if ctx.author.id not in settings.DEV_IDS: return
        if ctx.prefix.lower() == 'rpg ': return
        await ctx.reply(
            f'**{ctx.author.name}**, this will change **all** event reductions to **0.0%**. Continue? [`yes/no`]'
        )
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        if not answer.content.lower() in ['yes','y']:
            await ctx.send('Aborted')
            return
        all_cooldowns = await cooldowns.get_all_cooldowns()
        for cooldown in all_cooldowns:
            await cooldown.update(event_reduction=0.0)
        await ctx.reply(f'All event reductions have been reset.')

    @dev.command(name='cooldown-setup', aliases=('cd-setup',))
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def cooldown_setup(self, ctx: commands.Context, *args: str) -> None:
        """Sets base cooldowns of all activities"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        if ctx.author.id not in settings.DEV_IDS: return
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{ctx.prefix}{ctx.command.qualified_name} [activity] [seconds]')
        activity_list = 'Possible activities:'
        for activity in strings.ACTIVITIES_WITH_COOLDOWN:
            activity_list = f'{activity_list}\n{emojis.BP} `{activity}`'
        if not args or len(args) != 2:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            message = 'Current base cooldowns:'
            for cooldown in all_cooldowns:
                message = f'{message}\n{emojis.BP} {cooldown.activity}: {cooldown.base_cooldown:,}s'
            message = f'{message}\n\n{syntax}'
            await ctx.reply(message)
            return
        activity = args[0].lower()
        new_cooldown = args[1]
        if new_cooldown.isnumeric():
            new_cooldown = int(new_cooldown)
        else:
            if activity.isnumeric():
                new_cooldown = int(activity)
                activity = args[1]
        if activity in strings.ACTIVITIES_ALIASES:
            activity = strings.ACTIVITIES_ALIASES[activity]
        if activity not in strings.ACTIVITIES_WITH_COOLDOWN:
            await ctx.reply(f'**{ctx.author.name}**, couldn\'t find activity `{activity}`.')
            return
        await ctx.reply(
            f'**{ctx.author.name}**, this will change the base cooldown (before donor reduction) of activity '
            f'`{activity}` to **{new_cooldown:,}** seconds. Continue? [`yes/no`]'
        )
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        if not answer.content.lower() in ['yes','y']:
            await ctx.send('Aborted')
            return
        cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
        await cooldown.update(cooldown=new_cooldown)
        if cooldown.base_cooldown == new_cooldown:
            await ctx.reply(
                f'Changed base cooldown for activity `{cooldown.activity}` to '
                f'**{cooldown.base_cooldown:,}s**.'
            )
        else:
            await ctx.reply(strings.MSG_ERROR)

    @dev.command()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def shutdown(self, ctx: commands.Context) -> None:
        """Shut down the bot"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        if ctx.author.id not in settings.DEV_IDS: return
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        await ctx.reply(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`')
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        if answer.content.lower() in ['yes','y']:
            await ctx.send('Shutting down.')
            await self.bot.close()
        else:
            await ctx.send('Phew, was afraid there for a second.')

    @dev.command(aliases=('unload','reload',))
    @commands.bot_has_permissions(send_messages=True)
    async def load(self, ctx: commands.Context, *args: str) -> None:
        """Loads/unloads cogs and reloads cogs or modules"""
        if ctx.author.id not in settings.DEV_IDS: return
        action = ctx.invoked_with
        message_syntax = f'The syntax is `{ctx.prefix}dev {action} [name(s)]`'
        if ctx.prefix.lower() == 'rpg ': return
        if not args:
            await ctx.send(message_syntax)
            return
        args = [arg.lower() for arg in args]
        actions = []
        for mod_or_cog in args:
            name_found = False
            if not 'cogs.' in mod_or_cog:
                cog_name = f'cogs.{mod_or_cog}'
            try:
                if action == 'load':
                    cog_status = self.bot.load_extension(cog_name)
                elif action == 'reload':
                    cog_status = self.bot.reload_extension(cog_name)
                else:
                    cog_status = self.bot.unload_extension(cog_name)
            except:
                cog_status = 'Error'
            if cog_status is None:
                actions.append(f'+ Extension \'{cog_name}\' {action}ed.')
                name_found = True
            if not name_found:
                if action == 'reload':
                    for module_name in sys.modules.copy():
                        if mod_or_cog == module_name:
                            module = sys.modules.get(module_name)
                            if module is not None:
                                importlib.reload(module)
                                actions.append(f'+ Module \'{module_name}\' reloaded.')
                                name_found = True
            if not name_found:
                if action == 'reload':
                    actions.append(f'- No cog with the name \'{mod_or_cog}\' found or cog not loaded.')
                else:
                    actions.append(f'- No cog with the name \'{mod_or_cog}\' found or cog already {action}ed.')

        message = ''
        for action in actions:
            message = f'{message}\n{action}'
        await ctx.send(f'```diff\n{message}\n```')

    # Test command
    @dev.command()
    @commands.bot_has_permissions(send_messages=True)
    async def test_guild(self, ctx: commands.Context) -> None:
        if ctx.author.id not in settings.DEV_IDS: return
        from database import clans, reminders, users
        from resources import exceptions
        current_time = datetime.utcnow().replace(microsecond=0)
        user = ctx.author
        user_settings = await users.get_user(user.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_clan_name(user_settings.clan_name)
            await clan.update(quest_user_id=user.id)
            if clan.alert_enabled:
                try:
                    clan_reminder: reminders.Reminder = (
                        await reminders.get_clan_reminder(clan.clan_name)
                    )
                except exceptions.NoDataFoundError:
                    clan_reminder = None
            if clan_reminder is not None:
                for member_id in clan.member_ids:
                    if member_id == user.id: continue
                    try:
                        user_clan_reminder: reminders.Reminder = (
                            await reminders.get_user_reminder(member_id, 'guild')
                        )
                        user_reminder_time_left = user_clan_reminder.end_time - current_time
                        clan_reminder_time_left = clan_reminder.end_time - current_time
                        range_upper = clan_reminder_time_left + timedelta(seconds=2)
                        range_lower = clan_reminder_time_left - timedelta(seconds=2)
                        if not range_lower <= user_reminder_time_left <= range_upper:
                            new_end_time = current_time + (clan_reminder_time_left + timedelta(minutes=5))
                            await user_clan_reminder.update(end_time=new_end_time)
                    except exceptions.NoDataFoundError:
                        continue
        except exceptions.NoDataFoundError:
            pass

    # Another test command
    @dev.command()
    @commands.bot_has_permissions(send_messages=True)
    async def test(self, ctx: commands.Context) -> None:
        if ctx.author.id not in settings.DEV_IDS: return
        test_list = []
        for x in range(1,60):
            test_list.append(x)
        if len(test_list) > 50:
            test_list = test_list[-50:]
        pass

    @dev.command()
    @commands.bot_has_permissions(send_messages=True)
    async def cache(self, ctx: commands.Context) -> None:
        """Shows cache size"""
        if ctx.author.id not in settings.DEV_IDS: return
        from cache import messages
        cache_size = sys.getsizeof(messages._MESSAGE_CACHE)
        channel_count = len(messages._MESSAGE_CACHE)
        message_count = 0
        for channel_messages in messages._MESSAGE_CACHE.values():
            message_count += len(channel_messages)
            cache_size += sys.getsizeof(channel_messages)
            for message in channel_messages:
                cache_size += sys.getsizeof(message)
        await ctx.reply(
            f'Cache size: {cache_size / 1024:,.2f} KB\n'
            f'Channel count: {channel_count:,}\n'
            f'Message count: {message_count:,}\n'
        )

    @dev.command()
    @commands.bot_has_permissions(send_messages=True)
    async def migrate_messages(self, ctx: commands.Context) -> None:
        """Migrates the hunt message of all users to include drop_emoji IF they didn't change it"""
        if ctx.author.id not in settings.DEV_IDS: return
        from database import users
        all_user_settings = await users.get_all_users()
        for user_settings in all_user_settings:
            if user_settings.alert_hunt.message == strings.DEFAULT_MESSAGE:
                await user_settings.update(alert_hunt_message=strings.DEFAULT_MESSAGES['hunt'])
        await ctx.reply('Done')

def setup(bot):
    bot.add_cog(DevOldCog(bot))