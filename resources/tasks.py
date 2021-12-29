# tasks.py
"""Contains task related stuff"""

import asyncio
from datetime import datetime, timedelta

from discord.ext import tasks

from database import clans, errors, reminders, users
from resources import emojis, exceptions, settings, system


# Runnin tasks dictionary
running_tasks = {}


async def background_task(reminder: reminders.Reminder) -> None:
    """Background task for scheduling reminders"""
    current_time = datetime.utcnow().replace(microsecond=0)
    time_left = reminder.end_time - current_time
    await asyncio.sleep(time_left.total_seconds())
    try:
        await system.bot.wait_until_ready()
        channel = system.bot.get_channel(reminder.channel_id)
        if reminder.reminder_type == 'user':
            await system.bot.wait_until_ready()
            user = system.bot.get_user(reminder.user_id)
            user_settings = await users.get_user(user.id)
            if not user_settings.dnd_mode_enabled:
                await channel.send(f'{user.mention} {reminder.message}')
            else:
                await channel.send(f'**{user.name}**, {reminder.message}')
        else:
            clan = await clans.get_clan_by_user_id(reminder.user_id)
            message_mentions = ''
            for member_id in clan.member_ids:
                if member_id is not None:
                    await system.bot.wait_until_ready()
                    member = system.bot.get_user(member_id)
                    if member is not None:
                        message_mentions = f'{message_mentions}{member.mention} '
            await channel.send(f'{reminder.message}\n{message_mentions}')
        running_tasks.pop(reminder.task_name, None)
    except Exception as error:
        await errors.log_error(error)


async def create_task(reminder: reminders.Reminder) -> None:
    """Creates a new background task"""
    await delete_task(reminder.task_name)
    task = system.bot.loop.create_task(background_task(reminder))
    running_tasks[reminder.task_name] = task


async def delete_task(task_name: str) -> None:
    """Stops and deletes a running task if it exists"""
    if task_name in running_tasks:
        running_tasks[task_name].cancel()
        running_tasks.pop(task_name, None)


@tasks.loop(seconds=10.0)
async def schedule_reminders():
    """Task that reads all due reminders from the database and schedules them"""
    try:
        due_user_reminders = await reminders.get_due_user_reminders()
    except:
        due_user_reminders = ()
    try:
        due_clan_reminders = await reminders.get_due_clan_reminders()
    except:
        due_clan_reminders = ()
    due_reminders = list(due_user_reminders) + list(due_clan_reminders)
    for reminder in due_reminders:
        try:
            await create_task(reminder)
            await reminder.update(triggered=True)
        except Exception as error:
            await errors.log_error(
                f'Error scheduling a reminder.\nFunction: schedule_reminders\nReminder: {reminder}\nError: {error}'
            )


@tasks.loop(minutes=2.0)
async def delete_old_reminders() -> None:
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
                f'Error deleting old reminder.\nFunction: delete_old_reminders\nReminder: {reminder}\nError: {error}'
            )


@tasks.loop(minutes=1.0)
async def reset_clans() -> None:
    """Task that creates the weekly reports and resets the clans"""
    clan_reset_time = settings.ClanReset()
    current_time = datetime.utcnow().replace(microsecond=0)
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
            time_left = timedelta(minutes=1)
            reminder_message = clan.alert_message.replace('%','rpg guild upgrade')
            try:
                reminder = await reminders.get_clan_reminder(clan.clan_name)
                await reminder.delete()
            except:
                pass
            await reminders.insert_clan_reminder(clan.clan_name, time_left, clan.channel_id, reminder_message)
            try:
                weekly_report: clans.ClanWeeklyReport = await clans.get_weekly_report(clan)
            except exceptions.NoDataFoundError:
                continue
            message = (
                f'**{clan.clan_name} weekly guild report**\n\n'
                f'__Total energy from raids__: {weekly_report.energy_total} {emojis.ENERGY}\n\n'
            )
            if weekly_report.best_raid is None:
                message = f'{message}{emojis.BP} There were no cool raids. Not cool.\n'
            else:
                await system.bot.wait_until_ready()
                best_user = system.bot.get_user(weekly_report.best_raid.user_id)
                best_user_praise = weekly_report.praise.format(username=best_user.name)
                message = (
                    f'{message}{emojis.BP} '
                    f'{best_user_praise} (_Best raid: {weekly_report.best_raid.energy}_ {emojis.ENERGY})\n'
                )
            if weekly_report.worst_raid is None:
                message = f'{message}{emojis.BP} There were no cool raids. How lame.\n'
            else:
                await system.bot.wait_until_ready()
                worst_user = system.bot.get_user(weekly_report.worst_raid.user_id)
                worst_user_roast = weekly_report.roast.format(username=worst_user.name)
                message = (
                    f'{message}{emojis.BP} '
                    f'{worst_user_roast} (_Worst raid: {weekly_report.worst_raid.energy}_ {emojis.ENERGY})\n'
                )
            await system.bot.wait_until_ready()
            clan_channel = system.bot.get_channel(clan.channel_id)
            await clan_channel.send(message)
        # Delete leaderboard
        await clans.delete_clan_leaderboard()