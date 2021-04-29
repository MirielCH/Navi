# trade.py

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

# trade commands (cog)
class tradeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Trade detection
    async def get_trade_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Trade detection: {message}')
                
                if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('duh the amount has to be') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot trade rubies if you did not unlock area 5') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Alright! Our trade is done then') > -1))\
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
    # Trade
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def trade(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            
            if args:
                trade_id = args[0]
                trade_id = trade_id.lower()
                if trade_id in ('e','f'):
                    settings = await database.get_settings(ctx, 'rubies')
                    if not settings == None:
                        rubies_db = settings[0]
                        ruby_counter = settings[1]
                        reminders_on = settings[2]
                    else:
                        return
            
                    if not reminders_on == 0 and not ruby_counter == 0:
                        try:
                            task_status = self.bot.loop.create_task(self.get_trade_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)
                                        
                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Trade detection: {message}')
                                        
                                        if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('duh the amount has to be') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot trade rubies if you did not unlock area 5') > -1))\
                                        or ((message.find(ctx_author) > -1) and (message.find('Alright! Our trade is done then') > -1))\
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
                                    await ctx.send('Trade detection timeout.')
                                    return
                            
                            if bot_message.find('Our trade is done then') > -1:
                                rubies_start = bot_message.find('<:ruby:') + 28
                                if trade_id == 'f':
                                    rubies_end = bot_message.find(f'\'', rubies_start)
                                else:
                                    rubies_end = bot_message.find(f'\\', rubies_start) -1
                                rubies = bot_message[rubies_start:rubies_end]
                                if rubies.isnumeric():
                                    rubies = int(rubies)
                                    if trade_id == 'f':
                                        rubies = rubies_db + int(rubies)
                                    else:
                                        rubies = rubies_db - int(rubies)
                                        if rubies < 0:
                                            rubies == 0
                                    await database.set_rubies(ctx, rubies)
                                else:
                                    await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')
                            
                            # Ignore failed trades
                            elif (bot_message.find('duh the amount has to be') > -1) or (bot_message.find(f'you don\'t have enough') > -1) or (bot_message.find(f'you cannot trade rubies if you did not unlock area 5') > -1):
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
                            await ctx.send('Trade detection timeout.')
                            return
                        except Exception as e:
                            global_data.logger.error(f'Trade detection error: {e}')
                            return    
                    else:
                        return
                else:
                    return
                
                # Add reaction
                await bot_answer.add_reaction(emojis.navi)
        
# Initialization
def setup(bot):
    bot.add_cog(tradeCog(bot))