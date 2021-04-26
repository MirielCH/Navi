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
                    global_data.logger.debug(f'Open detection: {message}')
                
                if  ((message.find(ctx_author) > -1) and (message.find('has slept for a day') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have a sleepy potion') > -1))\
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
    # Sleepy potion (change command name according to event)
    @commands.command(aliases=('easter',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def egg(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            
            if args:
                args_full = ''
                for arg in args:
                    args_full = f'{args_full}{arg}'
                
                if args_full == 'usesleepypotion':
                    settings = await database.get_settings(ctx, 'hunt') # Only need reminders_on
                    if not settings == None:
                        reminders_on = settings[0]
                    else:
                        return
            
                if not reminders_on == 0:
                    try:
                        task_status = self.bot.loop.create_task(self.get_sleepy_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == 555955826880413696) and (msg.created_at > ctx.message.created_at):
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
                        if global_data.DEBUG_MODE == 'ON':
                            await ctx.send('Sleepy Potion detection timeout.')
                        return    
                else:
                    return
            else:
                return
        else:
            return
        
# Initialization
def setup(bot):
    bot.add_cog(sleepypotionCog(bot))