# settings_user.py
"""Contains user settings commands"""

import asyncio
from datetime import datetime, timedelta
import re
from typing import Optional, Union

import discord
from discord.ext import commands

from database import clans, guilds, reminders, users
from resources import emojis, functions, exceptions, settings, strings, views


class SettingsUserCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('me',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings(self, ctx: commands.Context) -> None:
        """Returns current user progress settings"""
        if ctx.prefix.lower() == 'rpg ': return
        embed = await embed_user_settings(self.bot, ctx)
        await ctx.reply(embed=embed)

    @commands.command(name='list', aliases=('cd','cooldowns', 'cooldown'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def list_reminders(self, ctx: commands.Context, *args: str) -> None:
        """Lists all active reminders"""
        if ctx.prefix.lower() == 'rpg ': return
        if ctx.message.mentions:
            user_id = ctx.message.mentions[0].id
        elif args:
            arg = args[0].lower().replace('<@!','').replace('<@','').replace('>','')
            if arg.isnumeric():
                try:
                    user_id = int(arg)
                except:
                    user_id = ctx.author.id
            else:
                user_id = ctx.author.id
        else:
            user_id = ctx.author.id
        user_discord = await functions.get_discord_user(self.bot, user_id)
        if user_discord is None:
            await ctx.reply('This user doesn\'t exist.')
            return
        if user_discord.bot:
            await ctx.reply('Imagine trying to check the reminders of a bot.')
            return
        try:
            user: users.User = await users.get_user(user_discord.id)
        except exceptions.FirstTimeUserError:
            if user_discord == ctx.author:
                raise
            else:
                await ctx.reply('This user is not registered with this bot.')
            return
        current_time = datetime.utcnow().replace(microsecond=0)
        try:
            user_reminders = await reminders.get_active_user_reminders(user.user_id)
        except:
            user_reminders = ()
        clan_reminders = ()
        if user.clan_name is not None:
            try:
                clan_reminders = await reminders.get_active_clan_reminders(user.clan_name)
            except:
                pass
        reminders_commands_list = []
        reminders_events_list = []
        reminders_pets_list = []
        reminders_custom_list = []
        for reminder in user_reminders:
            if 'pets' in reminder.activity:
                reminders_pets_list.append(reminder)
            elif reminder.activity == 'custom':
                reminders_custom_list.append(reminder)
            elif reminder.activity in strings.ACTIVITIES_EVENTS:
                reminders_events_list.append(reminder)
            else:
                reminders_commands_list.append(reminder)

        # Sort pets with same time left together
        if reminders_pets_list:
            counter = -1
            field_pets_list = {}
            for index, reminder in enumerate(reminders_pets_list):
                reminder_last = reminders_pets_list[index-1] if index != 0 else None
                pet_id = reminder.activity.replace('pets-','')
                time_left = reminder.end_time - current_time
                if reminder_last is None:
                    field_pets_list[time_left.total_seconds()] = pet_id
                    counter += 1
                    continue
                if reminder_last.end_time == reminder.end_time:
                    last_pet_id = field_pets_list[time_left.total_seconds()]
                    field_pets_list[time_left.total_seconds()] = f'{last_pet_id}, {pet_id}'
                else:
                    field_pets_list[time_left.total_seconds()] = pet_id
                    counter += 1

        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = f'{user_discord.name}\'S REMINDERS'.upper()
        )
        if not user_reminders and not clan_reminders:
            embed.description = f'{emojis.BP} You have no active reminders'
        if reminders_commands_list:
            field_command_reminders = ''
            for reminder in reminders_commands_list:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                activity = 'Dungeon / Miniboss' if reminder.activity == 'dungeon-miniboss' else reminder.activity
                activity = activity.replace('-',' ').capitalize()
                field_command_reminders = (
                    f'{field_command_reminders}\n'
                    f'{emojis.BP} **`{activity}`** (**{timestring}**)'
                )
            embed.add_field(name='COMMANDS', value=field_command_reminders.strip(), inline=False)
        if reminders_events_list:
            field_event_reminders = ''
            for reminder in reminders_events_list:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                activity = reminder.activity.replace('-',' ').capitalize()
                field_event_reminders = (
                    f'{field_event_reminders}\n'
                    f'{emojis.BP} **`{activity}`** (**{timestring}**)'
                )
            embed.add_field(name='EVENTS', value=field_event_reminders.strip(), inline=False)
        if clan_reminders:
            reminder = clan_reminders[0]
            time_left = reminder.end_time - current_time
            clan: clans.Clan = await clans.get_clan_by_clan_name(reminder.clan_name)
            if clan.quest_user_id is not None:
                if clan.quest_user_id != user_id: time_left = time_left + timedelta(minutes=5)
            timestring = await functions.parse_timedelta_to_timestring(time_left)
            field_value = f'{emojis.BP} **`{reminder.clan_name}`** (**{timestring}**)'
            if clan.quest_user_id == user_id: field_value = f'{field_value} (quest active)'
            embed.add_field(name='GUILD CHANNEL', value=field_value)
        if reminders_pets_list:
            field_no = 1
            pet_fields = {field_no: ''}
            for time_left_seconds, pet_ids in field_pets_list.items():
                timestring = await functions.parse_timedelta_to_timestring(timedelta(seconds=time_left_seconds))
                if ',' in pet_ids:
                    pet_message = f'{emojis.BP} **`Pets {pet_ids}`** (**{timestring}**)'
                else:
                    pet_message = f'{emojis.BP} **`Pet {pet_ids}`** (**{timestring}**)'
                if len(pet_fields[field_no]) + len(pet_message) > 1020:
                    field_no += 1
                    pet_fields[field_no] = ''
                pet_fields[field_no] = f'{pet_fields[field_no]}\n{pet_message}'
            for field_no, pet_field in pet_fields.items():
                field_name = f'PETS {field_no}' if field_no > 1 else 'PETS'
                embed.add_field(name=field_name, value=pet_field.strip(), inline=False)
        if reminders_custom_list:
            field_custom_reminders = ''
            for reminder in reminders_custom_list:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                custom_id = f'0{reminder.custom_id}' if reminder.custom_id <= 9 else reminder.custom_id
                field_custom_reminders = (
                    f'{field_custom_reminders}\n'
                    f'{emojis.BP} **`{custom_id}`** (**{timestring}**) - {reminder.message}'
                )
            embed.add_field(name='CUSTOM', value=field_custom_reminders.strip(), inline=False)
        await ctx.reply(embed=embed)

    @commands.command(aliases=('rd',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def ready(
        self, ctx: Union[commands.Context, discord.Message], *args: str, user: Optional[discord.User] = None
    ) -> None:
        """Lists all commands that are ready to use"""
        if isinstance(ctx, commands.Context):
            if ctx.prefix.lower() == 'rpg ': return
            message = ctx.message
            auto_ready = False
        else:
            message = ctx
            auto_ready = True
        user = user if user is not None else message.author
        if message.mentions:
            user_id = message.mentions[0].id
        elif args:
            arg = args[0].lower().replace('<@!','').replace('<@','').replace('>','')
            if arg.isnumeric():
                try:
                    user_id = int(arg)
                except:
                    user_id = user.id
            else:
                user_id = user.id
        else:
            user_id = user.id
        user_discord = await functions.get_discord_user(self.bot, user_id)
        if user_discord is None:
            await message.reply('This user doesn\'t exist.')
            return
        if user_discord.bot:
            await message.reply('Imagine trying to check the commands of a bot.')
            return
        try:
            user_settings: users.User = await users.get_user(user_discord.id)
        except exceptions.FirstTimeUserError:
            if user_discord == message.author:
                raise
            else:
                await message.reply('This user is not registered with this bot.')
            return
        try:
            user_reminders = await reminders.get_active_user_reminders(user_settings.user_id)
        except exceptions.NoDataFoundError:
            user_reminders = []
        clan_reminder = []
        clan = None
        if user_settings.clan_name is not None:
            try:
                clan: clans.Clan = await clans.get_clan_by_clan_name(user_settings.clan_name)
                clan_reminder = await reminders.get_active_clan_reminders(user_settings.clan_name)
            except exceptions.NoDataFoundError:
                pass
        clan_alert_enabled = getattr(clan, 'alert_enabled', False)
        if clan_alert_enabled:
            if clan.stealth_current >= clan.stealth_threshold:
                clan_command = await functions.get_slash_command(user_settings, 'guild raid')
            else:
                clan_command = await functions.get_slash_command(user_settings, 'guild upgrade')
        else:
            command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
            clan_command = f"{command_upgrade} or {command_raid}"
        ready_command_activities = list(strings.ACTIVITIES_COMMANDS[:])
        ready_event_activities = list(strings.ACTIVITIES_EVENTS[:])
        for reminder in user_reminders:
            if reminder.activity in ready_command_activities:
                ready_command_activities.remove(reminder.activity)
            elif reminder.activity in ready_event_activities:
                ready_event_activities.remove(reminder.activity)
        for activity in ready_command_activities.copy():
            alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
            if not alert_settings.enabled:
                ready_command_activities.remove(activity)
        for activity in ready_event_activities.copy():
            alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
            if not alert_settings.enabled:
                ready_event_activities.remove(activity)

        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = f'{user_discord.name}\'S READY'.upper()
        )
        if ready_command_activities:
            field_ready_commands = ''
            ready_commands = []
            for activity in ready_command_activities:
                if activity == 'dungeon-miniboss':
                    command_dungeon = await functions.get_slash_command(user_settings, 'dungeon')
                    command_miniboss = await functions.get_slash_command(user_settings, 'miniboss')
                    command = (
                        f"{command_dungeon} or {command_miniboss}"
                    )
                elif activity == 'guild':
                    command = clan_command
                elif activity == 'quest':
                    command = await functions.get_slash_command(user_settings, user_settings.last_quest_command)
                    if command is None: command = await functions.get_slash_command(user_settings, 'quest')
                elif activity == 'training':
                    command = await functions.get_slash_command(user_settings, user_settings.last_training_command)
                    if command is None: command = await functions.get_slash_command(user_settings, 'training')
                elif activity == 'work':
                    command = await functions.get_slash_command(user_settings, user_settings.last_work_command)
                    if command is None: command = 'work command'
                else:
                    command = await functions.get_slash_command(user_settings, strings.ACTIVITIES_SLASH_COMMANDS[activity])
                if activity == 'lootbox':
                    lootbox_name = '[lootbox]' if user_settings.last_lootbox == '' else f'{user_settings.last_lootbox} lootbox'
                    command = f'{command} `item: {lootbox_name}`'
                elif activity == 'adventure' and user_settings.last_adventure_mode != '':
                    command = f'{command} `mode: {user_settings.last_adventure_mode}`'
                elif activity == 'hunt' and user_settings.last_hunt_mode != '':
                    command = f'{command} `mode: {user_settings.last_hunt_mode}`'
                elif activity == 'farm' and user_settings.last_farm_seed != '':
                    command = f'{command} `seed: {user_settings.last_farm_seed}`'
                ready_commands.append(command)
            for command in sorted(ready_commands):
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.BP} {command}'
                )
            if field_ready_commands != '':
                embed.add_field(name='COMMANDS', value=field_ready_commands.strip(), inline=False)
        if ready_event_activities:
            field_ready_events = ''
            ready_events = []
            for activity in ready_event_activities:
                if activity == 'big-arena' and not 'arena' in ready_command_activities:
                    continue
                elif activity == 'horse-race' and not 'horse' in ready_command_activities:
                    continue
                elif activity == "minintboss" and not 'dungeon-miniboss' in ready_command_activities:
                    continue
                else:
                    command = await functions.get_slash_command(user_settings, strings.ACTIVITIES_SLASH_COMMANDS[activity])
                    ready_events.append(command)
            for event in sorted(ready_events):
                field_ready_events = (
                    f'{field_ready_events}\n'
                    f'{emojis.BP} {event}'
                )
            if field_ready_events != '':
                embed.add_field(name='EVENTS', value=field_ready_events.strip(), inline=False)
        clan_alert_enabled = getattr(clan, 'alert_enabled', False)
        if not clan_reminder and clan_alert_enabled:
            field_ready_clan = f"{emojis.BP} {clan_command}"
            embed.add_field(name='GUILD CHANNEL', value=field_ready_clan)
        if not embed.fields: embed.description = f'{emojis.BP} All done!'
        if auto_ready:
            prefix = await guilds.get_prefix(message)
            embed.set_footer(text=f"See '{prefix}rd' if you want to disable this message.")
            await message.channel.send(embed=embed)
        else:
            view = views.AutoReadyView(user, user_settings)
            interaction_message = await message.reply(embed=embed, view=view)
            view.message = interaction_message
            await view.wait()
            if view.value == 'timeout':
                try:
                    await interaction_message.edit(view=None)
                except discord.errors.NotFound:
                    pass


    @commands.command(aliases=('start',))
    @commands.bot_has_permissions(send_messages=True)
    async def on(self, ctx: commands.Context) -> None:
        """Enables reminders (main activation)"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        first_time_user = False
        try:
            user: users.User = await users.get_user(ctx.author.id)
            if user.bot_enabled:
                await ctx.reply(f'**{ctx.author.name}**, I\'m already turned on.')
                return
        except exceptions.FirstTimeUserError:
            user = await users.insert_user(ctx.author.id)
            first_time_user = True
        if not user.bot_enabled: await user.update(bot_enabled=True)
        if not user.bot_enabled:
            await ctx.reply(strings.MSG_ERROR)
            return
        if not first_time_user:
            welcome_message = (
            f'Hey! **{ctx.author.name}**! Welcome back!'
        )
        else:
            welcome_message = (
                f'Hey! **{ctx.author.name}**! Hello! I\'m now turned on!\n\n'
                f'**Donor tier**\n'
                f'You can set your EPIC RPG donor tier with `{prefix}donor` and - if you are married - '
                f'the donor tier of your partner with `{prefix}partner donor`.\n\n'
                f'**Settings**\n'
                f'Use `{prefix}me` to see all of your settings.\n\n'
                f'**Command tracking**\n'
                f'Please note that I track the amount of some EPIC RPG commands you use. Check `{ctx.prefix}stats` to '
                f'see what commands are tracked.\n'
                f'__No personal data is processed or stored in any way.__\n'
                f'If you want to opt-out of command tracking, please use `{ctx.prefix}tracking off`.\n\n'
                f'To read more about what data is processed and why, feel free to check the privacy policy found in '
                f'`{ctx.prefix}info`.'
            )
        await ctx.reply(welcome_message)


    @commands.command(aliases=('stop',))
    @commands.bot_has_permissions(send_messages=True)
    async def off(self, ctx: commands.Context) -> None:
        """Disables reminders (main deactivation)"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        if not user.bot_enabled:
            await ctx.reply(f'**{ctx.author.name}**, I\'m already turned off.')
            return
        await ctx.reply(
            f'**{ctx.author.name}**, turning me off will turn off all helpers, the stats tracking'
            f', and delete all of your active reminders. If you only want to turn off your reminders, consider using '
            f'`{ctx.prefix}disable all` instead.\n'
            f'Are you sure? `[yes/no]`'
        )
        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30)
            if answer.content.lower() not in ['yes','y']:
                await ctx.send('Aborted.')
                return
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        await user.update(bot_enabled=False)
        if user.bot_enabled:
            await ctx.reply(strings.MSG_ERROR)
            return
        try:
            active_reminders = await reminders.get_active_user_reminders(ctx.author.id)
            for reminder in active_reminders:
                await reminder.delete()
        except exceptions.NoDataFoundError:
            pass
        await ctx.reply(
            f'**{ctx.author.name}**, I\'m now turned off.\n'
            f'All active reminders were deleted.'
        )

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def dnd(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables dnd mode"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}dnd [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles DND mode. If DND mode is on, I will not ping you on when I send a reminder.\n'
                f'Note that this does not apply to guild reminders.\n\n'
                f'{syntax}'
            )
            return
        if args:
            action = args[0].lower()
            if action in ('on', 'enable', 'start'):
                enabled = True
                action = 'enabled'
            elif action in ('off', 'disable', 'stop'):
                enabled = False
                action = 'disabled'
            else:
                await ctx.reply(syntax)
                return
            if user_settings.dnd_mode_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, DND mode is already {action}.'
                )
                return
            await user_settings.update(dnd_mode_enabled=enabled)
            if user_settings.dnd_mode_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, DND mode is now **{action}**.'
                )
            else:
                await ctx.reply(strings.MSG_ERROR)

    @commands.command(name='slash-mentions', aliases=('slash-mention',))
    @commands.bot_has_permissions(send_messages=True)
    async def slash_mentions(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables slash mentions"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}slash-mentions [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles slash mentions in reminders. If this is on, Navi will send clickable / tappable '
                f'command links (example: </chainsaw:959162697398763590>).\n'
                f'Make sure that you use the placeholder \u007bcommand\u007d in your messages to see them.\n\n'
                f'Note that this feature is not officially released by Discord and does **not** work on mobile yet!\n\n'
                f'{syntax}'
            )
            return
        if args:
            action = args[0].lower()
            if action in ('on', 'enable', 'start'):
                enabled = True
                action = 'enabled'
            elif action in ('off', 'disable', 'stop'):
                enabled = False
                action = 'disabled'
            else:
                await ctx.reply(syntax)
                return
            if user_settings.slash_mentions_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, slash mentions are already {action}.'
                )
                return
            await user_settings.update(slash_mentions_enabled=enabled)
            if user_settings.slash_mentions_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, slash mentions are now **{action}**.'
                )
            else:
                await ctx.reply(strings.MSG_ERROR)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def reactions(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables Navi reactions"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}reactions [on|off]')
        if not args:
            await ctx.reply(
                f'This command enables/disables all message reactions. Why would you ever turn them off tho?\n'
                f'{syntax}'
            )
        if args:
            action = args[0].lower()
            if action in ('on', 'enable', 'start'):
                enabled = True
                action = 'enabled'
            elif action in ('off', 'disable', 'stop'):
                enabled = False
                action = 'disabled'
            else:
                await ctx.reply(syntax)
                return

            if user_settings.reactions_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reactions are already {action}.'
                )
                return
            await user_settings.update(reactions_enabled=enabled)
            if user_settings.reactions_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reactions are now **{action}**.'
                )
            else:
                await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('donator',))
    @commands.bot_has_permissions(send_messages=True)
    async def donor(self, ctx: commands.Context, *args: str) -> None:
        """Sets user donor tier"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        msg_syntax = strings.MSG_SYNTAX.format(syntax=f'`{prefix}donor [tier]`')
        possible_tiers = f'Possible tiers:'
        for index, donor_tier in enumerate(strings.DONOR_TIERS):
            possible_tiers = f'{possible_tiers}\n{emojis.BP}`{index}` : {donor_tier}'
        if not args:
            await ctx.reply(
                f'**{ctx.author.name}**, your current EPIC RPG donor tier is **{user_settings.user_donor_tier}** '
                f'({strings.DONOR_TIERS[user_settings.user_donor_tier]}).\n'
                f'If you want to change this, use `{prefix}{ctx.invoked_with} [tier]`.\n\n{possible_tiers}'
            )
            return
        if args:
            try:
                donor_tier = int(args[0])
            except:
                await ctx.reply(f'{msg_syntax}\n\n{possible_tiers}')
                return
            if donor_tier > len(strings.DONOR_TIERS) - 1 or donor_tier < 0:
                await ctx.reply(f'{msg_syntax}\n\n{possible_tiers}')
                return
            await user_settings.update(user_donor_tier=donor_tier)
            await ctx.reply(
                f'**{ctx.author.name}**, your EPIC RPG donor tier is now set to **{user_settings.user_donor_tier}** '
                f'({strings.DONOR_TIERS[user_settings.user_donor_tier]}).\n'
                f'Please note that the `hunt together` cooldown can only be accurately calculated if '
                f'`{prefix}partner donor [tier]` is set correctly as well.'
            )

    @commands.command(name='ping-mode', aliases=('pingmode',))
    @commands.bot_has_permissions(send_messages=True)
    async def ping_mode(self, ctx: commands.Context, *args: str) -> None:
        """Sets user ping mode"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        syntax = strings.MSG_SYNTAX.format(syntax=f'`{prefix}ping-mode [before | after]`')
        if not args:
            await ctx.reply(
                f'This command controls whether I will ping you before or after the reminder message.\n'
                f'{syntax}\n\n'
                f'Note that this setting has no effect if DND mode is turned on.'
            )
            return
        setting = args[0].lower()
        if setting in ('before', 'front', 'first', 'start'):
            enabled = False
            setting = 'before'
        elif setting in ('after', 'back', 'last', 'end'):
            enabled = True
            setting = 'after'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.ping_after_message == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, I\'m already set to ping you **{setting}** the reminder message.'
            )
            return
        await user_settings.update(ping_after_message=enabled)
        if user_settings.ping_after_message == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, I\'m now set to ping you **{setting}** the reminder message.\n'
                f'Note that this setting has no effect if DND mode is turned on.'
            )
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(name='hunt-rotation', aliases=('huntrotation','huntrotate','hunt-rotate','huntswitch','hunt-switch'))
    @commands.bot_has_permissions(send_messages=True)
    async def hunt_rotation(self, ctx: commands.Context, *args: str) -> None:
        """Sets hunt rotation"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        syntax = strings.MSG_SYNTAX.format(syntax=f'`{prefix}hunt-rotation [on | off]`')
        if not args:
            await ctx.reply(
                f'This enables the following behaviour:\n'
                f'{emojis.BP} Your hunt reminder rotates between `hunt together` and `hunt`.\n'
                f'{emojis.BP} The hunt reminder ignores your partner\'s donor setting.\n\n'
                f'This is meant for donors married to non-donors who want to optimize their hunt usage.\n'
                f'Example: If you are a SUPER donor and your partner is a non-donor, this will give you a hunt '
                f'reminder every 39s with every second one being `hunt together`. This means you will hunt every 39s, '
                f'and your partner will be taken hunting every 1m18s.\n\n'
                f'Note that hardmode mode does not work if you enable hunt rotation.\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        user_settings: users.User = await users.get_user(ctx.author.id)
        if user_settings.hunt_rotation_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, hunt rotation is already {action}.'
            )
            return
        await user_settings.update(hunt_rotation_enabled=enabled)
        if user_settings.hunt_rotation_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, hunt rotation is now **{action}**.'
            )
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('disable',))
    @commands.bot_has_permissions(send_messages=True)
    async def enable(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables specific reminders"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user_settings: users.User = await users.get_user(ctx.author.id)
        action = ctx.invoked_with.lower()
        enabled = True if action == 'enable' else False
        helper_action = 'on' if enabled else 'off'
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{action} [activity]')
        possible_activities = 'Possible activities:'
        for activity in strings.ACTIVITIES_ALL:
            possible_activities = f'{possible_activities}\n{emojis.BP} `{activity}`'
        if not args:
            await ctx.reply(
                f'This command enables/disables specific reminders.\n'
                f'{syntax}\n\n'
                f'{possible_activities}'
            )
            await ctx.reply(f'{syntax}\n\n{possible_activities}')
            return
        helper_check = ''.join(args).lower()
        if 'heal' in helper_check:
            await self.heal(ctx, helper_action)
            return
        if 'training' in helper_check and 'helper' in helper_check:
            await self.trhelper(ctx, helper_action)
            return
        if 'ruby' in helper_check:
            await self.ruby(ctx, helper_action)
            return
        if 'pet' in helper_check and 'helper' in helper_check:
            await self.pethelper(ctx, helper_action)
            return
        if 'track' in helper_check:
            await self.tracking(ctx, helper_action)
            return
        if 'reaction' in helper_check:
            await self.reactions(ctx, helper_action)
            return
        if 'dnd' in helper_check:
            await self.dnd(ctx, helper_action)
            return
        if 'hardmode' in helper_check:
            await self.hardmode(ctx, helper_action)
            return
        if args[0].lower() == 'all':
            if not enabled:
                try:
                    await ctx.reply(
                        f'**{ctx.author.name}**, turning off all reminders will delete all of your active reminders. '
                        f'Are you sure? `[yes/no]`'
                    )
                    answer = await self.bot.wait_for('message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                    return
                if answer.content.lower() not in ['yes','y']:
                    await ctx.send('Aborted')
                    return
            args = strings.ACTIVITIES
        updated_activities = []
        ignored_activites = []
        answer = ''
        for activity in args:
            if activity in strings.ACTIVITIES_ALIASES: activity = strings.ACTIVITIES_ALIASES[activity]
            updated_activities.append(activity) if activity in strings.ACTIVITIES else ignored_activites.append(activity)
        if updated_activities:
            kwargs = {}
            answer = f'{action.capitalize()}d reminders for the following activities:'
            for activity in updated_activities:
                kwargs[f'{strings.ACTIVITIES_COLUMNS[activity]}_enabled'] = enabled
                answer = f'{answer}\n{emojis.BP}`{activity}`'
                if not enabled:
                    if activity == 'pets':
                        try:
                            all_reminders = await reminders.get_active_user_reminders(ctx.author.id)
                            for reminder in all_reminders:
                                if 'pets' in reminder.activity: await reminder.delete()
                        except:
                            pass
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(ctx.author.id, activity)
                        await reminder.delete()
                    except exceptions.NoDataFoundError:
                        pass
            await user_settings.update(**kwargs)
        if ignored_activites:
            answer = f'{answer}\n\nCouldn\'t find the following activites:'
            for activity in ignored_activites:
                answer = f'{answer}\n{emojis.BP}`{activity}`'
        await ctx.reply(answer)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def message(self, ctx: commands.Context, *args: str) -> None:
        """Change specific reminder messages"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        if ctx.message.mentions:
            for user in ctx.message.mentions:
                if user != ctx.author:
                    await ctx.reply('Please don\'t.')
                    return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}message [activity] [message]')
        possible_activities = '**Possible activities**'
        for activity in strings.ACTIVITIES:
            possible_activities = f'{possible_activities}\n{emojis.BP} `{activity}`'
        syntax_message = (
            f'This command changes the reminder messages Navi sends.\n\n'
            f'**Syntax**\n'
            f'{emojis.BP} Use `{prefix}message [activity] [message]` to change a message.\n'
            f'{emojis.BP} Use `{prefix}message [activity]` to view a current message.\n'
            f'{emojis.BP} Use `{prefix}message [activity] reset` to reset a message to the default one.\n'
            f'{emojis.BP} Use `{prefix}message list` to view **all** current messages.\n'
            f'{emojis.BP} Use `{prefix}message reset` to reset **all** messages to the default one.\n\n'
            f'**Placeholders**\n'
            f'{emojis.BP} You can use placeholders in curly brackets such as \u007bcommand\u007d.\n'
            f'{emojis.BP} Check the default messages to see which placeholders you can use.\n\n'
            f'**Emojis**\n'
            f'{emojis.BP} You can use all emojis from this server + all default emojis.\n\n'
            f'{possible_activities}'
        )
        if not args:
            await ctx.reply(syntax_message)
            return
        activity = args[0].lower()
        if activity in ('reset','default'):
            await ctx.reply(
                f'**{ctx.author.name}**, this will reset **all** messages to the default one. '
                f'Are you sure? `[yes/no]`'
            )
            try:
                answer = await self.bot.wait_for('message', check=check, timeout=30)
                if answer.content.lower() not in ['yes','y']:
                    await ctx.send('Aborted.')
                    return
            except asyncio.TimeoutError:
                await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                return
            kwargs = {}
            for activity in strings.ACTIVITIES:
                activity_column = strings.ACTIVITIES_COLUMNS[activity]
                kwargs[f'{activity_column}_message'] = strings.DEFAULT_MESSAGES[activity]
            await user_settings.update(**kwargs)
            await ctx.reply(
                f'Changed all messages back to the default message.\n\n'
                f'Note that running reminders do not update automatically.'
            )
            return
        if activity == 'list':
            embed = await embed_message_settings(ctx, user_settings)
            await ctx.reply(embed=embed)
            return
        if activity in strings.ACTIVITIES_ALIASES: activity = strings.ACTIVITIES_ALIASES[activity]
        if activity not in strings.ACTIVITIES:
            await ctx.reply(
                f'I don\'t know an activity called `{activity}`.\n'
                f'{syntax}\n\n'
                f'{possible_activities}'
            )
            return
        activity_column = strings.ACTIVITIES_COLUMNS[activity]
        alert = getattr(user_settings, activity_column)
        if len(args) == 1:
            await ctx.reply(
                f'Current message for activity `{activity}`:'
                f'\n{emojis.BP} {alert.message}\n\n'
                f'Use `{prefix}message {activity} [message]` to change it.'
            )
            return
        if len(args) > 1:
            args = list(args)
            args.pop(0)
            new_message = " ".join(args)
            if new_message.lower() in ('reset','default'): new_message = strings.DEFAULT_MESSAGES[activity]
            if len(new_message) > 1024:
                await ctx.reply('This is a command to set a new message, not to write a novel :thinking:')
                return
            for placeholder in re.finditer('\{(.+?)\}', new_message):
                placeholder_str = placeholder.group(1)
                if placeholder_str not in strings.DEFAULT_MESSAGES[activity]:
                    allowed_placeholders = ''
                    for placeholder in re.finditer('\{(.+?)\}', strings.DEFAULT_MESSAGES[activity]):
                        allowed_placeholders = (
                            f'{allowed_placeholders}\n'
                            f'{emojis.BP} {{{placeholder.group(1)}}}'
                        )
                    if allowed_placeholders == '':
                        allowed_placeholders = f'There are no placeholders available for this message.'
                    else:
                        allowed_placeholders = (
                            f'Available placeholders for this message:\n'
                            f'{allowed_placeholders.strip()}'
                        )
                    await ctx.reply(
                        f'Invalid placeholder found.\n\n'
                        f'{allowed_placeholders}'
                    )
                    return
            kwargs = {}
            kwargs[f'{activity_column}_message'] = new_message
            await user_settings.update(**kwargs)
            alert = getattr(user_settings, activity_column)
            await ctx.reply(
                f'Changed message for activity `{activity}` to:\n{emojis.BP} {alert.message}\n\n'
                f'Note that running reminders do not update automatically.'
            )

    @commands.command(aliases=('hm',))
    @commands.bot_has_permissions(send_messages=True)
    async def hardmode(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables hardmode mode"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')

        if not args:
            await ctx.reply(
                f'This command toggles hardmode mode. If hardmode mode is on, your partner will be told to hunt solo '
                f'whenever they use `hunt together` so you can hardmode in peace.\n'
                f'Hardmode mode requires the partner to be set and your partner needs to have their partner alert '
                f'channel set.\n\n'
                f'Note that this setting does nothing if you have hunt rotation enabled.\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.partner_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you don\'t have a partner set.\n'
                f'This mode tells your partner to hunt solo, so you need to do that first.\n'
                f'To set a partner, use `{ctx.prefix}partner`.'
            )
            return
        if user_settings.hardmode_mode_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, hardmode mode is already {action}.'
            )
            return
        await user_settings.update(hardmode_mode_enabled=enabled)
        if user_settings.hardmode_mode_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, hardmode mode is now **{action}**.\n'
                f'Please note that your partner will only be properly notified if they have a partner alert channel set.'
            )
            if user_settings.partner_id is not None:
                partner_discord = await functions.get_discord_user(self.bot, user_settings.partner_id)
                partner: users.User = await users.get_user(user_settings.partner_id)
                if partner.partner_channel_id is not None:
                    partner_message = partner_discord.mention if not user_settings.dnd_mode_enabled else f'**{partner_discord.name}**,'
                    partner_message = f'{partner_message} **{ctx.author.name}** just {action} **hardmoding**.'
                    if action == 'enabled':
                        partner_message = (
                            f'{partner_message}\n'
                            f'Please don\'t use `hunt together` until they turn it off. '
                            f'If you want to hardmode too, please activate hardmode mode as well and hunt solo.'
                        )
                    else:
                        partner_message = (
                            f'{partner_message}\n'
                            f'Feel free to use `hunt togethter` again.'
                        )
                    partner_channel = await functions.get_discord_channel(self.bot, partner.partner_channel_id)
                    await partner_channel.send(partner_message)

        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('rubies',))
    @commands.bot_has_permissions(send_messages=True)
    async def ruby(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables ruby counter and shows rubies"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')


        if not args:
            if not user_settings.ruby_counter_enabled:
                await ctx.reply(
                    f'This command toggles the ruby counter. The ruby counter keeps track of your rubies to be able to '
                    f'answer the ruby training question.\n'
                    f'Note that I can only do that if you use commands where I can see them.\n'
                    f'If you used or gained rubies somewhere I couldn\'t see it, open your inventory to correct '
                    f'the count.\n\n'
                    f'{syntax}'
                )
                return
            await ctx.reply(
                f'**{ctx.author.name}**, you have {user_settings.rubies:,} {emojis.RUBY} rubies.'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.ruby_counter_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, the ruby counter is already {action}.'
            )
            return
        await user_settings.update(ruby_counter_enabled=enabled, rubies=0)
        if user_settings.ruby_counter_enabled == enabled:
            answer = f'**{ctx.author.name}**, the ruby counter is now **{action}**.'
            if enabled:
                answer = (
                    f'{answer}\n'
                    f'If your training reminder is turned on, I will automatically tell you your ruby count when '
                    f'the ruby training comes along.\n'
                    f'If you want to manually check your ruby count, use `{prefix}ruby`.'
                )
            await ctx.reply(answer)
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('tr-helper','traininghelper','training-helper'))
    @commands.bot_has_permissions(send_messages=True)
    async def trhelper(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables training helper"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles the training helper. The training helper will tell you the answer to '
                f'training questions.\n'
                f'Note that the ruby question is controlled separately with `{prefix}ruby [on|off]`\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.training_helper_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, the training helper is already {action}.'
            )
            return
        await user_settings.update(training_helper_enabled=enabled)
        if user_settings.training_helper_enabled == enabled:
            answer = f'**{ctx.author.name}**, the training helper is now **{action}**.'
            if enabled:
                answer = (
                    f'{answer}\n'
                    f'If your training reminder is turned on, I will automatically tell you the answer to all '
                    f'training questions.\n'
                    f'Note that the ruby question is controlled separately with `{prefix}ruby [on|off]`.'
                )
            await ctx.reply(answer)
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('pet-helper','pethelp','pet-help'))
    @commands.bot_has_permissions(send_messages=True)
    async def pethelper(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables pet catch helper"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles the pet helper. The pet helper will tell you the recommended commands to use '
                f'when a pet appears.\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.pet_helper_enabled == enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, the pet helper is already {action}.'
            )
            return
        await user_settings.update(pet_helper_enabled=enabled)
        if user_settings.pet_helper_enabled == enabled:
            await ctx.reply(f'**{ctx.author.name}**, the pet helper is now **{action}**.')
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('track',))
    @commands.bot_has_permissions(send_messages=True)
    async def tracking(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables command tracking"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles the command tracking. If it\'s turned on, I will record how often you do certain '
                f'commands\n'
                f'You can use `{prefix}stats` to see your stats.\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.tracking_enabled == enabled:
            await ctx.reply(f'**{ctx.author.name}**, command tracking is already {action}.')
            return
        await user_settings.update(tracking_enabled=enabled)
        if user_settings.tracking_enabled == enabled:
            await ctx.reply(f'**{ctx.author.name}**, command tracking is now **{action}**.')
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('heal-warning','healwarning','heal-warn','healwarn'))
    @commands.bot_has_permissions(send_messages=True)
    async def heal(self, ctx: commands.Context, *args: str) -> None:
        """Enables/disables heal warning"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [on|off]')
        if not args:
            await ctx.reply(
                f'This command toggles the heal warning. The heal warning will try to tell you to heal '
                f'if your HP gets low.\n'
                f'Please note that adventures do higher damage than hunts. '
                f'Always check your HP before doing an adventure regardless.\n\n'
                f'{syntax}'
            )
            return
        action = args[0].lower()
        if action in ('on', 'enable', 'start'):
            enabled = True
            action = 'enabled'
        elif action in ('off', 'disable', 'stop'):
            enabled = False
            action = 'disabled'
        else:
            await ctx.reply(syntax)
            return
        if user_settings.heal_warning_enabled == enabled:
            await ctx.reply(f'**{ctx.author.name}**, the heal warning is already {action}.')
            return
        await user_settings.update(heal_warning_enabled=enabled)
        if user_settings.heal_warning_enabled == enabled:
            answer = f'**{ctx.author.name}**, the heal warning is now **{action}**.'
            await ctx.reply(answer)
        else:
            await ctx.reply(strings.MSG_ERROR)

    @commands.command(aliases=('last-tt','lasttt'))
    @commands.bot_has_permissions(send_messages=True)
    async def last_tt(self, ctx: commands.Context, *args: str) -> None:
        """Updates the time of the last time travel"""
        user_settings: users.User = await users.get_user(ctx.author.id)
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax = strings.MSG_SYNTAX.format(syntax=f'{prefix}{ctx.invoked_with} [message ID / link]')
        msg_syntax = (
            f'{syntax}\n\n'
            f'Use the ID or link of the message that announced your time travel '
            f'("**{ctx.author.name}** traveled in time :cyclone:").\n'
            f'If you don\'t have access to that message anymore, choose another message that is as close '
            f'to your last time travel as possible.\n'
            f'Note that it does not matter if I can actually read the message, I only need the ID or link.'
        )
        if not args:
            await ctx.reply(msg_syntax)
            return
        if 'discord.com/channels' in args[0]:
            message_id_match = re.search(r"\/[0-9]+\/[0-9]+\/(.+?)$", args[0])
            if message_id_match:
                message_id = message_id_match.group(1)
            else:
                await ctx.reply(f'No valid message ID or URL found.\n{syntax}')
                return
        else:
            message_id = args[0]
        try:
            message_id = int(message_id)
            snowflake_binary = f'{message_id:064b}'
            timestamp_binary = snowflake_binary[:42]
            timestamp_decimal = int(timestamp_binary, 2)
            timestamp = (timestamp_decimal + 1_420_070_400_000) / 1000
            tt_time = datetime.utcfromtimestamp(timestamp).replace(microsecond=0)
        except:
            await ctx.reply(f'No valid message ID or URL found.\n{syntax}')
            return
        await user_settings.update(last_tt=tt_time.isoformat(sep=' '))
        if user_settings.last_tt != tt_time:
            await ctx.reply(strings.MSG_ERROR)
            return
        await ctx.reply(
            f'**{ctx.author.name}**, your last time travel time was changed to '
            f'<t:{int(user_settings.last_tt.timestamp())}:f> UTC.'
        )

# Initialization
def setup(bot):
    bot.add_cog(SettingsUserCog(bot))


# --- Embeds ---
async def embed_user_settings(bot: commands.Bot, ctx: commands.Context) -> discord.Embed:
    """User settings embed"""
    async def bool_to_text(boolean: bool):
        return 'Enabled' if boolean else 'Disabled'

    # Get user settings
    user_partner_channel_name = 'N/A'
    user_settings: users.User = await users.get_user(ctx.author.id)
    ping_mode_setting = 'After' if user_settings.ping_after_message else 'Before'
    if user_settings.partner_channel_id is not None:
        user_partner_channel = await functions.get_discord_channel(bot, user_settings.partner_channel_id)
        user_partner_channel_name = user_partner_channel.name

    # Get partner settings
    partner_name = partner_hardmode_status = 'N/A'
    partner_partner_channel_name = 'N/A'
    partner_partner_channel = None
    if user_settings.partner_id is not None:
        partner_settings: users.User = await users.get_user(user_settings.partner_id)
        partner = await functions.get_discord_user(bot, user_settings.partner_id)
        partner_name = f'{partner.name}#{partner.discriminator}'
        partner_hardmode_status = await bool_to_text(partner_settings.hardmode_mode_enabled)
        partner_partner_channel = await functions.get_discord_channel(bot, partner_settings.partner_channel_id)
        if partner_partner_channel is not None: partner_partner_channel_name = partner_partner_channel.name

    # Get clan settings
    clan_name = clan_alert_status = stealth_threshold = clan_channel_name = clan_upgrade_quests = 'N/A'
    try:
        clan_settings: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        clan_name = clan_settings.clan_name
        clan_alert_status = await bool_to_text(clan_settings.alert_enabled)
        clan_upgrade_quests = 'Allowed' if clan_settings.upgrade_quests_enabled else 'Not allowed'
        stealth_threshold = clan_settings.stealth_threshold
        if clan_settings.channel_id is not None:
            clan_channel = await functions.get_discord_channel(bot, clan_settings.channel_id)
            clan_channel_name = clan_channel.name
    except exceptions.NoDataFoundError:
        pass
    try:
        tt_timestamp = int(user_settings.last_tt.timestamp())
    except OSError as error: # Windows throws an error if datetime is set to 0 apparently
        tt_timestamp = 0
    # Fields
    field_user = (
        f'{emojis.BP} Bot: `{await bool_to_text(user_settings.bot_enabled)}`\n'
        f'{emojis.BP} Command tracking: `{await bool_to_text(user_settings.tracking_enabled)}`\n'
        f'{emojis.BP} Donor tier: `{user_settings.user_donor_tier}` '
        f'({strings.DONOR_TIERS[user_settings.user_donor_tier]})\n'
        f'{emojis.BP} DND mode: `{await bool_to_text(user_settings.dnd_mode_enabled)}`\n'
        f'{emojis.BP} Hardmode mode: `{await bool_to_text(user_settings.hardmode_mode_enabled)}`\n'
        f'{emojis.BP} Hunt rotation: `{await bool_to_text(user_settings.hunt_rotation_enabled)}`\n'
        f'{emojis.BP} Ping mode: `{ping_mode_setting}` reminder message\n'
        f'{emojis.BP} Reactions: `{await bool_to_text(user_settings.reactions_enabled)}`\n'
        f'{emojis.BP} Last TT: <t:{tt_timestamp}:f> UTC\n'
        f'{emojis.BP} Partner alert channel:\n{emojis.BLANK} `{user_partner_channel_name}`\n'
    )
    field_helpers = (
        f'{emojis.BP} Heal warning: `{await bool_to_text(user_settings.heal_warning_enabled)}`\n'
        f'{emojis.BP} Pet helper: `{await bool_to_text(user_settings.pet_helper_enabled)}`\n'
        f'{emojis.BP} Ruby counter: `{await bool_to_text(user_settings.ruby_counter_enabled)}`\n'
        f'{emojis.BP} Training helper: `{await bool_to_text(user_settings.training_helper_enabled)}`\n'
    )
    field_partner = (
        f'{emojis.BP} Name: `{partner_name}`\n'
        f'{emojis.BP} Donor tier: `{user_settings.partner_donor_tier}` '
        f'({strings.DONOR_TIERS[user_settings.partner_donor_tier]})\n'
        f'{emojis.BP} Hardmode mode: `{partner_hardmode_status}`\n'
        f'{emojis.BP} Partner alert channel:\n{emojis.BLANK} `{partner_partner_channel_name}`\n'
    )
    field_clan = (
        f'{emojis.BP} Guild name: `{clan_name}`\n'
        f'{emojis.BP} Guild channel reminder: `{clan_alert_status}`\n'
        f'{emojis.BP} Guild channel: `{clan_channel_name}`\n'
        f'{emojis.BP} Stealth threshold: `{stealth_threshold}`\n'
        f'{emojis.BP} Quests below threshold: `{clan_upgrade_quests}`\n'
    )
    field_reminders = (
        f'{emojis.BP} Adventure: `{await bool_to_text(user_settings.alert_adventure.enabled)}`\n'
        f'{emojis.BP} Arena: `{await bool_to_text(user_settings.alert_arena.enabled)}`\n'
        f'{emojis.BP} Daily: `{await bool_to_text(user_settings.alert_daily.enabled)}`\n'
        f'{emojis.BP} Duel: `{await bool_to_text(user_settings.alert_duel.enabled)}`\n'
        f'{emojis.BP} Dungeon / Miniboss: `{await bool_to_text(user_settings.alert_dungeon_miniboss.enabled)}`\n'
        f'{emojis.BP} Farm: `{await bool_to_text(user_settings.alert_farm.enabled)}`\n'
        f'{emojis.BP} Guild: `{await bool_to_text(user_settings.alert_guild.enabled)}`\n'
        f'{emojis.BP} Horse: `{await bool_to_text(user_settings.alert_horse_breed.enabled)}`\n'
        f'{emojis.BP} Hunt: `{await bool_to_text(user_settings.alert_hunt.enabled)}`\n'
        f'{emojis.BP} Lootbox: `{await bool_to_text(user_settings.alert_lootbox.enabled)}`\n'
        f'{emojis.BP} Lottery: `{await bool_to_text(user_settings.alert_lottery.enabled)}`\n'
        f'{emojis.BP} Partner alert: `{await bool_to_text(user_settings.alert_partner.enabled)}`\n'
        f'{emojis.BP} Pets: `{await bool_to_text(user_settings.alert_pets.enabled)}`\n'
        f'{emojis.BP} Quest: `{await bool_to_text(user_settings.alert_quest.enabled)}`\n'
        f'{emojis.BP} Training: `{await bool_to_text(user_settings.alert_training.enabled)}`\n'
        f'{emojis.BP} Vote: `{await bool_to_text(user_settings.alert_vote.enabled)}`\n'
        f'{emojis.BP} Weekly: `{await bool_to_text(user_settings.alert_weekly.enabled)}`\n'
        f'{emojis.BP} Work: `{await bool_to_text(user_settings.alert_work.enabled)}`'
    )
    field_event_reminders = (
        f'{emojis.BP} Big arena: `{await bool_to_text(user_settings.alert_big_arena.enabled)}`\n'
        f'{emojis.BP} Horse race: `{await bool_to_text(user_settings.alert_horse_race.enabled)}`\n'
        f'{emojis.BP} Minin\'tboss: `{await bool_to_text(user_settings.alert_not_so_mini_boss.enabled)}`\n'
        f'{emojis.BP} Pet tournament: `{await bool_to_text(user_settings.alert_pet_tournament.enabled)}`\n'
    )
    field_messages = (
        f'{emojis.BP} To see your reminder messages, use `{ctx.prefix}message list`\n'
    )
    if not user_settings.bot_enabled:
        field_reminders = f'**These settings are ignored because your reminders are off.**\n{field_reminders}'

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name}\'s settings'.upper(),
    )
    embed.add_field(name='USER', value=field_user, inline=True)
    embed.add_field(name='HELPERS', value=field_helpers, inline=True)
    embed.add_field(name='PARTNER', value=field_partner, inline=False)
    embed.add_field(name='GUILD CHANNEL', value=field_clan, inline=False)
    embed.add_field(name='COMMAND REMINDERS', value=field_reminders, inline=True)
    embed.add_field(name='EVENT REMINDERS', value=field_event_reminders, inline=True)
    embed.add_field(name='REMINDER MESSAGES', value=field_messages, inline=False)

    return embed


async def embed_message_settings(ctx: commands.Context, user: users.User) -> discord.Embed:
    """Message settings embed"""

    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name}\'s message settings'.upper(),
    )

    for activity in strings.ACTIVITIES:
        activity_column = strings.ACTIVITIES_COLUMNS[activity]
        alert = getattr(user, activity_column)
        activity = activity.capitalize()
        embed.add_field(name=activity, value=f'{alert.message}', inline=False)
    embed.set_footer(text=f'Use "{ctx.prefix}message [activity] [message]" to change a message.')

    return embed