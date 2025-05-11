# reminders_lists.py
"""Contains reminder list commands"""

from datetime import timedelta
from typing import Optional, Union

import discord
from discord import utils
from discord.ext import bridge, commands

from content import settings as settings_cmd
from database import clans, reminders, users
from database import settings as settings_db
from resources import emojis, functions, exceptions, settings, strings, views


# -- Commands ---
async def command_list(
    bot: bridge.AutoShardedBot,
    ctx: Union[commands.Context, discord.ApplicationContext, discord.Message],
    user: Optional[discord.User] = None
) -> None:
    """Lists all active reminders"""
    if user is not None and user != ctx.author:
        user_mentioned = True
    else:
        user = ctx.author
        user_mentioned = False
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
    embed = await embed_reminders_list(bot, user)
    view = views.RemindersListView(bot, ctx, user, user_settings, user_mentioned, custom_reminders, embed_reminders_list)
    if isinstance(ctx, discord.ApplicationContext):
        interaction_message = await ctx.respond(embed=embed, view=view)
    else:
        interaction_message = await ctx.reply(embed=embed, view=view)
    view.interaction_message = interaction_message
    await view.wait()


async def command_ready(
    bot: bridge.AutoShardedBot,
    ctx: Union[commands.Context, discord.ApplicationContext, discord.Message],
    user: Optional[discord.User] = None
) -> None:
    """Lists all commands that are ready to use"""
    channel_permissions = ctx.channel.permissions_for(ctx.guild.me)
    if not channel_permissions.view_channel or not channel_permissions.send_messages or not channel_permissions.embed_links:
        return
    if isinstance(ctx, discord.Message):
        message = ctx
        auto_ready = True
    else:
        message = ctx.message
        auto_ready = False
    user_mentioned = False
    if not auto_ready:
        if user is not None and user != ctx.author:
            user_mentioned = True
        else:
            user = ctx.author
    try:
        user_settings: users.User = await users.get_user(user.id)
        ready_as_embed = user_settings.ready_as_embed
    except exceptions.FirstTimeUserError:
        await functions.reply_or_respond(ctx, 'This user is not registered with this bot.', True)
    if not auto_ready:
        ctx_author_settings: users.User = await users.get_user(ctx.author.id)
        ready_as_embed = ctx_author_settings.ready_as_embed
    embed, answer = await embed_ready(bot, user, auto_ready)
    if auto_ready:
        if ready_as_embed:
            content = user.mention if user_settings.ready_ping_user else None
            await message.channel.send(content=content, embed=embed)
        else:
            await message.channel.send(answer)
    else:
        if not user_mentioned:
            view = views.ReadyView(bot, ctx, user, user_settings, user_mentioned, embed_ready)
        else:
            view = None
        if isinstance(ctx, discord.ApplicationContext):
            if ready_as_embed:
                interaction_message = await ctx.respond(embed=embed, view=view)
            else:
                interaction_message = await ctx.respond(answer, view=view)
        else:
            if ready_as_embed:
                interaction_message = await ctx.reply(embed=embed, view=view)
            else:
                interaction_message = await ctx.reply(answer, view=view)
        if not user_mentioned:
            view.interaction_message = interaction_message
            await view.wait()
            if view.value == 'show_settings':
                await functions.edit_interaction(interaction_message, view=None)
                await settings_cmd.command_settings_ready(bot, ctx)


