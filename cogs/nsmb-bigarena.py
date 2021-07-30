# nsmb-bigarena.py

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

# Big arena / Not so miniboss commands (cog)
class nsmbbaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Big arena / Not so mini boss detection
    async def get_nsmbba_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Big arena / Not so miniboss detection: {message}')

                if  ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **big arena** event') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **not so "mini" boss** event') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you are already registered!') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find('You have started an arena recently') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find('You have been in a fight with a boss recently') > -1)):
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
    # Big arena / Not so mini boss
    @commands.command(aliases=('not',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def big(self, ctx, *args):

        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()

        if prefix.lower() == 'rpg ':

            if args:
                full_args = ''
                if invoked == 'ascended':
                    args = args[0]
                    args.pop(0)
                for arg in args:
                    if arg == 'miniboss':
                        return
                    full_args = f'{full_args}{arg}'
            else:
                return

            if full_args in ('sominibossjoin','arenajoin',):
                if full_args == 'sominibossjoin':
                    event = 'nsmb'
                elif full_args == 'arenajoin':
                    event = 'bigarena'

                try:
                    settings = await database.get_settings(ctx, 'nsmb-bigarena')
                    if not settings == None:
                        reminders_on = settings[0]
                        if not reminders_on == 0:
                            user_donor_tier = int(settings[1])
                            if user_donor_tier > 3:
                                user_donor_tier = 3
                            arena_enabled = int(settings[2])
                            miniboss_enabled = int(settings[3])

                            # Set message to send
                            arena_message = global_data.arena_message
                            miniboss_message = global_data.miniboss_message

                            if not ((event == 'nsmb') and (miniboss_enabled == 0)) or ((event == 'bigarena') and (miniboss_enabled == 0)):
                                task_status = self.bot.loop.create_task(self.get_nsmbba_message(ctx))
                                bot_message = None
                                message_history = await ctx.channel.history(limit=50).flatten()
                                for msg in message_history:
                                    if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                        try:
                                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                            message = await global_functions.encode_message(msg)

                                            if global_data.DEBUG_MODE == 'ON':
                                                global_data.logger.debug(f'Big arena / Not so mini boss detection: {message}')

                                            if  ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **big arena** event') > -1))\
                                            or ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **not so "mini" boss** event') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you are already registered!') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                                            or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                            or ((message.find(f'{ctx_author}') > -1) and (message.find('You have started an arena recently') > -1))\
                                            or ((message.find(f'{ctx_author}') > -1) and (message.find('You have been in a fight with a boss recently') > -1)):
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
                                        await ctx.send('Big arena / Not so mini boss detection timeout.')
                                        return

                                # Check if event message with time in it, if yes, read the time and update/insert the reminder if necessary
                                if bot_message.find(f'The next event is in') > -1:
                                    timestring_start = bot_message.find('event is in **') + 14
                                    timestring_end = bot_message.find('**,', timestring_start)
                                    timestring = bot_message[timestring_start:timestring_end]
                                    timestring = timestring.lower()
                                    time_left = await global_functions.parse_timestring(ctx, timestring)
                                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                                    current_time = datetime.utcnow().replace(microsecond=0)
                                    time_elapsed = current_time - bot_answer_time
                                    time_elapsed_seconds = time_elapsed.total_seconds()
                                    time_left = time_left-time_elapsed_seconds
                                    if event == 'nsmb':
                                        write_status = await global_functions.write_reminder(self.bot, ctx, 'nsmb', time_left, miniboss_message, True)
                                    elif event == 'bigarena':
                                        write_status = await global_functions.write_reminder(self.bot, ctx, 'bigarena', time_left, arena_message, True)
                                    if write_status in ('inserted','scheduled','updated'):
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
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
                                # Ignore higher area error
                                elif bot_message.find('This command is unlocked in') > -1:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore ascended error
                                elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore error when another command is active
                                elif bot_message.find('end your previous command') > 1:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore if on cooldown
                                elif (bot_message.find('You have started an arena recently') > 1) or (bot_message.find('You have been in a fight with a boss recently') > 1):
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                            else:
                                return
                        else:
                            return
                    else:
                        return

                except asyncio.TimeoutError as error:
                    await ctx.send('Big arena / Not so mini boss detection timeout.')
                    return
                except Exception as e:
                    global_data.logger.error(f'Big arena / Not so mini boss detection error: {e}')
                    return

# Initialization
def setup(bot):
    bot.add_cog(nsmbbaCog(bot))