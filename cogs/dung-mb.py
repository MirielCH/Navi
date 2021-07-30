# dung-mb.py

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

# Dungeon / Miniboss commands (cog)
class dungmbCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Dungeon / Miniboss detection
    async def get_dungmb_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Dungeon / Miniboss detection: {message}')

                if  ((message.find(f'\'s cooldown') > -1) and (message.find('been in a fight with a boss recently') > -1))\
                or (message.find('ARE YOU SURE YOU WANT TO ENTER') > -1)\
                or (message.find('Requirements to enter the dungeon') > -1)\
                or (message.find(f'{ctx_author}\'s miniboss') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot enter a dungeon alone') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('bot is going to restart soon') > -1))\
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
    # Dungeon / Miniboss (cooldown detection only)
    @commands.command(aliases=('dung','miniboss',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def dungeon(self, ctx, *args):

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            command = 'rpg dungeon / miniboss'

            try:
                settings = await database.get_settings(ctx, 'dungmb')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[2]
                        dungmb_enabled = int(settings[3])
                        dungmb_message = settings[4]

                        # Set message to send
                        if dungmb_message == None:
                            dungmb_message = default_message.replace('%',command)
                        else:
                            dungmb_message = dungmb_message.replace('%',command)

                        if not dungmb_enabled == 0:
                            task_status = self.bot.loop.create_task(self.get_dungmb_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)

                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Dungeon / Miniboss detection: {message}')

                                        if  ((message.find(f'\'s cooldown') > -1) and (message.find('been in a fight with a boss recently') > -1))\
                                        or (message.find('ARE YOU SURE YOU WANT TO ENTER') > -1)\
                                        or (message.find('Requirements to enter the dungeon') > -1)\
                                        or (message.find(f'{ctx_author}\'s miniboss') > -1)\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot enter a dungeon alone') > -1))\
                                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('bot is going to restart soon') > -1))\
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
                                    await ctx.send('Dungeon / Miniboss detection timeout.')
                                    return

                            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if bot_message.find(f'{ctx_author}\'s cooldown') > -1:
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
                                write_status = await global_functions.write_reminder(self.bot, ctx, 'dungmb', time_left, dungmb_message, True)
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
                await ctx.send('Dungeon / Miniboss detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Dungeon / Miniboss detection error: {e}')
                return

# Initialization
def setup(bot):
    bot.add_cog(dungmbCog(bot))