# -- Embeds ---
async def embed_reminders_list(bot: bridge.AutoShardedBot, user: discord.User,
                               show_timestamps: Optional[bool] = False) -> discord.Embed:
    """Embed with active reminders"""
    user_settings: users.User = await users.get_user(user.id)
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

    current_time = utils.utcnow()
    reminders_commands_list = []
    reminders_events_list = []
    reminders_boosts_list = []
    reminders_epic_shop_list = []
    reminders_pets_list = []
    reminders_custom_list = []
    for reminder in user_reminders:
        if 'pets' in reminder.activity:
            reminders_pets_list.append(reminder)
        elif reminder.activity == 'custom':
            reminders_custom_list.append(reminder)
        elif reminder.activity in strings.ACTIVITIES_EVENTS:
            reminders_events_list.append(reminder)
        elif reminder.activity in strings.ACTIVITIES_BOOSTS or reminder.activity in strings.BOOSTS_ALIASES:
            reminders_boosts_list.append(reminder)
        elif reminder.activity.startswith('epic-shop-'):
            reminders_epic_shop_list.append(reminder)
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
    user_global_name = user.global_name if user.global_name is not None else user.name
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{user_global_name}\'S REMINDERS'.upper()
    )
    if not user_reminders and not clan_reminders:
        embed.description = f'{emojis.BP} You have no active reminders'
    if reminders_commands_list:
        field_command_reminders = ''
        reminder: reminders.Reminder
        for reminder in reminders_commands_list:
            if show_timestamps:
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
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
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
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
    if reminders_boosts_list:
        field_boosts_reminders = ''
        for reminder in reminders_boosts_list:
            if show_timestamps:
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
            else:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                reminder_time = f'**{timestring}**'
            activity = reminder.activity.replace('-',' ').capitalize()
            field_boosts_reminders = (
                f'{field_boosts_reminders}\n'
                f'{emojis.BP} **`{activity}`** ({reminder_time})'
            )
        embed.add_field(name='BOOSTS', value=field_boosts_reminders.strip(), inline=False)
    if reminders_epic_shop_list:
        field_epic_shop_reminders = ''
        for reminder in reminders_epic_shop_list:
            if show_timestamps:
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
            else:
                time_left = reminder.end_time - current_time
                timestring = await functions.parse_timedelta_to_timestring(time_left)
                reminder_time = f'**{timestring}**'
            activity = reminder.activity[10:].replace('-',' ').capitalize()
            field_epic_shop_reminders = (
                f'{field_epic_shop_reminders}\n'
                f'{emojis.BP} **`{activity}`** ({reminder_time})'
            )
        embed.add_field(name='EPIC SHOP RESTOCKS', value=field_epic_shop_reminders.strip(), inline=False)
    if clan_reminders:
        reminder = clan_reminders[0]
        clan: clans.Clan = await clans.get_clan_by_clan_name(reminder.clan_name)
        if clan.quest_user_id is not None:
            if clan.quest_user_id != user.id: time_left = time_left + timedelta(minutes=5)
        if show_timestamps:
            flag = 'T' if reminder.end_time.day == current_time.day else 'f'
            reminder_time = utils.format_dt(reminder.end_time, flag)
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
                end_time = current_time + timedelta(seconds=time_left_seconds)
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
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
                flag = 'T' if reminder.end_time.day == current_time.day else 'f'
                reminder_time = utils.format_dt(reminder.end_time, flag)
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


