# settings_user.py
"""Contains user settings commands"""

from datetime import datetime, timedelta
from typing import List, Optional, Union

import discord
from discord.ext import commands

from content import settings as settings_cmd
from database import clans, reminders, users
from resources import emojis, functions, exceptions, settings, strings, views


# -- Commands ---
async def command_list(
    bot: discord.Bot,
    ctx: Union[commands.Context, discord.ApplicationContext, discord.Message],
    user: Optional[discord.User] = None
) -> None:
    """Lists all active reminders"""
    user = user if user is not None else ctx.author
    try:
        user_settings: users.User = await users.get_user(user.id)
    except exceptions.FirstTimeUserError:
        if user == ctx.author:
            raise
        else:
            await functions.reply_or_respond(ctx, 'This user is not registered with this bot.', True)
        return
    try:
        custom_reminders = list(await reminders.get_active_user_reminders(user.id, 'custom'))
    except exceptions.NoDataFoundError:
        custom_reminders = []
    try:
        user_reminders = list(await reminders.get_active_user_reminders(user.id))
    except:
        user_reminders = []
    clan_reminders = []
    if user_settings.clan_name is not None:
        try:
            clan_reminders = list(await reminders.get_active_clan_reminders(user_settings.clan_name))
        except:
            pass
    embed = await embed_reminders_list(bot, user, user_reminders, clan_reminders)
    view = views.RemindersListView(bot, ctx, user, user_reminders, clan_reminders, custom_reminders, embed_reminders_list)
    if isinstance(ctx, discord.ApplicationContext):
        interaction_message = await ctx.respond(embed=embed, view=view)
    else:
        interaction_message = await ctx.reply(embed=embed, view=view)
    view.interaction_message = interaction_message
    await view.wait()


