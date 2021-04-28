# quest.py

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

# quest commands (cog)
class questCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Quest detection
    async def get_quest_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Quest detection: {message}')
                
                if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('FIRST WAVE') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('epic quest cancelled') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you did not accept the quest') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find(f'If you don\'t want this quest anymore') > -1))\
                or ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('Are you ready to start the EPIC quest') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or (message.find('You need a **special horse** to do this') > -1):
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
    # Quest
    @commands.command(aliases=('quest',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def epic(self, ctx, *args):

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':     
            command = 'rpg quest'
            if args:
                arg = args[0]
                arg = arg.lower()
                invoked = ctx.invoked_with
                invoked = invoked.lower()
                if invoked == 'epic':
                    if arg == 'quest':
                        command = 'rpg epic quest'
                    else:
                        return
            try:
                settings = await database.get_settings(ctx, 'quest')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[2]
                        quest_enabled = int(settings[3])
                        quest_message = settings[4]
                        
                        # Set message to send          
                        if quest_message == None:
                            quest_message = default_message.replace('%',command)
                        else:
                            quest_message = quest_message.replace('%',command)
                        
                        # Wait for bot message
                        if not quest_enabled == 0:
                            epic_quest = False
                            quest_declined = None
                            
                            task_status = self.bot.loop.create_task(self.get_quest_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == 555955826880413696) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)
                                        
                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Hunt detection: {message}')
                                        
                                        if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('FIRST WAVE') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('epic quest cancelled') > -1))\
                                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you did not accept the quest') > -1))\
                                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find(f'If you don\'t want this quest anymore') > -1))\
                                        or ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('Are you ready to start the EPIC quest') > -1))\
                                        or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                        or (message.find('You need a **special horse** to do this') > -1):
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
                                    await ctx.send('Quest detection timeout.')
                                    return

                            # Check what quest it is and if normal quest if the user accepts or denies the quest (different cooldowns)
                            if (bot_message.find('Are you looking for a quest?') > -1) or (bot_message.find('Are you ready to start the EPIC quest') > -1):
                                message = await self.get_quest_message(ctx)
                                bot_answer = message[0]
                                bot_message = message[1]
                                
                                if bot_message.find('you did not accept the quest') > -1:
                                    quest_declined = True
                                elif bot_message.find('got a **new quest**!') > -1:
                                    quest_declined = False
                                elif bot_message.find('FIRST WAVE') > -1:
                                    epic_quest = True
                                else:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await ctx.send('I could not find out if the quest was accepted or declined.')
                                    return                   
                            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                            elif bot_message.find(f'\'s cooldown') > 1:
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
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'quest', time_left, quest_message, True)
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
                            # Ignore quest cancellation as it does not reset the cooldown
                            elif bot_message.find('epic quest cancelled') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error when trying to do epic quest with active quest
                            elif bot_message.find(f'You cannot do this if you have a pending quest!') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore active quest
                            elif bot_message.find(f'If you don\'t want this quest anymore') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore completed quest
                            elif bot_message.find(f'Completed!') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore trying epic quest without a special horse
                            elif bot_message.find('You need a **special horse** to do this') > -1:
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
                cooldown_data = await database.get_cooldown(ctx, 'quest')
                if epic_quest == True:
                    cooldown = int(cooldown_data[0])
                else:
                    if quest_declined == True:
                        cooldown = 3600
                    elif quest_declined == False or epic_quest == True:
                        cooldown = int(cooldown_data[0])
                    else:
                        global_data.logger.error(f'Quest detection error: Neither quest_declined nor epic_quest had a value that allowed me to determine what the user did. epic_quest: {epic_quest}, quest_declined: {quest_declined}')
                        return
                
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
                write_status = await global_functions.write_reminder(self.bot, ctx, 'quest', time_left, quest_message)
                
                # Add reaction
                if not write_status == 'aborted':
                    await bot_answer.add_reaction(emojis.navi)
                else:
                    if global_data.DEBUG_MODE == 'ON':
                        await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            except asyncio.TimeoutError as error:
                await ctx.send('Quest detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Quest detection error: {e}')
                return   
        else:
            return
        
# Initialization
def setup(bot):
    bot.add_cog(questCog(bot))