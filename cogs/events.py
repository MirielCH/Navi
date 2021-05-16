# events.py

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

# events commands (cog)
class eventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Events detection
    async def get_events_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Duel detection: {message}')
                
                if  ((message.find(f'Normal events') > -1) and (message.find(f'Guild ranking') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
    # Events (cooldown detection only)
    @commands.command(aliases=('events',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def event(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            try:
                settings = await database.get_settings(ctx, 'events')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        default_message = settings[1]
                        bigarena_enabled = settings[2]
                        lottery_enabled = settings[3]
                        nsmb_enabled = settings[5]
                        pet_enabled = settings[6]
                        lottery_message = settings[4]
                        pet_message = settings[7]
                        race_enabled = settings[8]
                        
                        if not ((bigarena_enabled == 0) and (lottery_enabled == 0) and (nsmb_enabled == 0) and (pet_enabled == 0) and (race_enabled == 0)):
                            task_status = self.bot.loop.create_task(self.get_events_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)
                                        
                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Events detection: {message}')
                                        
                                        if  ((message.find(f'Normal events') > -1) and (message.find(f'Guild ranking') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
                                    await ctx.send('Events detection timeout.')
                                    return

                            # Check if event list, if yes, extract all the timestrings
                            if bot_message.find('Normal events') > 1:
                                
                                cooldowns = []
                                
                                if bigarena_enabled == 1:
                                    if bot_message.find('Big arena**: ') > -1:
                                        arena_start = bot_message.find('Big arena**: ') + 13
                                        arena_end = bot_message.find('s', arena_start) + 1
                                        arena = bot_message[arena_start:arena_end]
                                        arena = arena.lower()
                                        arena_message = global_data.arena_message
                                        cooldowns.append(['bigarena',arena,arena_message,])
                                if lottery_enabled == 1:
                                    if bot_message.find('Lottery**: ') > -1:
                                        lottery_start = bot_message.find('Lottery**: ') + 11
                                        lottery_end = bot_message.find('s', lottery_start) + 1
                                        lottery = bot_message[lottery_start:lottery_end]
                                        lottery = lottery.lower()
                                        if lottery_message == None:
                                            lottery_message = default_message.replace('%','rpg buy lottery ticket')
                                        else:
                                            lottery_message = lottery_message.replace('%','rpg buy lottery ticket')
                                        cooldowns.append(['lottery',lottery,lottery_message,])
                                if nsmb_enabled == 1:
                                    if bot_message.find('"mini" boss**: ') > -1:
                                        miniboss_start = bot_message.find('"mini" boss**: ') + 15
                                        miniboss_end = bot_message.find('s', miniboss_start) + 1
                                        miniboss = bot_message[miniboss_start:miniboss_end]
                                        miniboss = miniboss.lower()
                                        miniboss_message = global_data.miniboss_message
                                        cooldowns.append(['nsmb',miniboss,miniboss_message,])
                                if pet_enabled == 1:
                                    if bot_message.find('tournament**: ') > -1:
                                        pet_start = bot_message.find('tournament**: ') + 14
                                        pet_end = bot_message.find('s', pet_start) + 1
                                        tournament = bot_message[pet_start:pet_end]
                                        tournament = tournament.lower()
                                        pet_message = global_data.tournament_message
                                        cooldowns.append(['pett',tournament,pet_message,])
                                if race_enabled == 1:
                                    if bot_message.find('race**: ') > -1:
                                        race_start = bot_message.find('race**: ') + 8
                                        race_end = bot_message.find('s', race_start) + 1
                                        race = bot_message[race_start:race_end]
                                        race = race.lower()
                                        race_message = global_data.race_message
                                        cooldowns.append(['race',race,race_message,])
                                
                                write_status_list = []
                                
                                for cooldown in cooldowns:
                                    activity = cooldown[0]
                                    timestring = cooldown[1]
                                    message = cooldown[2]
                                    time_left = await global_functions.parse_timestring(ctx, timestring)
                                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)                
                                    current_time = datetime.utcnow().replace(microsecond=0)
                                    time_elapsed = current_time - bot_answer_time
                                    time_elapsed_seconds = time_elapsed.total_seconds()
                                    time_left = time_left-time_elapsed_seconds
                                    if activity == 'pett':
                                        time_left = time_left + 60 #The event is somethings not perfectly on point, so I added a minute
                                    if time_left > 1:
                                        if activity in ('bigarena','nsmb','race','pett'):
                                            write_status = await global_functions.write_reminder(self.bot, ctx, activity, time_left, message, True, True)
                                        else:
                                            write_status = await global_functions.write_reminder(self.bot, ctx, activity, time_left, message, True)
                                        if write_status in ('inserted','scheduled','updated','ignored',):
                                            write_status_list.append('OK')
                                        else:
                                            write_status_list.append('Fail')
                                    else:
                                        write_status_list.append('OK')
                                    
                                if not 'Fail' in write_status_list:                       
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await ctx.send(f'Something went wrong here. {write_status_list} {cooldowns}')
                                        await bot_answer.add_reaction(emojis.error)
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
                        else:
                            return
                    else:
                        return
                else:
                    return
            
            except asyncio.TimeoutError as error:
                await ctx.send('Event detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Event detection error: {e}')
                return 
        
# Initialization
def setup(bot):
    bot.add_cog(eventsCog(bot))