async def command_ready(
    bot: discord.Bot,
    ctx: Union[commands.Context, discord.ApplicationContext, discord.Message],
    user: Optional[discord.User] = None
) -> None:
    """Lists all commands that are ready to use"""
    channel_permissions = ctx.channel.permissions_for(ctx.guild.me)
    if not channel_permissions.view_channel or not channel_permissions.send_messages or not channel_permissions.embed_links:
        return
    async def get_command_from_activity(activity:str) -> str:
        if activity == 'dungeon-miniboss':
            command_dungeon = await functions.get_slash_command(user_settings, 'dungeon', False)
            command_miniboss = await functions.get_slash_command(user_settings, 'miniboss', False)
            command = (
                f"{command_dungeon} or {command_miniboss}"
            )
        elif activity == 'epic':
            command_use = await functions.get_slash_command(user_settings, 'use', False)
            command_options = 'item: <EPIC item>' if user_settings.slash_mentions_enabled else '<EPIC item>'
            command = f"{command_use} `{command_options}`"
        elif activity == 'guild':
            command = clan_command
        elif activity == 'quest':
            command = await functions.get_slash_command(user_settings, user_settings.last_quest_command, False)
            if command is None: command = await functions.get_slash_command(user_settings, 'quest', False)
        elif activity == 'training':
            command = await functions.get_slash_command(user_settings, user_settings.last_training_command, False)
            if command is None: command = await functions.get_slash_command(user_settings, 'training', False)
        elif activity == 'work':
            command = await functions.get_slash_command(user_settings, user_settings.last_work_command, False)
            if command is None: command = '`work command`'
        elif activity == 'pets':
            if user_settings.ready_pets_claim_active:
                command = await functions.get_slash_command(user_settings, 'pets claim', False)
            else:
                command = await functions.get_slash_command(user_settings, 'pets adventure', False)
        elif activity == 'custom':
            command = '`custom reminder`'
        elif activity == 'unstuck':
            command = '`chimney unstuck lol`'
        else:
            command = await functions.get_slash_command(user_settings, strings.ACTIVITIES_SLASH_COMMANDS[activity], False)
        if activity == 'lootbox':
            lootbox_name = '[lootbox]' if user_settings.last_lootbox == '' else f'{user_settings.last_lootbox} lootbox'
            if user_settings.slash_mentions_enabled:
                command = f"{command} `item: {lootbox_name}`"
            else:
                command = f"{command} `{lootbox_name}`"
        elif activity == 'adventure' and user_settings.last_adventure_mode != '':
            if user_settings.slash_mentions_enabled:
                command = f"{command} `mode: {user_settings.last_adventure_mode}`"
            else:
                command = f"{command} `{user_settings.last_adventure_mode}`"
        elif activity == 'hunt' and user_settings.last_hunt_mode != '':
            if user_settings.slash_mentions_enabled:
                command = f"{command} `mode: {user_settings.last_hunt_mode}`"
            else:
                command = f"{command} `{user_settings.last_hunt_mode}`"
        elif activity == 'farm' and user_settings.last_farm_seed != '':
            if user_settings.slash_mentions_enabled:
                command = f"{command} `seed: {user_settings.last_farm_seed}`"
            else:
                command = f"{command} `{user_settings.last_farm_seed}`"
        return command.replace('` `', ' ')

    if isinstance(ctx, discord.Message):
        message = ctx
        auto_ready = True
    else:
        message = ctx.message
        auto_ready = False
    user = user if user is not None else ctx.author
    try:
        user_settings: users.User = await users.get_user(user.id)
    except exceptions.FirstTimeUserError:
        if user == ctx.author:
            raise
        else:
            await functions.reply_or_respond(ctx, 'This user is not registered with this bot.', True)
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
    clan_alert_visible = getattr(clan, 'alert_visible', False)
    if clan_alert_enabled and clan_alert_visible:
        if clan.stealth_current >= clan.stealth_threshold:
            clan_command = await functions.get_slash_command(user_settings, 'guild raid', False)
        else:
            clan_command = await functions.get_slash_command(user_settings, 'guild upgrade', False)
    else:
        command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade', False)
        command_raid = await functions.get_slash_command(user_settings, 'guild raid', False)
        clan_command = f"{command_upgrade} or {command_raid}"
    ready_command_activities = list(strings.ACTIVITIES_COMMANDS[:])
    ready_event_activities = list(strings.ACTIVITIES_EVENTS[:])
    active_pet_reminders = False
    for reminder in user_reminders:
        if reminder.activity in ready_command_activities:
            ready_command_activities.remove(reminder.activity)
        elif reminder.activity in ready_event_activities:
            ready_event_activities.remove(reminder.activity)
        elif 'pets' in reminder.activity:
            active_pet_reminders = True
    if not active_pet_reminders or user_settings.ready_pets_claim_active:
        ready_command_activities.append('pets')
    current_time = datetime.utcnow().replace(microsecond=0)
    if 'hunt' in ready_command_activities and user_settings.partner_hunt_end_time > current_time:
        ready_command_activities.remove('hunt')
    if 'farm' in ready_command_activities and not user_settings.ascended and user_settings.current_area in [1,2,3]:
        ready_command_activities.remove('farm')
    if 'training' in ready_command_activities and not user_settings.ascended and user_settings.current_area == 1:
        ready_command_activities.remove('training')
    for activity in ready_command_activities.copy():
        alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
        if not alert_settings.enabled:
            ready_command_activities.remove(activity)
    for activity in ready_event_activities.copy():
        alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
        if not alert_settings.enabled:
            ready_event_activities.remove(activity)

    field_other = ''
    if user_settings.cmd_cd_visible:
        field_other = (
            f'{field_other}\n'
            f'{emojis.BP} {strings.SLASH_COMMANDS["cd"]}'
        )
    if user_settings.cmd_inventory_visible:
        field_other = (
            f'{field_other}\n'
            f'{emojis.BP} {strings.SLASH_COMMANDS["inventory"]}'
        )
    if user_settings.cmd_ready_visible:
        field_other = (
            f'{field_other}\n'
            f'{emojis.BP} {await functions.get_navi_slash_command(bot, "ready")}'
        )
    if user_settings.cmd_slashboard_visible:
        field_other = (
            f'{field_other}\n'
            f'{emojis.BP} {await functions.get_navi_slash_command(bot, "slashboard")}'
        )
    embed = discord.Embed(
        color = int(f'0x{user_settings.ready_embed_color}', 16),
        title = f'{user.name}\'S READY'.upper()
    )
    answer = f'**{user.name}\'S READY**'.upper()
    if user_settings.ready_other_on_top and field_other != '':
        embed.add_field(name='OTHER', value=field_other.strip(), inline=False)
        answer = (
            f'{answer}\n'
            f'**OTHER**\n'
            f'{field_other.strip()}'
        )
    ready_commands = []
    if ready_command_activities:
        field_ready_commands = ''
        for activity in ready_command_activities.copy():
            alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
            if not alert_settings.visible: continue
            command = await get_command_from_activity(activity)
            ready_commands.append(command)
        for command in sorted(ready_commands):
            field_ready_commands = (
                f'{field_ready_commands}\n'
                f'{emojis.BP} {command}'
            )
            if 'pets adventure' in command:
                command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.DETAIL} _Use {command_pets_list} to update reminders._'
                )
        if field_ready_commands != '':
            answer = (
                f'{answer}\n'
                f'**COMMANDS**\n'
                f'{field_ready_commands.strip()}'
            )
            embed.add_field(name='COMMANDS', value=field_ready_commands.strip(), inline=False)
    if ready_event_activities:
        field_ready_events = ''
        ready_events = []
        for activity in ready_event_activities.copy():
            alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[activity])
            if not alert_settings.visible:
                ready_event_activities.remove(activity)
                continue
            if (activity == 'big-arena' and user_settings.alert_arena.enabled
                and not 'arena' in ready_command_activities):
                    ready_event_activities.remove(activity)
                    continue
            elif (activity == 'horse-race' and user_settings.alert_horse_breed.enabled
                  and not 'horse' in ready_command_activities):
                ready_event_activities.remove(activity)
                continue
            elif (activity == "minintboss" and user_settings.alert_dungeon_miniboss.enabled
                  and not 'dungeon-miniboss' in ready_command_activities):
                ready_event_activities.remove(activity)
                continue
            else:
                command = await functions.get_slash_command(user_settings, strings.ACTIVITIES_SLASH_COMMANDS[activity],
                                                            False)
                ready_events.append(command.replace(' join', ''))
        for event in sorted(ready_events):
            field_ready_events = (
                f'{field_ready_events}\n'
                f'{emojis.BP} {event}'
            )
        if field_ready_events != '':
            answer = (
                f'{answer}\n'
                f'**EVENTS**\n'
                f'{field_ready_events.strip()}'
            )
            embed.add_field(name='EVENTS', value=field_ready_events.strip(), inline=False)
    clan_alert_enabled = getattr(clan, 'alert_enabled', False)
    if not clan_reminder and clan_alert_enabled:
        field_ready_clan = (
            f"{emojis.BP} {clan_command}\n"
            f"{emojis.DETAIL} <#{clan.channel_id}>"
        )
        answer = (
            f'{answer}\n'
            f'**GUILD CHANNEL**\n'
            f'{field_ready_clan}'
        )
        embed.add_field(name='GUILD CHANNEL', value=field_ready_clan)
    if not ready_commands and not ready_event_activities and (clan_reminder or not clan_alert_enabled):
        answer = (
            f'{answer}\n'
            f'**COMMANDS**\n'
            f'{emojis.BP} All done!'
        )
        embed.add_field(name='COMMANDS', value=f'{emojis.BP} All done!', inline=False)
    if not user_settings.ready_other_on_top and field_other != '':
        embed.add_field(name='OTHER', value=field_other.strip(), inline=False)
        answer = (
            f'{answer}\n'
            f'**OTHER**\n'
            f'{field_other.strip()}'
        )
    if user_settings.ready_up_next_visible:
        try:
            active_reminders = await reminders.get_active_user_reminders(user.id)
        except exceptions.NoDataFoundError:
            active_reminders = []
        if active_reminders:
            field_up_next = ''
            current_time = datetime.utcnow().replace(microsecond=0)
            for reminder in active_reminders:
                if 'pets' in reminder.activity: continue
                if user_settings.ready_up_next_as_timestamp:
                    local_time_difference = datetime.now().replace(microsecond=0) - current_time
                    end_time = reminder.end_time + local_time_difference
                    up_next_time = f'<t:{int(end_time.timestamp())}:R>'
                else:
                    time_left = reminder.end_time - current_time
                    timestring = await functions.parse_timedelta_to_timestring(time_left)
                    up_next_time = f'in **{timestring}**'
                command = await get_command_from_activity(reminder.activity)
                field_up_next = (
                    f'{field_up_next}\n'
                    f'{emojis.BP} {command} {up_next_time}'
                )
                break
            if field_up_next.strip() != '':
                embed.add_field(name='UP NEXT', value=field_up_next.strip(), inline=False)
                answer = (
                    f'{answer}\n'
                    f'**UP NEXT**\n'
                    f'{field_up_next.strip()}'
                )
    if auto_ready:
        embed.set_footer(text=f"See '/ready' if you want to disable this message.")
        if user_settings.ready_as_embed:
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(answer)
    else:
        view = views.AutoReadyView(ctx, user, user_settings)
        if isinstance(ctx, discord.ApplicationContext):
            if user_settings.ready_as_embed:
                interaction_message = await ctx.respond(embed=embed, view=view)
            else:
                interaction_message = await ctx.respond(answer, view=view)
        else:
            if user_settings.ready_as_embed:
                interaction_message = await ctx.reply(embed=embed, view=view)
            else:
                interaction_message = await ctx.reply(answer, view=view)
        view.interaction_message = interaction_message
        await view.wait()
        if view.value == 'show_settings':
            await settings_cmd.command_settings_ready(bot, ctx)
            await functions.edit_interaction(interaction_message, view=None)


