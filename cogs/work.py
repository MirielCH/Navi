# work.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class WorkCog(commands.Cog):
    """Cog that contains the work detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_work_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the work message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Work detection: {message}')
                if  (((message.find(f'{ctx_author}** got ') > -1) or (message.find(f'{ctx_author}** GOT ') > -1)) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                or (message.find('RUBY') > -1) or (message.find('ruby') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or (message.find('it seems like the river is frozen in this area lmao') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('You slept well and the items respawned') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
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
    @commands.command(aliases=('axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor',
                               'greenhouse','mine','pickaxe','drill','dynamite',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def chop(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG work messages and creates reminders"""
        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()
        if prefix.lower() != 'rpg ': return
        if invoked == 'ascended':
            command = f'rpg ascended {args[0].lower()}'
        else:
            command = f'rpg {invoked.lower()}'

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled or not user.alert_work.enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            work_message = user.alert_work.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_work_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Work detection: {message}')
                        if  (((message.find(f'{ctx_author}** got ') > -1) or (message.find(f'{ctx_author}** GOT ') > -1)) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                        or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                        or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                        or (message.find('RUBY') > -1) or (message.find('ruby') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                        and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                        or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                        or (message.find('it seems like the river is frozen in this area lmao') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('You slept well and the items respawned') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
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
                    await ctx.send('Work detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check for rubies
            if user.ruby_counter_enabled:
                if (bot_message.lower().find('<:ruby:') > -1):
                    rubies_start = bot_message.lower().find(' got ') + 5
                    rubies_end = bot_message.lower().find('<:ruby:') - 1
                    rubies = bot_message[rubies_start:rubies_end]
                    if rubies.isnumeric():
                        rubies = user.rubies + int(rubies)
                        await user.update(rubies=rubies)
                        await bot_answer.add_reaction(emojis.NAVI)
                    elif (bot_message.find('rubies in it') > -1):
                        rubies_start = bot_message.find('One of them had ') + 16
                        rubies_end = bot_message.find('<:ruby:') - 1
                        rubies = bot_message[rubies_start:rubies_end]
                        if rubies.isnumeric():
                            rubies = user.rubies + int(rubies)
                            await user.update(rubies=rubies)
                            await bot_answer.add_reaction(emojis.NAVI)
                        else:
                            await ctx.send(
                                f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}'
                            )
                    else:
                        await ctx.send(
                            f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}'
                        )

            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            if bot_message.find(f'\'s cooldown') > 1:
                timestring_start = bot_message.find('wait at least **') + 16
                timestring_end = bot_message.find('**...', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(ctx.author.id, 'work', time_left,
                                                         ctx.channel.id, work_message)
                )
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
            # Ignore higher area error
            elif bot_message.find('This command is unlocked in') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore ascended error
            elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when another command is active
            elif bot_message.find('end your previous command') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

            # Calculate cooldown
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('work')
            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            if cooldown.donor_affected:
                time_left_seconds = (cooldown.actual_cooldown()
                                     * settings.DONOR_COOLDOWNS[user_donor_tier]
                                     - time_elapsed.total_seconds())
            else:
                time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
            time_left = timedelta(seconds=time_left_seconds)

            # Save reminder to database
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(ctx.author.id, 'work', time_left,
                                                     ctx.channel.id, work_message)
            )

            # Add reaction
            if reminder.record_exists:
                await bot_answer.add_reaction(emojis.NAVI)
                if (bot_message.find(f'IS THIS A **DREAM**?????') > -1) or (bot_message.find(f'**HYPER** log') > -1) or (bot_message.find(f'**MEGA** log') > -1):
                    await bot_answer.add_reaction(emojis.FIRE)
                if '(quite a large leaf)' in bot_message:
                    await bot_answer.add_reaction(emojis.WOAH_THERE)
                elif 'For some reason, one of the fish was carrying' in bot_message:
                    await bot_answer.add_reaction(emojis.FISHPOGGERS)
                elif 'mined with too much force, one of the nearby trees' in bot_message:
                    await bot_answer.add_reaction(emojis.SWEATY)
                elif 'One of them had' in bot_message and 'rubies in it' in bot_message:
                    await bot_answer.add_reaction(emojis.WOW)
            else:
                if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)
                return
        except asyncio.TimeoutError:
            await ctx.send('Work detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Work detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(WorkCog(bot))