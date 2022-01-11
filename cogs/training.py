# training.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, tracking, users
from resources import emojis, exceptions, functions, logs, settings, strings


class TrainingCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Training detection
    async def get_training_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Cog that contains the training detection commands"""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Training detection: {message}')
                if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('is training in') > -1))\
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

    # Training answer detection
    async def get_training_answer_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Cog that contains the training answer detection commands"""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Training detection: {message}')
                if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT_LONGER)
        bot_message = await functions.encode_message(bot_answer)
        return (bot_answer, bot_message)

    # --- Commands ---
    @commands.command(aliases=('tr','ultraining','ultr',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def training(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG training messages and creates reminders"""
        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()
        if prefix.lower() != 'rpg ': return
        if not args:
            if invoked in ('tr', 'training',):
                command = 'rpg training'
            elif invoked in ('ultr', 'ultraining',):
                command = 'rpg ultraining'
        else:
            if invoked == 'ascended':
                arg_command = args[0]
                if arg_command in ('tr', 'training',):
                    command = 'rpg ascended training'
                elif arg_command in ('ultr', 'ultraining',):
                    command = 'rpg ascended ultraining'
                args = list(args)
                args.pop(0)
            else:
                args = [arg.lower() for arg in args]
                if invoked in ('tr', 'training',):
                    command = 'rpg training'
                elif invoked in ('ultr', 'ultraining',):
                    command = 'rpg ultraining'

                    if len(args) >= 1 and command.find('ultraining') > -1:
                        if args[0] in ('p','progress',): return

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.bot_enabled: return
            if not user.alert_training.enabled and not user.tracking_enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            tr_message = user.alert_training.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_training_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Training detection: {message}')
                        if (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                        or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('is training in') > -1))\
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
                    await ctx.send('Training detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Trigger training helper if necessary
            if bot_message.find('is training in') > -1:
                if bot_message.find('training in the mine') > -1 and user.ruby_counter_enabled:
                    ruby_start = bot_message.find('more than ') + 10
                    ruby_end = bot_message.find('<:ruby') - 1
                    ruby_count = bot_message[ruby_start:ruby_end]
                    try:
                        ruby_count = int(ruby_count)
                        if user.rubies > ruby_count:
                            answer = 'YES'
                        else:
                            answer = 'NO'
                    except:
                        answer = 'ERROR'
                    await bot_answer.reply(f'`{answer}` (you have {user.rubies} {emojis.RUBY})', mention_author=False)
                else:
                    if user.training_helper_enabled:
                        answer = functions.get_training_answer(bot_message.lower())
                        if answer is not None:
                            await bot_answer.reply(f'`{answer}`', mention_author=False)
                task_status = self.bot.loop.create_task(self.get_training_answer_message(ctx))
                bot_first_answer = bot_answer
                bot_message = None
                message_history = await ctx.channel.history(limit=50).flatten()
                for msg in message_history:
                    if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > bot_first_answer.created_at):
                        try:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message = await functions.encode_message(msg)
                            if settings.DEBUG_MODE: logs.logger.debug(f'Training detection (2nd message): {message}')
                            if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1):
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
                        await ctx.send('Training detection timeout.')
                        return
                if not task_status.done(): task_status.cancel()

            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            if bot_message.find(f'\'s cooldown') > 1:
                if not user.alert_training.enabled: return
                timestring_start = bot_message.find('wait at least **') + 16
                timestring_end = bot_message.find('**...', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(ctx.author.id, 'training', time_left,
                                                         ctx.channel.id, tr_message)
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

            # Add record to the tracking log
            if user.tracking_enabled:
                await tracking.insert_log_entry(user.user_id, ctx.guild.id, 'training', current_time)
            if not user.alert_training.enabled: return

            # Calculate cooldown
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('training')
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
                await reminders.insert_user_reminder(ctx.author.id, 'training', time_left,
                                                     ctx.channel.id, tr_message)
            )

            # Add reaction
            if reminder.record_exists:
                await bot_answer.add_reaction(emojis.NAVI)
                if 'Better luck next time,' in bot_message:
                    await bot_answer.add_reaction(emojis.LAUGH)
            else:
                if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)

        except asyncio.TimeoutError:
            await ctx.send('Training detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Training detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(TrainingCog(bot))