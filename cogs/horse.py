# horse.py

import asyncio
from datetime import datetime
from typing import Tuple

import discord
from discord.ext import commands

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings


class HorseCog(commands.Cog):
    """Cog that contains the horse detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_horse_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the horse message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Horse detection: {message}')
                if  ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have used this command recently') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('registered for the next **horse race** event') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you are registered already!') > -1))\
                or (message.find(f'\'s horse breeding') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def horse(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG horse messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if not args: return
        if not args[0] in ('breed','race'): return
        command = 'rpg horse breed / race'
        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled: return
            if not user.alert_horse_breed.enabled and not user.alert_horse_race.enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_horse_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Horse detection: {message}')
                        if  ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have used this command recently') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('registered for the next **horse race** event') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you are registered already!') > -1))\
                        or (message.find(f'\'s horse breeding') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
                    await ctx.send('Horse detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            if user.alert_horse_breed.enabled:
                horse_breed_message = user.alert_horse_breed.message.replace('%',command)
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                if bot_message.find(f'{ctx_author}\'s cooldown') > -1:
                    timestring_start = bot_message.find('wait at least **') + 16
                    timestring_end = bot_message.find('**...', timestring_start)
                    timestring = bot_message[timestring_start:timestring_end]
                    time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left - time_elapsed
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(self.bot, ctx.author.id, 'horse', time_left,
                                                             ctx.channel.id, horse_breed_message)
                    )
                    if reminder.record_exists:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
            if user.alert_horse_race.enabled:
                horse_race_message = user.alert_horse_race.message.format(event='horse race')
                # Check if event message with time in it, if yes, read the time and update/insert the reminder if necessary
                if bot_message.find(f'The next race is in') > -1:
                    timestring_start = bot_message.find('race is in **') + 13
                    timestring_end = bot_message.find('**,', timestring_start)
                    timestring = bot_message[timestring_start:timestring_end]
                    time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left-time_elapsed
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(self.bot, ctx.author.id, 'horse-race', time_left,
                                                             ctx.channel.id, horse_race_message)
                    )
                    if reminder.record_exists:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
            # Ignore anti spam embed
            if bot_message.find('Huh please don\'t spam') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore failed Epic Guard event
            if bot_message.find('is now in the jail!') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                await bot_answer.add_reaction(emojis.RIP)
                return
            # Ignore higher area error
            if bot_message.find('This command is unlocked in') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore ascended error
            if bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when another command is active
            if bot_message.find('end your previous command') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

        except asyncio.TimeoutError:
            await ctx.send('Horse detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Horse detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(HorseCog(bot))