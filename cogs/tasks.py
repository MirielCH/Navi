# tasks.py
"""Contains task related stuff"""

import asyncio
from datetime import datetime, timedelta

from discord.ext import commands, tasks

from database import clans, errors, reminders, users
from resources import emojis, exceptions, settings, strings


running_tasks = {}


class TasksCog(commands.Cog):
    """Cog with tasks"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Task management
    async def background_task(self, reminder: reminders.Reminder) -> None:
        """Background task for scheduling reminders"""
        def get_time_left() -> timedelta:
            current_time = datetime.utcnow().replace(microsecond=0)
            time_left = reminder.end_time - current_time
            if time_left.total_seconds() < 0: time_left = timedelta(seconds=0)
            return time_left

        try:
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(reminder.channel_id)
            if reminder.reminder_type == 'user':
                await self.bot.wait_until_ready()
                user = self.bot.get_user(reminder.user_id)
                user_settings = await users.get_user(user.id)
                if reminder.activity == 'custom':
                    message = strings.DEFAULT_MESSAGE_CUSTOM_REMINDER.replace('%', reminder.message)
                else:
                    message = reminder.message
                time_left = get_time_left()
                await asyncio.sleep(time_left.total_seconds())
                if not user_settings.dnd_mode_enabled:
                    await channel.send(f'{user.mention} {message}')
                else:
                    await channel.send(f'**{user.name}**, {message}')
            else:
                clan = await clans.get_clan_by_clan_name(reminder.clan_name)
                message_mentions = ''
                for member_id in clan.member_ids:
                    if member_id is not None:
                        await self.bot.wait_until_ready()
                        member = self.bot.get_user(member_id)
                        if member is not None:
                            message_mentions = f'{message_mentions}{member.mention} '
                time_left = get_time_left()
                await asyncio.sleep(time_left.total_seconds())
                await channel.send(f'{reminder.message}\n{message_mentions}')
            running_tasks.pop(reminder.task_name, None)
        except Exception as error:
            await errors.log_error(error)

    async def create_task(self, reminder: reminders.Reminder) -> None:
        """Creates a new background task"""
        await self.delete_task(reminder.task_name)
        task = self.bot.loop.create_task(self.background_task(reminder))
        running_tasks[reminder.task_name] = task

    async def delete_task(self, task_name: str) -> None:
        """Stops and deletes a running task if it exists"""
        if task_name in running_tasks:
            running_tasks[task_name].cancel()
            running_tasks.pop(task_name, None)
        return

    # Events
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when bot has finished starting"""
        reminders.schedule_reminders.start()
        self.delete_old_reminders.start()
        self.reset_clans.start()
        self.schedule_tasks.start()

    # Tasks
    @tasks.loop(seconds=0.5)
    async def schedule_tasks(self):
        """Task that creates or deletes tasks from scheduled reminders"""
        for reminder in reminders.scheduled_for_tasks.copy().values():
            reminders.scheduled_for_tasks.pop(reminder.task_name, None)
            await self.create_task(reminder)
        for reminder in reminders.scheduled_for_deletion.copy().values():
            reminders.scheduled_for_deletion.pop(reminder.task_name, None)
            await self.delete_task(reminder.task_name)

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
                    f'Error deleting old reminder.\nFunction: delete_old_reminders\nReminder: {reminder}\nError: {error}'
            )

    @tasks.loop(minutes=1.0)
    async def reset_clans(self) -> None:
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
                try:
                    reminder = await reminders.get_clan_reminder(clan.clan_name)
                    await reminder.delete()
                except:
                    pass
                if not clan.alert_enabled: continue
                reminder_message = clan.alert_message.replace('%','rpg guild upgrade')
                time_left = timedelta(minutes=1)
                await reminders.insert_clan_reminder(clan.clan_name, time_left, clan.channel_id, reminder_message)
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
                    await self.bot.wait_until_ready()
                    best_user = self.bot.get_user(weekly_report.best_raid.user_id)
                    best_user_praise = weekly_report.praise.format(username=best_user.name)
                    message = (
                        f'{message}{emojis.BP} '
                        f'{best_user_praise} (_Best raid: {weekly_report.best_raid.energy:,}_ {emojis.ENERGY})\n'
                    )
                if weekly_report.worst_raid is None:
                    message = f'{message}{emojis.BP} There were no cool raids. How lame.\n'
                else:
                    await self.bot.wait_until_ready()
                    worst_user = self.bot.get_user(weekly_report.worst_raid.user_id)
                    worst_user_roast = weekly_report.roast.format(username=worst_user.name)
                    message = (
                        f'{message}{emojis.BP} '
                        f'{worst_user_roast} (_Worst raid: {weekly_report.worst_raid.energy:,}_ {emojis.ENERGY})\n'
                    )
                await self.bot.wait_until_ready()
                clan_channel = self.bot.get_channel(clan.channel_id)
                await clan_channel.send(message)
            # Delete leaderboard
            await clans.delete_clan_leaderboard()


# Initialization
def setup(bot):
    bot.add_cog(TasksCog(bot))