# weekly.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class WeeklyCog(commands.Cog):
    """Cog that contains the weekly detection commands"""
    def __init__(self, bot):
        self.bot = bot

    # Weekly detection
    async def get_weekly_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the weekly message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Weekly detection: {message}')
                if  (message.find(f'{ctx_author}\'s weekly reward') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have claimed your weekly rewards already') > -1))\
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
    async def weekly(self, ctx: commands.Context) -> None:
        """Detects EPIC RPG weekly messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        command = 'rpg weekly'

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled or not user.alert_weekly.enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            weekly_message = user.alert_weekly.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_weekly_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Weekly detection: {message}')
                        if  (message.find(f'{ctx_author}\'s weekly reward') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have claimed your weekly rewards already') > -1))\
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
                    await ctx.send('Hunt detection timeout.')
                    return

            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            if bot_message.find(f'\'s cooldown') > 1:
                timestring_start = bot_message.find('wait at least **') + 16
                timestring_end = bot_message.find('**...', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder: reminders.Reminder = reminders.insert_user_reminder(ctx.author.id, 'weekly', time_left,
                                                                              ctx.channel.id, weekly_message)
                if reminder.record_exists:
                    await bot_answer.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
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

            # Calculate cooldown
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('weekly')
            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            if cooldown.donor_affected:
                time_left_seconds = cooldown.actual_cooldown() * settings.DONOR_COOLDOWNS[user_donor_tier]
            else:
                time_left_seconds = cooldown.actual_cooldown()
            time_left = timedelta(seconds=time_left_seconds)

            # Save reminder to database
            reminder: reminders.Reminder = reminders.insert_user_reminder(ctx.author.id, 'weekly', time_left,
                                                                          ctx.channel.id, weekly_message)

            # Add reaction
            if reminder.record_exists:
                await bot_answer.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)

        except asyncio.TimeoutError:
            await ctx.send('Weekly detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Weekly detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(WeeklyCog(bot))