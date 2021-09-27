# dev.py
"""Internal dev commands"""

import asyncio
import importlib
import inspect
import os
import sys
from datetime import datetime
from math import ceil, floor

import discord
from discord.ext import commands

# Allow importing modules from parent directory
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import database
import emojis
import global_data
import global_functions


class DevCog(commands.Cog):
    """Cog class containing internal dev commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def dev(self, ctx, *args):
        """Dev command group"""
        subcommands = ''
        for command in self.bot.walk_commands():
            if isinstance(command, commands.Group):
                if command.qualified_name == 'dev':
                    for subcommand in command.walk_commands():
                        if subcommand.parents[0] == command:
                            aliases = f'`{subcommand.qualified_name}`'
                            for alias in subcommand.aliases:
                                aliases = f'{aliases}, `{alias}`'
                            subcommands = f'{subcommands}{emojis.bp} {aliases}\n'
        await ctx.reply(
            f'Available dev commands:\n'
            f'{subcommands}',
            mention_author=False
            )

    @dev.command(aliases=('ts',))
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def timestring(self, ctx, *args):
        """calculate time left from a timestamp"""
        error_syntax = f'It\'s `{ctx.prefix}timestring [timestamp]`, you dummy.'
        if args:
            timestamp = args[0]
            if timestamp.isnumeric():
                try:
                    timestamp = float(timestamp)
                    current_time = datetime.utcnow().replace(microsecond=0)
                    end_time_datetime = datetime.fromtimestamp(timestamp)
                    end_time_difference = end_time_datetime - current_time
                    time_left = end_time_difference.total_seconds()
                    timestring = await global_functions.parse_seconds(time_left)
                    await ctx.reply(f'That is **{timestring}** from now.', mention_author=False)
                except:
                    await ctx.reply(f'That really didn\'t calculate to anything useful.', mention_author=False)
                    return
            else:
                await ctx.reply(error_syntax, mention_author=False)
        else:
            await ctx.reply(error_syntax, mention_author=False)

    @dev.command(name='event-reduction', aliases=('er',))
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def event_reduction(self, ctx, *args):
        """Sets event reductions of all activities"""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if not prefix.lower() == 'rpg ':
            if not ctx.author.id in (285399610032390146, 619879176316649482):
                await ctx.reply('You are not allowed to use this command.', mention_author=False)
                return

            activity_list = 'Possible activities:'
            for index in range(len(global_data.cooldown_activities)):
                activity_list = f'{activity_list}\n{emojis.bp} `{global_data.cooldown_activities[index]}`'

            if args:
                if len(args) in (1,2):

                    activity_aliases = {
                        'adv': 'adventure',
                        'lb': 'lootbox',
                        'tr': 'training',
                        'chop': 'work',
                        'farming': 'farm',
                        'fish': 'work',
                        'mine': 'work',
                        'pickup': 'work',
                        'axe': 'work',
                        'net': 'work',
                        'pickaxe': 'work',
                        'ladder': 'work',
                        'boat': 'work',
                        'bowsaw': 'work',
                        'drill': 'work',
                        'tractor': 'work',
                        'chainsaw': 'work',
                        'bigboat': 'work',
                        'dynamite': 'work',
                        'greenhouse': 'work',
                        'mb': 'miniboss'
                    }

                    activity = args[0]
                    activity = activity.lower()
                    action = ctx.invoked_with

                    if activity == 'reset':
                        await ctx.reply(f'**{ctx.author.name}**, this will change **all** event reductions to **0.0%**. Continue? [`yes/no`]', mention_author=False)
                        try:
                            answer = await self.bot.wait_for('message', check=check, timeout=30)
                            if not answer.content.lower() in ['yes','y']:
                                await ctx.send('Aborted')
                                return
                        except asyncio.TimeoutError as error:
                            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

                        status = await database.set_event_reduction(ctx, 'all', 0.0)
                        await ctx.reply(status, mention_author=False)
                        return

                    if len(args) == 2:
                        reduction = args[1]
                        reduction = reduction.replace('%','')
                        try:
                            reduction = float(reduction)
                        except:
                            try:
                                reduction = float(activity)
                                activity = args[1]
                            except:
                                await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.command.qualified_name} [activity] [reduction in %]`.\n\n{activity_list}', mention_author=False)
                                return

                        if not 0 <= reduction <= 99:
                            await ctx.reply(f'**{ctx.author.name}**, a reduction of **{reduction}%** doesn\'t make much sense, does it.', mention_author=False)
                            return

                        if activity in activity_aliases:
                            activity = activity_aliases[activity]

                        if activity in global_data.cooldown_activities:
                            await ctx.reply(f'**{ctx.author.name}**, this will change the event reduction of activity **{activity}** to **{reduction}%**. Continue? [`yes/no`]', mention_author=False)
                            try:
                                answer = await self.bot.wait_for('message', check=check, timeout=30)
                                if not answer.content.lower() in ['yes','y']:
                                    await ctx.send('Aborted')
                                    return
                            except asyncio.TimeoutError as error:
                                await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

                            status = await database.set_event_reduction(ctx, activity, reduction)
                            await ctx.reply(status, mention_author=False)

                    else:
                        cooldown_data = await database.get_cooldowns(ctx)
                        message = 'Current event reductions:'
                        for cd in cooldown_data:
                            cooldown = cd[1]
                            reduction = cd[2]
                            cooldown = int(ceil(cooldown*((100-reduction)/100)))
                            if not reduction == 0:
                                message = f'{message}\n{emojis.bp} **{cd[0]}: {reduction}% ({cooldown:,}s)**'
                            else:
                                message = f'{message}\n{emojis.bp} {cd[0]}: {reduction}% ({cooldown:,}s)'

                        message = f'{message}\n\nUse `{ctx.prefix}{ctx.command.qualified_name} [activity] [reduction in %]` to change an event reduction.'
                        await ctx.reply(message, mention_author=False)
                else:
                    await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.command.qualified_name} [activity] [reduction in %]`.\n\n{activity_list}', mention_author=False)
                    return
            else:
                cooldown_data = await database.get_cooldowns(ctx)
                message = 'Current event reductions:'
                for cd in cooldown_data:
                    cooldown = cd[1]
                    reduction = cd[2]
                    cooldown = int(ceil(cooldown*((100-reduction)/100)))
                    if not reduction == 0:
                        message = f'{message}\n{emojis.bp} **{cd[0]}: {reduction}% ({cooldown:,}s)**'
                    else:
                        message = f'{message}\n{emojis.bp} {cd[0]}: {reduction}% ({cooldown:,}s)'

                message = f'{message}\n\nUse `{ctx.prefix}{ctx.command.qualified_name} [activity] [reduction in %]` to change a cooldown.'
                await ctx.reply(message, mention_author=False)

    @dev.command(name='cooldown-setup', aliases=('cd-setup',))
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def cooldown_setup(self, ctx, *args):
        """Sets cooldowns of all activities"""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if not prefix.lower() == 'rpg ':
            if not ctx.author.id in (285399610032390146, 619879176316649482):
                await ctx.reply('You are not allowed to use this command.', mention_author=False)
                return
            activity_list = 'Possible activities:'
            for index in range(len(global_data.cooldown_activities)):
                activity_list = f'{activity_list}\n{emojis.bp} `{global_data.cooldown_activities[index]}`'

            if args:
                if len(args) in (1,2):

                    activity_aliases = {
                        'adv': 'adventure',
                        'lb': 'lootbox',
                        'tr': 'training',
                        'chop': 'work',
                        'farming': 'farm',
                        'fish': 'work',
                        'mine': 'work',
                        'pickup': 'work',
                        'axe': 'work',
                        'net': 'work',
                        'pickaxe': 'work',
                        'ladder': 'work',
                        'boat': 'work',
                        'bowsaw': 'work',
                        'drill': 'work',
                        'tractor': 'work',
                        'chainsaw': 'work',
                        'bigboat': 'work',
                        'dynamite': 'work',
                        'greenhouse': 'work',
                        'mb': 'miniboss'
                    }

                    activity = args[0]
                    activity = activity.lower()

                    action = ctx.invoked_with

                    if len(args) == 2:
                        seconds = args[1]
                        if seconds.isnumeric():
                            seconds = int(seconds)
                        else:
                            if activity.isnumeric():
                                seconds = int(activity)
                                activity = args[1]

                        if activity in activity_aliases:
                            activity = activity_aliases[activity]

                        if activity in global_data.cooldown_activities:
                            await ctx.reply(f'**{ctx.author.name}**, this will change the base cooldown (before donor reduction!) of activity **{activity}** to **{seconds:,}** seconds. Continue? [`yes/no`]', mention_author=False)
                            try:
                                answer = await self.bot.wait_for('message', check=check, timeout=30)
                                if not answer.content.lower() in ['yes','y']:
                                    await ctx.send('Aborted')
                                    return
                            except asyncio.TimeoutError as error:
                                await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

                            status = await database.set_cooldown(ctx, activity, seconds)
                            await ctx.reply(status, mention_author=False)

                    else:
                        cooldown_data = await database.get_cooldowns(ctx)
                        message = 'Current cooldowns:'
                        for cd in cooldown_data:
                            message = f'{message}\n{emojis.bp} {cd[0]}: {cd[1]:,}s'

                        message = f'{message}\n\nUse `{ctx.prefix}{ctx.invoked_with} [activity] [seconds]` to change a cooldown.'
                        await ctx.reply(message, mention_author=False)
                else:
                    await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity] [seconds]`.\n\n{activity_list}', mention_author=False)
                    return
            else:
                cooldown_data = await database.get_cooldowns(ctx)
                message = 'Current cooldowns:'
                for cd in cooldown_data:
                    message = f'{message}\n{emojis.bp} {cd[0]}: {cd[1]:,}s'

                message = f'{message}\n\nUse `{ctx.prefix}{ctx.command.qualified_name} [activity] [seconds]` to change a cooldown.'
                await ctx.reply(message, mention_author=False)

    @dev.command()
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def sleepy(self, ctx, arg):
        """Sleepy potion test command"""

        prefix = ctx.prefix

        if arg:
            try:
                arg = int(arg)
            except:
                await ctx.send(f'Syntax: `{prefix}sleepy [seconds]`')
                return
            status = await global_functions.reduce_reminder_time(ctx, arg)
            await ctx.send(status)
        else:
            await ctx.send(f'Syntax: `{prefix}sleepy [seconds]`')
            return

    @dev.command()
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def shutdown(self, ctx):
        """Shut down the bot"""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if not prefix.lower() == 'rpg ':
            try:
                await ctx.reply(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`', mention_author=False)
                answer = await self.bot.wait_for('message', check=check, timeout=30)
                if answer.content.lower() in ['yes','y']:
                    await ctx.send(f'Shutting down.')
                    await ctx.bot.logout()
                else:
                    await ctx.send(f'Phew, was afraid there for a second.')
            except asyncio.TimeoutError as error:
                await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

    @dev.command(name='eval')
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def evaluate(self, ctx):
        """Basic eval command with await support"""
        message_prefix_command = f'{ctx.prefix}{ctx.command.qualified_name} '
        eval_command_start = (ctx.message.content.find(message_prefix_command)
                              + len(message_prefix_command))
        eval_command = ctx.message.content[eval_command_start:]
        try:
            if eval_command.startswith('await '):
                eval_command = eval_command[6:]
                result = await eval(eval_command)
            else:
                result = eval(eval_command)
            if result is None:
                await ctx.send('No return value')
            else:
                await ctx.send(result)
        except Exception as error:
            await ctx.send(error)

    @dev.command()
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def reload(self, ctx, *args):
        """Reloads modules or cogs"""
        if args:
            actions = []
            arg = args[0].lower()
            if arg in ('lib','libs','modules','module'):
                importlib.reload(database)
                actions.append(f'Module \'database\' reloaded.')
                importlib.reload(emojis)
                actions.append(f'Module \'emojis\' reloaded.')
                importlib.reload(global_data)
                actions.append(f'Module \'global_data\' reloaded.')
                importlib.reload(global_functions)
                actions.append(f'Module \'global_functions\' reloaded.')
            else:
                for arg in args:
                    cog_name = f'cogs.{arg}'
                    try:
                        result = self.bot.reload_extension(cog_name)
                        if result is None:
                            actions.append(f'Extension \'{cog_name}\' reloaded.')
                        else:
                            actions.append(f'{cog_name}: {result}')
                    except Exception as error:
                        actions.append(f'{cog_name}: {error}')
            message = ''
            for action in actions:
                message = f'{message}\n{action}'
            await ctx.send(message)
        else:
            await ctx.send('Uhm, what.')

    # Enable/disable commands
    @dev.command(aliases=('disable',))
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def enable(self, ctx, *args):
        action = ctx.invoked_with
        if args:
            command = ''
            for arg in args:
                command = f'{command} {arg}'
            command = self.bot.get_command(command)
            if command is None:
                await ctx.reply(
                    'No command with that name found.',
                    mention_author=False
                    )
            elif ctx.command == command:
                await ctx.reply(
                    f'You can not {action} this command.',
                    mention_author=False
                    )
            else:
                if action == 'enable':
                    command.enabled = True
                else:
                    command.enabled = False
                await ctx.reply(
                    f'Command {command.qualified_name} {action}d.',
                    mention_author=False
                    )
        else:
            await ctx.reply(
                f'Syntax is `{ctx.prefix}{ctx.command} [command]`',
                mention_author=False
                )


def setup(bot):
    bot.add_cog(DevCog(bot))