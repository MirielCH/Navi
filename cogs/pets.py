# pets.py

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

# pet commands (cog)
class petsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Pet detection
    async def get_pet_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Pet detection: {message}')
                
                if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet(s) are you trying to select?') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'this pet is already in an adventure!') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):
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
    # Pets
    @commands.command(aliases=('pets',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def pet(self, ctx, *args):
    
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            if args:
                if len(args) in (2,3):
                    arg1 = args[0]
                    arg1 = arg1.lower()
                    pet_action = args[1]
                    pet_action = pet_action.lower()
                    if len(args) == 3:
                        pet_id = args[2]
                        if pet_id.lower() == 'epic':
                            return
                        pet_id = pet_id.upper()
                    else:
                        pet_id = ''
                    if (arg1 in ('adv', 'adventure',)) and pet_action in ('find', 'learn', 'drill',) and not pet_id == '':
                        command = 'rpg pet adventure'
                
                        try:
                            settings = await database.get_settings(ctx, 'pet')
                            if not settings == None:
                                reminders_on = settings[0]
                                if not reminders_on == 0:
                                    user_donor_tier = int(settings[2])
                                    if user_donor_tier > 3:
                                        user_donor_tier = 3
                                    pet_enabled = int(settings[3])
                                    pet_message = settings[4]
                                    
                                    # Set message to send          
                                    if pet_message == None:
                                        pet_message = global_data.pet_message.replace('%',command).replace('$',pet_id)
                                    else:
                                        pet_message = pet_message.replace('%',command).replace('$',pet_id)
                                    
                                    if not pet_enabled == 0:
                                        task_status = self.bot.loop.create_task(self.get_pet_message(ctx))
                                        bot_message = None
                                        message_history = await ctx.channel.history(limit=50).flatten()
                                        for msg in message_history:
                                            if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                                try:
                                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                                    message = await global_functions.encode_message(msg)
                                                    
                                                    if global_data.DEBUG_MODE == 'ON':
                                                        global_data.logger.debug(f'Pet adventure detection: {message}')
                                                    
                                                    if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet(s) are you trying to select?') > -1))\
                                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'this pet is already in an adventure!') > -1))\
                                                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                                    or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                                                    or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                                    or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):    
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
                                                await ctx.send('Pet adventure detection timeout.')
                                                return

                                        # Check if pet adventure started overview, if yes, read the time and update/insert the reminder
                                        if bot_message.find('Your pet has started an adventure and will be back') > -1:
                                            timestring_start = bot_message.find('back in **') + 10
                                            timestring_end = bot_message.find('**!', timestring_start)
                                            timestring = bot_message[timestring_start:timestring_end]
                                            timestring = timestring.lower()
                                            time_left = await global_functions.parse_timestring(ctx, timestring)
                                            bot_answer_time = bot_answer.created_at.replace(microsecond=0)                
                                            current_time = datetime.utcnow().replace(microsecond=0)
                                            time_elapsed = current_time - bot_answer_time
                                            time_elapsed_seconds = time_elapsed.total_seconds()
                                            time_left = time_left-time_elapsed_seconds
                                            write_status = await global_functions.write_reminder(self.bot, ctx, f'pet-{pet_id}', time_left, pet_message, True)
                                            if write_status in ('inserted','scheduled','updated'):
                                                await bot_answer.add_reaction(emojis.navi)
                                            else:
                                                if global_data.DEBUG_MODE == 'ON':
                                                    await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that max amount of pets is on adventures
                                        elif bot_message.find('you cannot send another pet') > 1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that ID is wrong
                                        elif bot_message.find('what pet(s) are you trying to select?') > 1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that pet is already on adventure
                                        elif bot_message.find('this pet is already in an adventure') > 1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore time traveler instant pet return
                                        elif bot_message.find('IT CAME BACK INSTANTLY!') > 1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            await bot_answer.add_reaction(emojis.timetraveler)
                                            return
                                        # Ignore error that pets are not unlocked yet
                                        elif bot_message.find('unlocked after second') > 1:
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
                                    else:
                                        return
                                else:
                                    return
                            else:
                                return    
                        except asyncio.TimeoutError as error:
                            await ctx.send('Pet adventure detection timeout.')
                        except Exception as e:
                            global_data.logger.error(f'Pet adventure detection error: {e}')
                            return  
                    elif arg1 in ('tournament'):
                        try:
                            settings = await database.get_settings(ctx, 'pet')
                            if not settings == None:
                                reminders_on = settings[0]
                                if not reminders_on == 0:
                                    user_donor_tier = int(settings[2])
                                    if user_donor_tier > 3:
                                        user_donor_tier = 3
                                    pet_enabled = int(settings[3])
                                    
                                    # Set message to send         
                                    pet_message = global_data.tournament_message
                                    
                                    if not pet_enabled == 0:
                                        task_status = self.bot.loop.create_task(self.get_pet_message(ctx))
                                        bot_message = None
                                        message_history = await ctx.channel.history(limit=50).flatten()
                                        for msg in message_history:
                                            if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                                try:
                                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                                    message = await global_functions.encode_message(msg)
                                                    
                                                    if global_data.DEBUG_MODE == 'ON':
                                                        global_data.logger.debug(f'Pet tournament detection: {message}')
                                                    
                                                    if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet(s) are you trying to select?') > -1))\
                                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'this pet is already in an adventure!') > -1))\
                                                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                                    or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                                                    or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                                    or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):                                                        
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
                                                await ctx.send('Pet tournament detection timeout.')
                                                return

                                        # Check if pet tournament started, if yes, read the time and update/insert the reminder
                                        if bot_message.find('pet successfully sent to the pet tournament!') > -1:
                                            timestring_start = bot_message.find('is in **') + 8
                                            timestring_end = bot_message.find('**,', timestring_start)
                                            timestring = bot_message[timestring_start:timestring_end]
                                            timestring = timestring.lower()
                                            time_left = await global_functions.parse_timestring(ctx, timestring)
                                            bot_answer_time = bot_answer.created_at.replace(microsecond=0)                
                                            current_time = datetime.utcnow().replace(microsecond=0)
                                            time_elapsed = current_time - bot_answer_time
                                            time_elapsed_seconds = time_elapsed.total_seconds()
                                            time_left = time_left-time_elapsed_seconds
                                            time_left = time_left + 60 #The event is somethings not perfectly on point, so I added a minute
                                            write_status = await global_functions.write_reminder(self.bot, ctx, f'pett', time_left, pet_message, True)
                                            if write_status in ('inserted','scheduled','updated'):
                                                await bot_answer.add_reaction(emojis.navi)
                                            else:
                                                if global_data.DEBUG_MODE == 'ON':
                                                    await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that pet tournament is already active
                                        elif bot_message.find('You cannot send another pet to the **pet tournament**!') > -1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that ID is wrong
                                        elif bot_message.find('what pet are you trying to select?') > 1:
                                            if global_data.DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                            return
                                        # Ignore error that pets are not unlocked yet
                                        elif bot_message.find('unlocked after second') > 1:
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
                                    else:
                                        return
                                else:
                                    return
                            else:
                                return
                        except asyncio.TimeoutError as error:
                            await ctx.send('Pet tournament detection timeout.')
                            return
                        except Exception as e:
                            global_data.logger.error(f'Pet tournament detection error: {e}')
                            return    
        
# Initialization
def setup(bot):
    bot.add_cog(petsCog(bot))