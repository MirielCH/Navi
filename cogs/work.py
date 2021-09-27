# work.py

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

# work commands (cog)
class workCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Work detection
    async def get_work_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Work detection: {message}')

                if  (((message.find(f'{ctx_author}** got ') > -1) or (message.find(f'{ctx_author}** GOT ') > -1)) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                or (message.find('RUBY') > -1) or (message.find('ruby') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('You slept well and the items respawned') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
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
    # Work
    @commands.command(aliases=('axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor','greenhouse','mine','pickaxe','drill','dynamite',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def chop(self, ctx, *args):

        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()

        if prefix.lower() == 'rpg ':
            if invoked == 'ascended':
                args = args[0]
                command = f'rpg ascended {args[0].lower()}'
            else:
                command = f'rpg {invoked.lower()}'

            try:
                settings = await database.get_settings(ctx, 'work')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[2]
                        work_enabled = int(settings[3])
                        work_message = settings[4]
                        rubies_db = settings[5]
                        ruby_counter = settings[6]

                        task_status = self.bot.loop.create_task(self.get_work_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await global_functions.encode_message(msg)

                                    if global_data.DEBUG_MODE == 'ON':
                                        global_data.logger.debug(f'Work detection: {message}')

                                    if  (((message.find(f'{ctx_author}** got ') > -1) or (message.find(f'{ctx_author}** GOT ') > -1)) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                                    or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                                    or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                                    or (message.find('RUBY') > -1) or (message.find('ruby') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                                    and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                                    or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                                    or ((message.find(ctx_author) > -1) and (message.find('You slept well and the items respawned') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
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
                                await ctx.send('Work detection timeout.')
                                return

                        # Set message to send
                        if work_message == None:
                            work_message = default_message.replace('%',command)
                        else:
                            work_message = work_message.replace('%',command)

                        # Check for rubies
                        if not ruby_counter == 0:
                            if (bot_message.lower().find('<:ruby:') > -1):
                                rubies_start = bot_message.lower().find(' got ') + 5
                                rubies_end = bot_message.lower().find('<:ruby:') - 1
                                rubies = bot_message[rubies_start:rubies_end]
                                if rubies.isnumeric():
                                    rubies = rubies_db + int(rubies)
                                    await database.set_rubies(ctx, rubies)
                                    await bot_answer.add_reaction(emojis.navi)
                                elif (bot_message.find('rubies in it') > -1):
                                    rubies_start = bot_message.find('One of them had ') + 16
                                    rubies_end = bot_message.find('<:ruby:') - 1
                                    rubies = bot_message[rubies_start:rubies_end]
                                    if rubies.isnumeric():
                                        rubies = rubies_db + int(rubies)
                                        await database.set_rubies(ctx, rubies)
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
                                        await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')
                                else:
                                    await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')

                        if not work_enabled == 0:
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
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'work', time_left, work_message)
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
                    else:
                        return
                else:
                    return

                if not work_enabled == 0:
                    # Calculate cooldown
                    cooldown_data = await database.get_cooldown(ctx, 'work')
                    cooldown = int(cooldown_data[0])
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    current_time = datetime.utcnow().replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_elapsed_seconds = time_elapsed.total_seconds()
                    donor_affected = int(cooldown_data[1])
                    if donor_affected == 1:
                        time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]-time_elapsed_seconds
                    else:
                        time_left = cooldown-time_elapsed_seconds

                    # Save task to database
                    write_status = await global_functions.write_reminder(self.bot, ctx, 'work', time_left, work_message)

                    # Add reaction
                    if not write_status == 'aborted':
                        await bot_answer.add_reaction(emojis.navi)
                        if (bot_message.find(f'IS THIS A **DREAM**?????') > -1) or (bot_message.find(f'**HYPER** log') > -1) or (bot_message.find(f'**MEGA** log') > -1):
                            await bot_answer.add_reaction(emojis.fire)
                    else:
                        if global_data.DEBUG_MODE == 'ON':
                            await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                        return
            except asyncio.TimeoutError as error:
                await ctx.send('Work detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Work detection error: {e}')
                return

# Initialization
def setup(bot):
    bot.add_cog(workCog(bot))