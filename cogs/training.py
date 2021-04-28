# training.py

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

# training commands (cog)
class trainingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Training detection
    async def get_training_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Training detection: {message}')
                
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
            
            return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
        bot_message = await global_functions.encode_message(bot_answer)
            
        return (bot_answer, bot_message,)
    
    # Training answer detection
    async def get_training_answer_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Training detection: {message}')
                
                if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            
            return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout_longer)
        bot_message = await global_functions.encode_message(bot_answer)
            
        return (bot_answer, bot_message,)
            
    
    
    # --- Commands ---
    # Training
    @commands.command(aliases=('tr','ultraining','ultr',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def training(self, ctx, *args):

        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()
        
        if prefix.lower() == 'rpg ':
            if args:
                if invoked == 'ascended':
                    args = args[0]
                    arg_command = args[0]
                    if arg_command in ('tr', 'training',):
                        command = 'rpg ascended training'
                    elif arg_command in ('ultr', 'ultraining',):
                        command = 'rpg ascended ultraining'
                        
                    args.pop(0)   
                else:
                    if invoked in ('tr', 'training',):
                        command = 'rpg training'
                    elif invoked in ('ultr', 'ultraining',):
                        command = 'rpg ultraining'
                    
                        if len(args) >= 1 and command.find('ultraining') > -1:
                            arg = args[0]
                            if arg in ('p','progress',):
                                return
            else:
                if invoked in ('tr', 'training',):
                    command = 'rpg training'
                elif invoked in ('ultr', 'ultraining',):
                    command = 'rpg ultraining'
                
            try:
                settings = await database.get_settings(ctx, 'training')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[2]
                        tr_enabled = int(settings[3])
                        tr_message = settings[4]
                        rubies = settings[5]
                        ruby_counter = settings[6]
                        
                        # Set message to send          
                        if tr_message == None:
                            tr_message = default_message.replace('%',command)
                        else:
                            tr_message = tr_message.replace('%',command)
                        
                        task_status = self.bot.loop.create_task(self.get_training_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == 555955826880413696) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await global_functions.encode_message(msg)
                                    
                                    if global_data.DEBUG_MODE == 'ON':
                                        global_data.logger.debug(f'Training detection: {message}')
                                    
                                    if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                                    or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1))\
                                    or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                                    or ((message.find(ctx_author) > -1) and (message.find('is training in') > -1))\
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
                                await ctx.send('Training detection timeout.')
                                return

                        # Trigger ruby counter if necessary
                        if bot_message.find('is training in') > -1:
                            if bot_message.find('training in the mine') > -1:
                                if not ruby_counter == 0:
                                    await ctx.send(f'**{ctx.author.name}**, you have {rubies} {emojis.ruby} rubies.')
                            if not tr_enabled == 0:
                                message = await self.get_training_answer_message(ctx)
                                bot_answer = message[0]
                                bot_message = message[1]

                        if not tr_enabled == 0:
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
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'training', time_left, tr_message, True)
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
                else:
                    return
                
                # Calculate cooldown
                cooldown_data = await database.get_cooldown(ctx, 'training')
                cooldown = int(cooldown_data[0])
                donor_affected = int(cooldown_data[1])
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)                
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_elapsed_seconds = time_elapsed.total_seconds()
                if donor_affected == 1:
                    time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]-time_elapsed_seconds
                else:
                    time_left = cooldown-time_elapsed_seconds
                
                # Save task to database
                write_status = await global_functions.write_reminder(self.bot, ctx, 'training', time_left, tr_message)
                
                # Add reaction
                if not write_status == 'aborted':
                    await bot_answer.add_reaction(emojis.navi)
                else:
                    if global_data.DEBUG_MODE == 'ON':
                        await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            except asyncio.TimeoutError as error:
                await ctx.send('Training detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Training detection error: {e}')
                return     
        
# Initialization
def setup(bot):
    bot.add_cog(trainingCog(bot))