async def embed_ready(bot: bridge.AutoShardedBot, user: discord.User, auto_ready: bool) -> discord.Embed:
    """Embed with ready commands"""

    user_settings: users.User = await users.get_user(user.id)
    try:
        user_reminders = await reminders.get_active_user_reminders(user_settings.user_id)
    except exceptions.NoDataFoundError:
        user_reminders = []
    clan_reminders = []
    clan = None
    if user_settings.clan_name is not None:
        try:
            clan: clans.Clan = await clans.get_clan_by_clan_name(user_settings.clan_name)
            clan_reminders = await reminders.get_active_clan_reminders(user_settings.clan_name)
        except exceptions.NoDataFoundError:
            pass

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
        elif activity == 'party-popper':
            command_use = await functions.get_slash_command(user_settings, 'use', False)
            command_options = 'item: party popper' if user_settings.slash_mentions_enabled else 'party popper'
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
        elif activity == 'maintenance':
            command = '`maintenance`'
        elif activity == 'eternity-sealing':
            command = '`eternity sealing`'
        elif activity == 'hunt-partner':
            command = await functions.get_slash_command(user_settings, 'hunt', False)
            command = f'{command} `({user_settings.partner_name})`'
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
        elif activity == 'eternal-presents':
            if user_settings.slash_mentions_enabled:
                command = f"{command} `eternal`"
            else:
                command = f"{command} `eternal`"
        elif activity == 'farm':
            command = await functions.get_farm_command(user_settings, False)
        return command.replace('` `', ' ')

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

    all_settings: dict[str, str] = await settings_db.get_settings()
    ready_command_activities = await functions.get_ready_command_activities(all_settings['seasonal_event'])
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
    current_time = utils.utcnow()
    if 'hunt' in ready_command_activities and user_settings.partner_hunt_end_time > current_time:
        ready_command_activities.remove('hunt')
    if 'hunt-partner' in ready_command_activities:
        if user_settings.partner_id is not None:
            try:
                partner_hunt_reminder: reminders.Reminder = await reminders.get_user_reminder(user_settings.partner_id, 'hunt')
                ready_command_activities.remove('hunt-partner')
            except exceptions.NoDataFoundError:
                pass
        try:
            if user_settings.hunt_reminders_combined:
                ready_command_activities.remove('hunt-partner')
            if user_settings.partner_name is None:
                ready_command_activities.remove('hunt-partner')
        except ValueError:
            pass
    if 'farm' in ready_command_activities and not user_settings.ascended and user_settings.current_area in [1,2,3]:
        ready_command_activities.remove('farm')
    if 'training' in ready_command_activities and not user_settings.ascended and user_settings.current_area == 1:
        ready_command_activities.remove('training')
    if 'guild' in ready_command_activities and clan_reminders:
        ready_command_activities.remove('guild')
    if 'eternal-presents' in ready_command_activities and user_settings.inventory.present_eternal < 1:
        ready_command_activities.remove('eternal-presents')
    if 'advent-calendar' in ready_command_activities and (current_time.month != 12 or current_time.day > 25):
        ready_command_activities.remove('advent-calendar')
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
    user_global_name = user.global_name if user.global_name is not None else user.name
    embed = discord.Embed(
        color = int(f'0x{user_settings.ready_embed_color}', 16),
        title = f'• {user_global_name}\'S READY • '.upper()
    )
    if user_settings.ready_ping_user and auto_ready:
        answer = f'• **{user.mention}\'s ready** •'
    else:
        answer = f'• **{user_global_name}\'S READY** •'.upper()
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
            elif 'arena' in command and user_settings.ready_channel_arena is not None:
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.DETAIL} <#{user_settings.ready_channel_arena}>'
                )
            elif 'duel' in command and user_settings.ready_channel_duel is not None:
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.DETAIL} <#{user_settings.ready_channel_duel}>'
                )
            elif 'dungeon' in command and user_settings.ready_channel_dungeon is not None:
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.DETAIL} <#{user_settings.ready_channel_dungeon}>'
                )
            elif 'horse breed' in command and user_settings.ready_channel_horse is not None:
                field_ready_commands = (
                    f'{field_ready_commands}\n'
                    f'{emojis.DETAIL} <#{user_settings.ready_channel_horse}>'
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
    if not clan_reminders and clan_alert_enabled:
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
    if not ready_commands and not ready_event_activities and (clan_reminders or not clan_alert_enabled):
        answer = (
            f'{answer}\n'
            f'**Commands**\n'
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
    if user_settings.ready_trade_daily_visible and user_settings.top_hat_unlocked:
        if user_settings.trade_daily_total == 0:
            trade_daily_total = 0
            trade_daily_total_str = '?'
            trade_daily_left = 0
        else:
            trade_daily_total = user_settings.trade_daily_total
            trade_daily_total_str = f'{trade_daily_total:,}'
            trade_daily_left = user_settings.trade_daily_total - user_settings.trade_daily_done
            if trade_daily_left < 0: trade_daily_left = 0
        if (user_settings.trade_daily_done < trade_daily_total
            or (user_settings.trade_daily_done >= trade_daily_total and user_settings.ready_trade_daily_completed_visible)):
            field_trade_daily = (
                f'{emojis.BP} `{user_settings.trade_daily_done:,}`/`{trade_daily_total_str}` (`{trade_daily_left:,}` left)'
            ).strip()
            if user_settings.trade_daily_total == 0:
                trade_command = await functions.get_slash_command(user_settings, 'trade list')
                field_trade_daily = (
                    f'{field_trade_daily}\n'
                    f'{emojis.DETAIL} _Total amount unknown. Use {trade_command} to update._'
                )
            embed.add_field(name='DAILY TRADES', value=field_trade_daily.strip(), inline=False)
            answer = (
                f'{answer}\n'
                f'**DAILY TRADES**\n'
                f'{field_trade_daily.strip()}'
            )
    if user_settings.ready_eternity_visible:
        for reminder in user_reminders:
            if reminder.activity == 'eternity-sealing':
                current_time = utils.utcnow()
                if user_settings.ready_up_next_as_timestamp:
                    seal_time = utils.format_dt(reminder.end_time, 'R')
                else:
                    time_left = reminder.end_time - current_time
                    timestring = await functions.parse_timedelta_to_timestring(time_left)
                    seal_time = f'in **{timestring}**'
                field_eternity = (
                    f'{emojis.DETAIL} Eternity will seal {seal_time}.'
                )
                embed.add_field(name='ETERNITY UNSEALED', value=field_eternity.strip(), inline=False)
                answer = (
                    f'{answer}\n'
                    f'**ETERNITY UNSEALED**\n'
                    f'{field_eternity.strip()}'
                )
                break
    if user_settings.ready_up_next_visible:
        try:
            active_reminders = await reminders.get_active_user_reminders(user.id)
        except exceptions.NoDataFoundError:
            active_reminders = []
        if active_reminders:
            field_up_next = ''
            current_time = utils.utcnow()
            for reminder in active_reminders:
                if 'pets' in reminder.activity: continue
                if (reminder.activity in strings.ACTIVITIES_BOOSTS or reminder.activity in strings.BOOSTS_ALIASES
                    or reminder.activity.startswith('epic-shop')): continue
                if (not user_settings.ready_up_next_show_hidden_reminders and not 'custom' in reminder.activity
                    and not reminder.activity == 'unstuck'):
                    alert_settings = getattr(user_settings, strings.ACTIVITIES_COLUMNS[reminder.activity])
                    if not alert_settings.visible: continue
                if user_settings.ready_up_next_as_timestamp:
                    up_next_time = utils.format_dt(reminder.end_time, 'R')
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
                
    if all_settings['seasonal_event'] in strings.SEASONAL_EVENTS:
        embed.set_footer(text=f'{all_settings["seasonal_event"].replace("_"," ").capitalize()} event mode active.')

    return (embed, answer)