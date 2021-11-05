# sleepypotion.py

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import discord
import emojis
import global_data
import global_functions
import asyncio
import database

from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timedelta

# sleepy potion commands (cog)
class sleepypotionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Sleepy potion detection
    async def get_sleepy_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Sleepy detection: {message}')

                if  ((message.find(ctx_author) > -1) and (message.find('has slept for a day') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have a sleepy potion') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False

            return m.author.id == global_data.epic_rpg_id and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
        bot_message = await global_functions.encode_message(bot_answer)

        return (bot_answer, bot_message,)

    # Boo detection
    async def get_boo_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Boo detection: {message}')

                if ((message.find(ctx_author) > -1) and (message.find('failed to scare') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('scared') > -1))\
                or ('bots cannot be scared' in message)\
                or ('you can\'t scare yourself lol' in message)\
                or ('so no chance to scare lol' in message)\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have scared someone recently') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False

            return m.author.id == global_data.epic_rpg_id and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
        bot_message = await global_functions.encode_message(bot_answer)

        return (bot_answer, bot_message,)

    # --- Commands ---
    # Sleepy potion (change command name according to event)
    @commands.command(aliases=('halloween',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def hal(self, ctx, *args):

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':

            if args:
                args_full = ''
                for arg in args:
                    args_full = f'{args_full}{arg}'

                if args_full == 'usesleepypotion':
                    settings = await database.get_settings(ctx, 'hunt') # Only need reminders_on
                    if settings is not None:
                        reminders_on = settings[0]
                    else:
                        return
                    if reminders_on != 0:
                        try:
                            task_status = self.bot.loop.create_task(self.get_sleepy_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)

                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Sleepy potion detection: {message}')

                                        if  ((message.find(ctx_author) > -1) and (message.find('has slept for a day') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have a sleepy potion') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):

                                            bot_answer = msg
                                            bot_message = message
                                    except Exception as e:
                                        await ctx.send(f'Error reading message history: {e}')

                            if bot_message == None:
                                task_result = await task_status
                                if not task_result == None:
                                    bot_answer = task_result[0]
                                    bot_message = task_result[1]
                                else:
                                    await ctx.send('Sleepy potion detection timeout.')
                                    return

                            if bot_message.find('has slept for a day') > -1:
                                status = await global_functions.reduce_reminder_time(ctx, 86400)
                                if not status == 'ok':
                                    await ctx.send(status)
                                await bot_answer.add_reaction(emojis.navi)
                            # Ignore if htey don't have a potion
                            elif bot_message.find(f'you don\'t have a sleepy potion') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore in the middle of command error
                            elif bot_message.find('so no chance to scare lol') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore anti spam embed
                            elif bot_message.find('Huh please don\'t spam') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore failed Epic Guard event
                            elif bot_message.find('is now in the jail!') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                await bot_answer.add_reaction(emojis.rip)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return

                        except asyncio.TimeoutError as error:
                            await ctx.send('Sleepy Potion detection timeout.')
                            return
                        except Exception as e:
                            global_data.logger.error(f'Sleepy potion detection error: {e}')
                            return

                if args_full.startswith('boo') and ctx.message.mentions:
                    settings = await database.get_settings(ctx, 'hunt') # Only need reminders_on
                    if settings is not None:
                        reminders_on = settings[0]
                        user_donor_tier = int(settings[1])
                        boo_message = 'Hey! It\'s time for `rpg hal boo`!'
                    else:
                        return
                    if reminders_on != 0:
                        try:
                            task_status = self.bot.loop.create_task(self.get_boo_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)

                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Boo detection: {message}')

                                        if ((message.find(ctx_author) > -1) and (message.find('failed to scare') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('scared') > -1))\
                                        or ('bots cannot be scared' in message)\
                                        or ('you can\'t scare yourself lol' in message)\
                                        or ('so no chance to scare lol' in message)\
                                        or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have scared someone recently') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                                            bot_answer = msg
                                            bot_message = message
                                    except Exception as e:
                                        await ctx.send(f'Error reading message history: {e}')

                            if bot_message == None:
                                task_result = await task_status
                                if not task_result == None:
                                    bot_answer = task_result[0]
                                    bot_message = task_result[1]
                                else:
                                    await ctx.send('Boo detection timeout.')
                                    return

                            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                            if bot_message.find(f'\'s cooldown') > 1:
                                timestring_start = bot_message.find('wait at least **') + 16
                                timestring_end = bot_message.find('**...', timestring_start)
                                timestring = bot_message[timestring_start:timestring_end]
                                timestring = timestring.lower()
                                time_left = await global_functions.parse_timestring(ctx, timestring)
                                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                                current_time = datetime.utcnow().replace(microsecond=0)
                                time_elapsed = current_time - bot_answer_time
                                time_elapsed_seconds = time_elapsed.total_seconds()
                                time_left = time_left-time_elapsed_seconds
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'boo', time_left, boo_message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                return

                            # Ignore bots
                            elif bot_message.find('bots cannot be scared') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore self scare
                            elif bot_message.find('you can\'t scare yourself lol') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore anti spam embed
                            elif bot_message.find('Huh please don\'t spam') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore failed Epic Guard event
                            elif bot_message.find('is now in the jail!') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                await bot_answer.add_reaction(emojis.rip)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return

                            # Calculate cooldown
                            cooldown = 7200
                            donor_affected = 0
                            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                            current_time = datetime.utcnow().replace(microsecond=0)
                            time_elapsed = current_time - bot_answer_time
                            time_elapsed_seconds = time_elapsed.total_seconds()
                            if donor_affected == 1:
                                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]-time_elapsed_seconds
                            else:
                                time_left = cooldown-time_elapsed_seconds

                            # Save task to database
                            write_status = await global_functions.write_reminder(self.bot, ctx, 'boo', time_left, boo_message)

                            # Add reaction
                            if not write_status == 'aborted':
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.DEBUG_MODE == 'ON':
                                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')

                        except asyncio.TimeoutError as error:
                            await ctx.send('Boo detection timeout.')
                            return
                        except Exception as e:
                            global_data.logger.error(f'Boo detection error: {e}')
                            return

# Initialization
def setup(bot):
    bot.add_cog(sleepypotionCog(bot))