# open.py

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

# open commands (cog)
class openCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Open detection
    async def get_open_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Open detection: {message}')
                
                if  ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have any of this lootbox type') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what lootbox are you trying to open?') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                or (message.find(f'Huh you don\'t have that many of this lootbox type') > -1)\
                or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('lootbox opened!') > -1))\
                or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('You were about to open a nice lootbox') > -1))\
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
    # Open
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def open(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            
            if args:
                settings = await database.get_settings(ctx, 'rubies')
                if not settings == None:
                    rubies_db = settings[0]
                    ruby_counter = settings[1]
                    reminders_on = settings[2]
                else:
                    return
            
                if not reminders_on == 0 and not ruby_counter == 0:
                    try:
                        task_status = self.bot.loop.create_task(self.get_open_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await global_functions.encode_message(msg)
                                    
                                    if global_data.DEBUG_MODE == 'ON':
                                        global_data.logger.debug(f'Open detection: {message}')
                                    
                                    if  ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have any of this lootbox type') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what lootbox are you trying to open?') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                                    or (message.find(f'Huh you don\'t have that many of this lootbox type') > -1)\
                                    or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('lootbox opened!') > -1))\
                                    or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('You were about to open a nice lootbox') > -1))\
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
                                await ctx.send('Open detection timeout.')
                                return
                        
                        if bot_message.find('lootbox opened!') > -1:
                            if bot_message.find('<:ruby:') > -1:
                                rubies_end = bot_message.find('<:ruby:') -1
                                rubies_start = bot_message.rfind('+', 0, rubies_end) + 1
                                rubies = bot_message[rubies_start:rubies_end]
                                if rubies.isnumeric():
                                    rubies = rubies_db + int(rubies)
                                    await database.set_rubies(ctx, rubies)
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')
                            await bot_answer.add_reaction(emojis.navi)
                        # Ignore failed openings
                        elif (bot_message.find('of this lootbox type') > -1) or (bot_message.find('what lootbox') > -1):
                            if global_data.DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore lootbox event
                        elif (bot_message.find('You were about to open a nice lootbox') > -1):
                            if global_data.DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error message if wrong name
                        elif bot_message.find('what are you doing??') > 1:
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
                        await ctx.send('Lootbox detection timeout.')
                        return
                    except Exception as e:
                        global_data.logger.error(f'Lootbox detection error: {e}')
                        return    
                else:
                    return
            else:
                return
        
# Initialization
def setup(bot):
    bot.add_cog(openCog(bot))