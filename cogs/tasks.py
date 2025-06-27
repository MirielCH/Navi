# tasks.py
"""Contains task related stuff"""

import asyncio
from datetime import datetime, timedelta
from humanfriendly import format_timespan
import re
import sqlite3

import discord
from discord import utils
from discord.ext import bridge, commands, tasks

from cache import messages
from database import clans, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, logs, settings, strings


running_tasks = {}


class TasksCog(commands.Cog):
    """Cog with tasks"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Task management
    async def background_task(self, reminders_list: list[reminders.Reminder]) -> None:
        """Background task for scheduling reminders"""
        first_reminder = reminders_list[0]
        current_time = utils.utcnow()
        def get_time_left() -> timedelta:
            time_left = first_reminder.end_time - current_time
            if time_left.total_seconds() < 0: time_left = timedelta(seconds=0)
            return time_left

        try:
            if first_reminder.reminder_type == 'user':
                user = await functions.get_discord_user(self.bot, first_reminder.user_id)
                user_global_name = user.global_name if user.global_name is not None else user.name
                user_settings = await users.get_user(user.id)
                if user_settings.reminder_channel_id is not None:
                    reminder_channel_id = user_settings.reminder_channel_id
                else:
                    reminder_channel_id = first_reminder.channel_id
                channel = await functions.get_discord_channel(self.bot, reminder_channel_id)
                if channel is None: return
                hunt_reminder = None
                message_no = 1
                messages = {message_no: ''}
                for reminder in reminders_list:
                    if reminder.activity == 'custom':
                        reminder_message = strings.DEFAULT_MESSAGE_CUSTOM_REMINDER.format(message=reminder.message)
                        if user_settings.dnd_mode_enabled:
                            message = f'**{user_global_name}** {reminder_message}\n'
                        else:
                            message = f'{user.mention} {reminder_message}\n'
                    else:
                        reminder_message = reminder.message
                        if user_settings.dnd_mode_enabled:
                            message = f'{reminder_message.replace("{name}", f"**{user_global_name}**")}\n'
                        else:
                            message = f'{reminder_message.replace("{name}", user.mention)}\n'
                        mob_drop_emoji = emojis.MONSTER_DROP_AREAS_EMOJIS.get(user_settings.current_area, '')
                        message = message.replace('{drop_emoji}', mob_drop_emoji)
                        if reminder.activity == 'hunt' and not user_settings.hunt_reminders_combined:
                            try:
                                hunt_partner_reminder = await reminders.get_user_reminder(user.id, 'hunt-partner')
                            except exceptions.NoDataFoundError:
                                hunt_partner_reminder = None
                            if hunt_partner_reminder is not None:
                                if not hunt_partner_reminder.triggered:
                                    time_left_hunt_partner = hunt_partner_reminder.end_time - reminder.end_time
                                    if time_left_hunt_partner.total_seconds() >= 1:
                                        timestring = await functions.parse_timedelta_to_timestring(time_left_hunt_partner)
                                        message = f'{message}➜ **{user_settings.partner_name}** will be ready in **{timestring}**.\n'
                        if reminder.activity == 'hunt-partner':
                            try:
                                hunt_reminder = await reminders.get_user_reminder(user.id, 'hunt')
                            except exceptions.NoDataFoundError:
                                hunt_reminder = None
                            if hunt_reminder is not None:
                                time_left_hunt = hunt_reminder.end_time - reminder.end_time
                                if time_left_hunt.total_seconds() >= 1:
                                    timestring = await functions.parse_timedelta_to_timestring(time_left_hunt)
                                    message = f'{message}➜ You will be ready in **{timestring}**.\n'
                    if len(f'{messages[message_no]}{message}') > 1900:
                        message_no += 1
                        messages[message_no] = ''
                    messages[message_no] = f'{messages[message_no]}{message}'
                if reminder.activity.startswith('pets'):
                    try:
                        pet_reminders = (
                            await reminders.get_active_user_reminders(user_id=reminder.user_id, activity='pets',
                                                                      end_time=reminder.end_time)
                        )
                    except exceptions.NoDataFoundError:
                        pet_reminders = ()
                        await user_settings.update(ready_pets_claim_active=True)
                    command_pets_claim = strings.SLASH_COMMANDS['pets claim']
                    if not pet_reminders:
                        messages[message_no] = (
                            f'{messages[message_no]}'
                            f"➜ {command_pets_claim} - No more pets found."
                        )
                    else:
                        next_pet_reminder = pet_reminders[0]
                        next_pet_id = next_pet_reminder.activity.replace('pets-','')
                        time_left_next = next_pet_reminder.end_time - reminder.end_time
                        timestring = await functions.parse_timedelta_to_timestring(time_left_next)
                        pet_amount_left = len(pet_reminders)
                        pets_left = f'**{pet_amount_left}** pet'
                        if pet_amount_left > 1: pets_left = f'{pets_left}s'
                        messages[message_no] = (
                            f'{messages[message_no]}'
                            f"➜ {command_pets_claim} - {pets_left} left. Next pet (`{next_pet_id}`) "
                            f'in **{timestring}**.'
                        )
                time_left = get_time_left()
                try:
                    await asyncio.sleep(time_left.total_seconds())
                    if user_settings.ready_pets_claim_after_every_pet and reminder.activity.startswith('pets'):
                        await user_settings.update(ready_pets_claim_active=True)
                    if reminder.activity == 'dragon-breath-potion':
                        await user_settings.update(potion_dragon_breath_active=False)
                    elif reminder.activity == 'round-card':
                        await reminders.increase_reminder_time_percentage(user_settings, 95, strings.ROUND_CARD_AFFECTED_ACTIVITIES)
                        await user_settings.update(round_card_active=False)
                    elif reminder.activity in ('mega-boost', 'egg-blessing', 'potion-potion'):
                        auto_healing_active = False
                        try:
                            await reminders.get_user_reminder(user_settings.user_id, 'potion-potion')
                            auto_healing_active = True
                        except exceptions.NoDataFoundError:
                            pass
                        try:
                            await reminders.get_user_reminder(user_settings.user_id, 'mega-boost')
                            auto_healing_active = True
                        except exceptions.NoDataFoundError:
                            pass
                        try:
                            await reminders.get_user_reminder(user_settings.user_id, 'egg-blessing')
                            auto_healing_active = True
                        except exceptions.NoDataFoundError:
                            pass
                        await user_settings.update(auto_healing_active=auto_healing_active)
                    for message in messages.values():
                        for found_id in re.findall(r'<@!?(\d{16,20})>', message):
                            if int(found_id) not in user_settings.alts and int(found_id) != user_settings.user_id:
                                message = re.sub(rf'<@!?{found_id}>', '-Removed alt-', message)
                            if hunt_reminder is not None:
                                await hunt_reminder.refresh()
                                if hunt_reminder.record_exists:
                                    time_left_hunt = hunt_reminder.end_time - reminder.end_time
                                    if time_left_hunt.total_seconds() >= 1:
                                        timestring = await functions.parse_timedelta_to_timestring(time_left_hunt)
                                        re.sub(r'➜ You will be ready in \*\*(.+?)\*\*', message, timestring)
                        await channel.send(message.strip())
                except asyncio.CancelledError:
                    return
                except discord.errors.Forbidden:
                    return

            if first_reminder.reminder_type == 'clan':
                channel = await functions.get_discord_channel(self.bot, first_reminder.channel_id)
                if channel is None: return
                clan: clans.Clan = await clans.get_clan_by_clan_name(first_reminder.clan_name)
                if clan.quest_user_id is not None:
                    quest_user_id = clan.quest_user_id
                    await clan.update(quest_user_id=None)
                    time_left_all_members = timedelta(minutes=5)
                    if clan.stealth_current >= clan.stealth_threshold:
                        alert_message = strings.SLASH_COMMANDS["guild raid"]
                    else:
                        alert_message = strings.SLASH_COMMANDS["guild upgrade"]
                    time_left = get_time_left()
                    try:
                        await asyncio.sleep(time_left.total_seconds())
                        await channel.send(
                            f'<@{quest_user_id}> Hey! It\'s time for your raid quest. '
                            f'You have 5 minutes, chop chop.'
                        )
                        reminder: reminders.Reminder = (
                            await reminders.insert_clan_reminder(clan.clan_name, time_left_all_members,
                                                                 clan.channel_id, alert_message)
                        )
                        return
                    except asyncio.CancelledError:
                        return
                message_mentions = ''
                clan_member: clans.ClanMember
                for clan_member in clan.members:
                    message_mentions = f'{message_mentions}<@{clan_member.user_id}> '
                time_left = get_time_left()
                try:
                    await asyncio.sleep(time_left.total_seconds())
                    await channel.send(f'It\'s time for {first_reminder.message}!\n\n{message_mentions}')
                except asyncio.CancelledError:
                    return
                except discord.errors.Forbidden:
                    return
            running_tasks.pop(first_reminder.task_name, None)
        except discord.errors.Forbidden:
            return
        except Exception as error:
            await errors.log_error(error)

    async def create_task(self, reminders_list: list[reminders.Reminder]) -> None:
        """Creates a new background task"""
        await self.delete_task(reminders_list[0].task_name)
        task = self.bot.loop.create_task(self.background_task(reminders_list))
        running_tasks[reminders_list[0].task_name] = task

    async def delete_task(self, task_name: str) -> None:
        """Stops and deletes a running task if it exists"""
        if task_name in running_tasks:
            running_tasks[task_name].cancel()
            running_tasks.pop(task_name, None)
        return

    @commands.command(name='task-start')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def task_start(self, ctx: commands.Context, *args: str) -> None:
        """Manually start tasks"""
        if ctx.author.id not in settings.DEV_IDS: return
        errors = []
        try:
            reminders.schedule_reminders.start()
        except Exception as error:
            errors.append(f'Task "schedule_reminders": {error}')
        try:
            self.schedule_tasks.start()
        except Exception as error:
            errors.append(f'Task "schedule_tasks": {error}')
        try:
            self.delete_old_reminders.start()
        except Exception as error:
            errors.append(f'Task "delete_old_reminders": {error}')
        try:
            self.reset_clans.start()
        except Exception as error:
            errors.append(f'Task "reset_clans": {error}')
        try:
            self.consolidate_tracking_log.start()
        except Exception as error:
            errors.append(f'Task "consolidate_tracking_log": {error}')
        try:
            self.delete_old_messages_from_cache.start()
        except Exception as error:
            errors.append(f'Task "delete_olde_messages_from_cache": {error}')
        try:
            self.reset_trade_daily_done.start()
        except Exception as error:
            errors.append(f'Task "trade_daily_done": {error}')
        try:
            self.disable_event_reduction.start()
        except Exception as error:
            errors.append(f'Task "disable_event_reduction": {error}')
        errors_list = ''
        if errors:
            errors_list = '```'
            for error in errors:
                errors_list = f'{errors_list}\n{error}'
            errors_list = f'{errors_list}\n```'
        await ctx.reply(f'Done\n{errors_list}'.strip())

    # Events
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when bot has finished starting"""
        try:
            reminders.schedule_reminders.start()
        except RuntimeError:
            pass
        try:
            self.schedule_tasks.start()
        except RuntimeError:
            pass
        try:
            self.delete_old_reminders.start()
        except RuntimeError:
            pass
        try:
            self.reset_clans.start()
        except RuntimeError:
            pass
        try:
            self.consolidate_tracking_log.start()
        except RuntimeError:
            pass
        try:
            self.delete_old_messages_from_cache.start()
        except RuntimeError:
            pass 
        try:
            self.reset_trade_daily_done.start()
        except RuntimeError:
            pass
        try:
            self.disable_event_reduction.start()
        except RuntimeError:
            pass
        try:
            self.delete_empty_clans.start()
        except RuntimeError:
            pass

    # Tasks
    @tasks.loop(seconds=0.5)
    async def schedule_tasks(self):
        """Task that creates or deletes tasks from scheduled reminders.
        Reminders that fire at the same second for the same user in the same channel are combined into one task.
        """
        user_reminders = {}
        reminder: reminders.Reminder
        for reminder in reminders.scheduled_for_tasks.copy().values():
            reminders.scheduled_for_tasks.pop(reminder.task_name, None)
            if reminder.reminder_type == 'user':
                reminder_user_channel = f'{reminder.user_id}-{reminder.channel_id}-{reminder.end_time.replace(microsecond=0)}'
                if reminder_user_channel in user_reminders:
                    user_reminders[reminder_user_channel].append(reminder)
                else:
                    user_reminders[reminder_user_channel] = [reminder,]
            else:
                await self.create_task([reminder,])
        for reminder in reminders.scheduled_for_deletion.copy().values():
            reminders.scheduled_for_deletion.pop(reminder.task_name, None)
            await self.delete_task(reminder.task_name)
        if user_reminders:
            for reminders_list in user_reminders.values():
                reminders_list.sort(key=lambda reminder: reminder.activity)
                pet_reminders = []
                other_reminders = []
                for reminder in reminders_list:
                    if reminder.activity.startswith('pets'):
                        pet_reminders.append(reminder)
                    else:
                        other_reminders.append(reminder)
                await self.create_task(other_reminders + pet_reminders)

    @tasks.loop(minutes=2.0)
    async def delete_old_reminders(self) -> None:
        """Task that deletes all old reminders"""
        try:
            old_user_reminders = await reminders.get_old_user_reminders()
        except:
            old_user_reminders = ()
        try:
            old_clan_reminders = await reminders.get_old_clan_reminders()
        except:
            old_clan_reminders = ()
        old_reminders = list(old_user_reminders) + list(old_clan_reminders)

        for reminder in old_reminders:
            try:
                await reminder.delete()
            except Exception as error:
                await errors.log_error(
                    f'Error deleting old reminder.\nFunction: delete_old_reminders\n'
                    f'Reminder: {reminder}\nError: {error}'
            )

    @tasks.loop(hours=24)
    async def delete_empty_clans(self) -> None:
        """Task that deletes clans that have no members registered anymore."""
        try:
            all_clans: tuple[clans.Clan, ...] = await clans.get_all_clans()
        except exceptions.NoDataFoundError:
            return
        clan: clans.Clan
        for clan in all_clans:
            if not clan.members: await clan.delete()
            
    @tasks.loop(seconds=60)
    async def reset_clans(self) -> None:
        """Task that creates the weekly reports and resets the clans"""
        clan_reset_time = settings.ClanReset()
        current_time = utils.utcnow()
        if (
            (datetime.today().weekday() == clan_reset_time.weekday)
            and
            (current_time.hour == clan_reset_time.hour)
            and
            (current_time.minute == clan_reset_time.minute)
        ):
            # Create weekly clan reports, reset clan energy, delete current reminders and create a new reminder
            all_clans = await clans.get_all_clans()
            for clan in all_clans:
                await clan.update(stealth_current=1)
                try:
                    reminder = await reminders.get_clan_reminder(clan.clan_name)
                    await reminder.delete()
                except:
                    pass
                if not clan.alert_enabled: continue
                if clan.stealth_threshold > 1:
                    command = strings.SLASH_COMMANDS["guild upgrade"]
                else:
                    command = strings.SLASH_COMMANDS["guild raid"]
                time_left = timedelta(minutes=1)
                await reminders.insert_clan_reminder(clan.clan_name, time_left, clan.channel_id, command)
                try:
                    weekly_report: clans.ClanWeeklyReport = await clans.get_weekly_report(clan)
                except exceptions.NoDataFoundError:
                    continue
                message = (
                    f'**{clan.clan_name} weekly guild report**\n\n'
                    f'__Total energy from raids__: {weekly_report.energy_total:,} {emojis.ENERGY}\n\n'
                )
                if weekly_report.best_raid is None:
                    message = f'{message}{emojis.BP} There were no cool raids. Not cool.\n'
                else:
                    best_user = await functions.get_discord_user(self.bot, weekly_report.best_raid.user_id)
                    user_global_name = best_user.global_name if best_user.global_name is not None else best_user.name
                    best_user_praise = weekly_report.praise.format(username=user_global_name)
                    message = (
                        f'{message}{emojis.BP} '
                        f'{best_user_praise} (_Best raid: {weekly_report.best_raid.energy:,}_ {emojis.ENERGY})\n'
                    )
                if weekly_report.worst_raid is None:
                    message = f'{message}{emojis.BP} There were no lame raids. How lame.\n'
                else:
                    worst_user = await functions.get_discord_user(self.bot, weekly_report.worst_raid.user_id)
                    user_global_name = worst_user.global_name if worst_user.global_name is not None else worst_user.name
                    worst_user_roast = weekly_report.roast.format(username=user_global_name)
                    message = (
                        f'{message}{emojis.BP} '
                        f'{worst_user_roast} (_Worst raid: {weekly_report.worst_raid.energy:,}_ {emojis.ENERGY})\n'
                    )
                try:
                    clan_channel = await functions.get_discord_channel(self.bot, clan.channel_id)
                    if clan_channel is not None: await clan_channel.send(message)
                except:
                    pass
            # Delete leaderboard
            await clans.delete_clan_leaderboard()

    @tasks.loop(seconds=60)
    async def consolidate_tracking_log(self) -> None:
        """Task that consolidates tracking log entries older than 28 days into summaries"""
        start_time = utils.utcnow()
        if start_time.hour == 0 and start_time.minute == 15:
            log_entry_count = 0
            try:
                old_log_entries = await tracking.get_old_log_entries(28)
            except exceptions.NoDataFoundError:
                logs.logger.info('Didn\'t find any log entries to consolidate.')
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
            date_time = utils.utcnow() - timedelta(days=366)
            date_time = date_time.replace(hour=0, minute=0, second=0)
            sql = 'DELETE FROM tracking_log WHERE date_time<?'
            try:
                cur.execute(sql, (date_time,))
                cur.execute('VACUUM')
            except sqlite3.Error as error:
                logs.logger.error(f'Error while consolidating: {error}')
                raise
            end_time = utils.utcnow()
            time_passed = end_time - start_time
            logs.logger.info(f'Consolidated {log_entry_count:,} log entries in {format_timespan(time_passed)}.')
            
    @tasks.loop(seconds=60)
    async def reset_trade_daily_done(self) -> None:
        """Task that resets the daily trade amounts to 0"""
        current_time = utils.utcnow()
        if current_time.hour == 0 and current_time.minute == 0:
            all_user_settings = await users.get_all_users()
            for user_settings in all_user_settings:
                if user_settings.trade_daily_done != 0: await user_settings.update(trade_daily_done=0)

    @tasks.loop(seconds=60)
    async def delete_old_messages_from_cache(self) -> None:
        """Task that deletes messages from the message cache that are older than 10 minutes"""
        deleted_messages_count = await messages.delete_old_messages(timedelta(minutes=10))
        if settings.DEBUG_MODE:
            logs.logger.debug(f'Deleted {deleted_messages_count} messages from message cache.')

    @tasks.loop(seconds=60)
    async def disable_event_reduction(self) -> None:
        """Task that sets all event reductions to 0. Set time when needed (UTC)."""
        year, month, day = 2024, 2, 29
        hour, minute = 23, 55
        start_time = utils.utcnow()
        if (start_time.year == year and start_time.month == month and start_time.day == day and start_time.hour == hour
            and start_time.minute == minute):
            from database import cooldowns
            all_cooldowns = await cooldowns.get_all_cooldowns()
            for cooldown in all_cooldowns:
                await cooldown.update(event_reduction_slash=0, event_reduction_mention=0)

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(TasksCog(bot))