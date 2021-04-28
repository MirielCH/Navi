# duel.py

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

# duel commands (cog)
class duelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Duel detection
    async def get_duel_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Duel detection: {message}')
                
                if  ((message.find(f'\'s cooldown') > -1) and (message.find('You have been in a duel recently') > -1))\
                or ((message.find(f'{ctx_author}\'s duel') > -1) and (message.find('Profit:') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Duel cancelled') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('sent a Duel request') > -1))\
                or (message.find(f'Huh, next time be sure to say who you want to duel') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
            
    
    
    # --- Commands ---
    # Duel (cooldown detection only)
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def duel(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            command = 'rpg duel'
                
            try:
                settings = await database.get_settings(ctx, 'duel')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[2]
                        duel_enabled = int(settings[3])
                        duel_message = settings[4]
                        
                        # Set message to send          
                        if duel_message == None:
                            duel_message = default_message.replace('%',command)
                        else:
                            duel_message = duel_message.replace('%',command)
                        
                        if not duel_enabled == 0:
                            task_status = self.bot.loop.create_task(self.get_duel_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == 555955826880413696) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)
                                        
                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Duel detection: {message}')
                                        
                                        if  ((message.find(f'\'s cooldown') > -1) and (message.find('You have been in a duel recently') > -1))\
                                        or ((message.find(f'{ctx_author}\'s duel') > -1) and (message.find('Profit:') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('Duel cancelled') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('sent a Duel request') > -1))\
                                        or (message.find(f'Huh, next time be sure to say who you want to duel') > -1)\
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
                                    await ctx.send('Duel detection timeout.')
                                    return

                            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if bot_message.find(f'{ctx_author}\'s cooldown') > 1:
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
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'duel', time_left, duel_message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
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
                await ctx.send('Duel detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Duel detection error: {e}')
                return   
        
# Initialization
def setup(bot):
    bot.add_cog(duelCog(bot))