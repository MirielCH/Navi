# events.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class EventsCog(commands.Cog):
    """Cog that contains the Event detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_events_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the events message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Duel detection: {message}')
                if  ((message.find(f'Normal events') > -1) and (message.find(f'Guild ranking') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message(bot_answer)
        return (bot_answer, bot_message)

    # --- Commands ---
    @commands.command(aliases=('events',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def event(self, ctx: commands.Context) -> None:
        """Detects EPIC RPG events messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled: return
            if (not user.alert_big_arena.enabled and not user.alert_lottery.enabled
                and not user.alert_not_so_mini_boss.enabled and not user.alert_pet_tournament.enabled
                and not user.alert_horse_race.enabled):
                return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_events_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Events detection: {message}')
                        if  ((message.find(f'Normal events') > -1) and (message.find(f'Guild ranking') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                            bot_answer = msg
                            bot_message = message
                    except Exception as e:
                        await ctx.send(f'Error reading message history: {e}')
            if bot_message is None:
                task_result = await task_status
                if task_result is not None:
                    bot_answer = task_result[0]
                    bot_message = task_result[1]
                else:
                    await ctx.send('Events detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check if event list, if yes, extract all the timestrings
            if bot_message.find('Normal events') > 1:
                cooldowns = []
                if user.alert_big_arena.enabled:
                    if bot_message.find('Big arena**: ') > -1:
                        arena_start = bot_message.find('Big arena**: ') + 13
                        arena_end = bot_message.find('s', arena_start) + 1
                        arena = bot_message[arena_start:arena_end]
                        arena_message = user.alert_big_arena.message.format(event='big arena')
                        cooldowns.append(['big-arena', arena.lower(), arena_message])
                if user.alert_lottery.enabled:
                    if bot_message.find('Lottery**: ') > -1:
                        lottery_start = bot_message.find('Lottery**: ') + 11
                        lottery_end = bot_message.find('s', lottery_start) + 1
                        lottery = bot_message[lottery_start:lottery_end]
                        lottery_message = user.alert_lottery.message.replace('%','rpg buy lottery ticket')
                        cooldowns.append(['lottery', lottery.lower(), lottery_message])
                if user.alert_not_so_mini_boss.enabled:
                    if bot_message.find('"mini" boss**: ') > -1:
                        miniboss_start = bot_message.find('"mini" boss**: ') + 15
                        miniboss_end = bot_message.find('s', miniboss_start) + 1
                        miniboss = bot_message[miniboss_start:miniboss_end]
                        miniboss_message = user.alert_dungeon_miniboss.message.replace('%','rpg dungeon / miniboss')
                        cooldowns.append(['not-so-mini-boss', miniboss.lower(), miniboss_message])
                if user.alert_pet_tournament.enabled:
                    if bot_message.find('tournament**: ') > -1:
                        pet_start = bot_message.find('tournament**: ') + 14
                        pet_end = bot_message.find('s', pet_start) + 1
                        tournament = bot_message[pet_start:pet_end]
                        pet_message = user.alert_pet_tournament.message.format(event='pet tournament')
                        cooldowns.append(['pet-tournament',tournament.lower(),pet_message])
                if user.alert_horse_race.enabled:
                    if bot_message.find('race**: ') > -1:
                        race_start = bot_message.find('race**: ') + 8
                        race_end = bot_message.find('s', race_start) + 1
                        race = bot_message[race_start:race_end]
                        race_message = user.alert_horse_race.message.format(event='horse race')
                        cooldowns.append(['horse-race', race.lower(), race_message])
                for cooldown in cooldowns:
                    activity = cooldown[0]
                    timestring = cooldown[1]
                    message = cooldown[2]
                    time_left = await functions.parse_timestring_to_timedelta(ctx, timestring)
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left - time_elapsed
                    if activity == 'pet-tournament':
                        time_left = time_left + timedelta(minutes=1) #The event is somethings not perfectly on point, so I added a minute
                    updated_reminder = False
                    if time_left.total_seconds() > 0:
                        try:
                            reminder: reminders.Reminder = await reminders.get_user_reminder(ctx.author.id, activity)
                            end_time = current_time + time_left
                            await reminder.update(end_time=end_time)
                            if not reminder.record_exists:
                                await ctx.send(strings.MSG_ERROR)
                                return
                            updated_reminder = True
                        except exceptions.NoDataFoundError:
                            pass
                if updated_reminder: await bot_answer.add_reaction(emojis.NAVI)

            # Ignore anti spam embed
            elif bot_message.find('Huh please don\'t spam') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore failed Epic Guard event
            elif bot_message.find('is now in the jail!') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                await bot_answer.add_reaction(emojis.RIP)
                return
            # Ignore error when another command is active
            elif bot_message.find('end your previous command') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
        except asyncio.TimeoutError:
            await ctx.send('Event detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Event detection error: {e}')
            return

# Initialization
def setup(bot):
    bot.add_cog(EventsCog(bot))