# -- Embeds ---
async def embed_reminders_list(bot: discord.Bot, user: discord.User, user_reminders: List[reminders.Reminder],
                               clan_reminders = List[reminders.Reminder],
                               show_timestamps: Optional[bool] = False) -> discord.Embed:
    """Embed with active reminders"""
    current_time = datetime.utcnow().replace(microsecond=0)
    local_time_difference = datetime.now().replace(microsecond=0) - current_time
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
        title = f'{user.name}\'S REMINDERS'.upper()
    )
    if not user_reminders and not clan_reminders:
        embed.description = f'{emojis.BP} You have no active reminders'
    if reminders_commands_list:
        field_command_reminders = ''
        for reminder in reminders_commands_list:
            if show_timestamps:
                end_time = reminder.end_time + local_time_difference
                flag = 'T' if end_time.day == current_time.day else 'f'
                reminder_time = f'<t:{int(end_time.timestamp())}:{flag}>'
            else:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                reminder_time = f'**{timestring}**'
            if reminder.activity == 'dungeon-miniboss':
                activity = 'Dungeon / Miniboss'
            elif reminder.activity == 'epic':
                activity = 'EPIC items'
            else:
                activity = reminder.activity
            activity = activity.replace('-',' ').capitalize()
            field_command_reminders = (
                f'{field_command_reminders}\n'
                f'{emojis.BP} **`{activity}`** ({reminder_time})'
            )
        embed.add_field(name='COMMANDS', value=field_command_reminders.strip(), inline=False)
    if reminders_events_list:
        field_event_reminders = ''
        for reminder in reminders_events_list:
            if show_timestamps:
                end_time = reminder.end_time + local_time_difference
                flag = 'T' if end_time.day == current_time.day else 'f'
                reminder_time = f'<t:{int(end_time.timestamp())}:{flag}>'
            else:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                reminder_time = f'**{timestring}**'
            activity = reminder.activity.replace('-',' ').capitalize()
            field_event_reminders = (
                f'{field_event_reminders}\n'
                f'{emojis.BP} **`{activity}`** ({reminder_time})'
            )
        embed.add_field(name='EVENTS', value=field_event_reminders.strip(), inline=False)
    if clan_reminders:
        reminder = clan_reminders[0]
        clan: clans.Clan = await clans.get_clan_by_clan_name(reminder.clan_name)
        if clan.quest_user_id is not None:
            if clan.quest_user_id != user.id: time_left = time_left + timedelta(minutes=5)
        if show_timestamps:
            end_time = reminder.end_time + local_time_difference
            flag = 'T' if end_time.day == current_time.day else 'f'
            reminder_time = f'<t:{int(end_time.timestamp())}:{flag}>'
        else:
            time_left = reminder.end_time - current_time
            timestring = await functions.parse_timedelta_to_timestring(time_left)
            reminder_time = f'**{timestring}**'
        field_value = f'{emojis.BP} **`{reminder.clan_name}`** ({reminder_time})'
        if clan.quest_user_id == user.id: field_value = f'{field_value} (quest active)'
        embed.add_field(name='GUILD CHANNEL', value=field_value)
    if reminders_pets_list:
        field_no = 1
        pet_fields = {field_no: ''}
        for time_left_seconds, pet_ids in field_pets_list.items():
            if show_timestamps:
                end_time = current_time + timedelta(seconds=time_left_seconds) + local_time_difference
                flag = 'T' if end_time.day == current_time.day else 'f'
                reminder_time = f'<t:{int(end_time.timestamp())}:{flag}>'
            else:
                timestring = await functions.parse_timedelta_to_timestring(timedelta(seconds=time_left_seconds))
                reminder_time = f'**{timestring}**'
            if ',' in pet_ids:
                pet_message = f'{emojis.BP} **`Pets {pet_ids}`** ({reminder_time})'
            else:
                pet_message = f'{emojis.BP} **`Pet {pet_ids}`** ({reminder_time})'
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
            if show_timestamps:
                end_time = reminder.end_time + local_time_difference
                flag = 'T' if end_time.day == current_time.day else 'f'
                reminder_time = f'<t:{int(end_time.timestamp())}:{flag}>'
            else:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                reminder_time = f'**{timestring}**'
            custom_id = f'0{reminder.custom_id}' if reminder.custom_id <= 9 else reminder.custom_id
            field_custom_reminders = (
                f'{field_custom_reminders}\n'
                f'{emojis.BP} **`{custom_id}`** ({reminder_time}) - {reminder.message}'
            )
        embed.add_field(name='CUSTOM', value=field_custom_reminders.strip(), inline=False)
    return embed