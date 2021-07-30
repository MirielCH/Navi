# buy.py

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

# buy commands (cog)
class buyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Buy detection
    async def get_buy_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Work detection: {message}')

                if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
                or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('check the name of the item again') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you have to be level') > -1))\
                or (message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough coins to do this') > -1))\
                or (message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
    # Buy
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def buy(self, ctx, *args):

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ' and args:
            command = 'rpg buy lootbox'
            arg1 = ''
            arg2 = ''
            arg1 = args[0]
            if len(args) >= 2:
                arg2 = args[1]

            if arg1 == 'lottery' and arg2 == 'ticket':
                command = self.bot.get_command(name='lottery')
                if not command == None:
                    await command.callback(command.cog, ctx, args)
                return

            elif (len(args) in (1,2)) and ((arg1 in ('lb','lootbox',)) or (arg2 in ('lb','lootbox',))):
                try:
                    settings = await database.get_settings(ctx, 'lootbox')
                    if not settings == None:
                        reminders_on = settings[0]
                        if not reminders_on == 0:
                            user_donor_tier = int(settings[1])
                            if user_donor_tier > 3:
                                user_donor_tier = 3
                            default_message = settings[2]
                            lb_enabled = int(settings[3])
                            lb_message = settings[4]

                            # Set message to send
                            if lb_message == None:
                                lb_message = default_message.replace('%',command)
                            else:
                                lb_message = lb_message.replace('%',command)

                            if not lb_enabled == 0:
                                task_status = self.bot.loop.create_task(self.get_buy_message(ctx))
                                bot_message = None
                                message_history = await ctx.channel.history(limit=50).flatten()
                                for msg in message_history:
                                    if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                        try:
                                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                            message = await global_functions.encode_message(msg)

                                            if global_data.DEBUG_MODE == 'ON':
                                                global_data.logger.debug(f'Buy detection: {message}')

                                            if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
                                            or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                                            or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('check the name of the item again') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you have to be level') > -1))\
                                            or (message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > -1)\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough coins to do this') > -1))\
                                            or (message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
                                        await ctx.send('Buy detection timeout.')
                                        return

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
                                    write_status = await global_functions.write_reminder(self.bot, ctx, 'lootbox', time_left, lb_message, True)
                                    if write_status in ('inserted','scheduled','updated'):
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
                                        if global_data.DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore error message that appears if you already own a lootbox
                                elif bot_message.find('You can\'t carry more than 1 lootbox at once!') > -1:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore error message that you are too low level to buy a lootbox
                                elif bot_message.find('you have to be level') > -1:
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore not enough money info
                                elif (bot_message.find(f'you don\'t have enough coins to do this') > -1) or (bot_message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
                                # Ignore error when trying to buy omegas or godlys
                                elif bot_message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > 1:
                                    await bot_answer.add_reaction(emojis.sad)
                                    return
                            else:
                                return
                        else:
                            return
                    else:
                        return

                    # Calculate cooldown
                    cooldown_data = await database.get_cooldown(ctx, 'lootbox')
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
                    write_status = await global_functions.write_reminder(self.bot, ctx, 'lootbox', time_left, lb_message)

                    # Add reaction
                    if not write_status == 'aborted':
                        await bot_answer.add_reaction(emojis.navi)
                    else:
                        if global_data.DEBUG_MODE == 'ON':
                            await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                except asyncio.TimeoutError as error:
                    await ctx.send('Buy detection timeout.')
                    return
                except Exception as e:
                    global_data.logger.error(f'Buy detection error: {e}')
                    return
            else:
                return
        else:
            return

# Initialization
def setup(bot):
    bot.add_cog(buyCog(bot))