# cooldowns.py

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

# Cooldowns commands (cog)
class cooldownsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cooldowns detection
    async def get_cooldowns_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Dungeon / Miniboss detection: {message}')

                if  (message.find(f'{ctx_author}\'s cooldowns') > -1) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
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
    # Cooldowns
    @commands.command(aliases=('cd','cds','cooldowns',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def cooldown(self, ctx, *args):

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ':
            if args:
                arg = args[0]
                if not arg == 'max' and not (arg.find(f'ctx.author.id') > -1):
                    return

            try:
                settings = await database.get_settings(ctx, 'all')
                if not settings == None:
                    reminders_on = settings[1]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[2])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        default_message = settings[3]
                        adv_enabled = settings[9]
                        arena_enabled = settings[11]
                        daily_enabled = settings[13]
                        duel_enabled = settings[14]
                        dungmb_enabled = settings[15]
                        farm_enabled = settings[16]
                        horse_enabled = settings[17]
                        lb_enabled = settings[19]
                        quest_enabled = settings[23]
                        tr_enabled = settings[25]
                        vote_enabled = settings[26]
                        weekly_enabled = settings[27]
                        adv_message = settings[29]
                        arena_message = settings[31]
                        daily_message = settings[32]
                        duel_message = settings[33]
                        dungmb_message = settings[34]
                        farm_message = settings[35]
                        horse_message = settings[36]
                        lb_message = settings[38]
                        quest_message = settings[41]
                        tr_message = settings[42]
                        vote_message = settings[43]
                        weekly_message = settings[44]

                        if not ((adv_enabled == 0) and (daily_enabled == 0) and (lb_enabled == 0) and (quest_enabled == 0) and (tr_enabled == 0) and (weekly_enabled == 0) and (duel_enabled == 0) and (arena_enabled == 0) and (dungmb_enabled == 0) and (vote_enabled == 0)):
                            task_status = self.bot.loop.create_task(self.get_cooldowns_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)

                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Cooldowns detection: {message}')

                                        if  (message.find(f'{ctx_author}\'s cooldowns') > -1) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
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
                                    await ctx.send('Cooldowns detection timeout.')
                                    return

                            # Check if cooldown list, if yes, extract all the timestrings
                            if bot_message.find(f'\'s cooldowns') > 1:

                                cooldowns = []

                                if daily_enabled == 1:
                                    if bot_message.find('Daily`** (**') > -1:
                                        daily_start = bot_message.find('Daily`** (**') + 12
                                        daily_end = bot_message.find('s**', daily_start) + 1
                                        daily = bot_message[daily_start:daily_end]
                                        daily = daily.lower()
                                        if daily_message == None:
                                            daily_message = default_message.replace('%','rpg daily')
                                        else:
                                            daily_message = daily_message.replace('%','rpg daily')
                                        cooldowns.append(['daily',daily,daily_message,])
                                if weekly_enabled == 1:
                                    if bot_message.find('Weekly`** (**') > -1:
                                        weekly_start = bot_message.find('Weekly`** (**') + 13
                                        weekly_end = bot_message.find('s**', weekly_start) + 1
                                        weekly = bot_message[weekly_start:weekly_end]
                                        weekly = weekly.lower()
                                        if weekly_message == None:
                                            weekly_message = default_message.replace('%','rpg weekly')
                                        else:
                                            weekly_message = weekly_message.replace('%','rpg weekly')
                                        cooldowns.append(['weekly',weekly,weekly_message,])
                                if lb_enabled == 1:
                                    if bot_message.find('Lootbox`** (**') > -1:
                                        lb_start = bot_message.find('Lootbox`** (**') + 14
                                        lb_end = bot_message.find('s**', lb_start) + 1
                                        lootbox = bot_message[lb_start:lb_end]
                                        lootbox = lootbox.lower()
                                        if lb_message == None:
                                            lb_message = default_message.replace('%','rpg buy lootbox')
                                        else:
                                            lb_message = lb_message.replace('%','rpg buy lootbox')
                                        cooldowns.append(['lootbox',lootbox,lb_message,])
                                if adv_enabled == 1:
                                    if bot_message.find('Adventure`** (**') > -1:
                                        adv_start = bot_message.find('Adventure`** (**') + 16
                                        adv_end = bot_message.find('s**', adv_start) + 1
                                        adventure = bot_message[adv_start:adv_end]
                                        adventure = adventure.lower()
                                        if adv_message == None:
                                            adv_message = default_message.replace('%','rpg adventure')
                                        else:
                                            adv_message = adv_message.replace('%','rpg adventure')
                                        cooldowns.append(['adventure',adventure,adv_message,])
                                    elif bot_message.find('Adventure hardmode`** (**') > -1:
                                        adv_start = bot_message.find('Adventure hardmode`** (**') + 25
                                        adv_end = bot_message.find('s**', adv_start) + 1
                                        adventure = bot_message[adv_start:adv_end]
                                        adventure = adventure.lower()
                                        if adv_message == None:
                                            adv_message = default_message.replace('%','rpg adventure')
                                        else:
                                            adv_message = adv_message.replace('%','rpg adventure hardmode')
                                        cooldowns.append(['adventure',adventure,adv_message,])
                                if tr_enabled == 1:
                                    if bot_message.find('Training`** (**') > -1:
                                        tr_start = bot_message.find('Training`** (**') + 15
                                        tr_end = bot_message.find('s**', tr_start) + 1
                                        training = bot_message[tr_start:tr_end]
                                        training = training.lower()
                                        if tr_message == None:
                                            tr_message = default_message.replace('%','rpg training')
                                        else:
                                            tr_message = tr_message.replace('%','rpg training')
                                        cooldowns.append(['training',training,tr_message,])
                                    elif bot_message.find('Ultraining`** (**') > -1:
                                        tr_start = bot_message.find('Ultraining`** (**') + 17
                                        tr_end = bot_message.find('s**', tr_start) + 1
                                        training = bot_message[tr_start:tr_end]
                                        training = training.lower()
                                        if tr_message == None:
                                            tr_message = default_message.replace('%','rpg ultraining')
                                        else:
                                            tr_message = tr_message.replace('%','rpg training')
                                        cooldowns.append(['training',training,tr_message,])
                                if quest_enabled == 1:
                                    if bot_message.find('quest`** (**') > -1:
                                        quest_start = bot_message.find('quest`** (**') + 12
                                        quest_end = bot_message.find('s**', quest_start) + 1
                                        quest = bot_message[quest_start:quest_end]
                                        quest = quest.lower()
                                        if quest_message == None:
                                            quest_message = default_message.replace('%','rpg quest')
                                        else:
                                            quest_message = quest_message.replace('%','rpg quest')
                                        cooldowns.append(['quest',quest,quest_message,])
                                if duel_enabled == 1:
                                    if bot_message.find('Duel`** (**') > -1:
                                        duel_start = bot_message.find('Duel`** (**') + 11
                                        duel_end = bot_message.find('s**', duel_start) + 1
                                        duel = bot_message[duel_start:duel_end]
                                        duel = duel.lower()
                                        if duel_message == None:
                                            duel_message = default_message.replace('%','rpg duel')
                                        else:
                                            duel_message = duel_message.replace('%','rpg duel')
                                        cooldowns.append(['duel',duel,duel_message,])
                                if arena_enabled == 1:
                                    if bot_message.find('rena`** (**') > -1:
                                        arena_start = bot_message.find('rena`** (**') + 11
                                        arena_end = bot_message.find('s**', arena_start) + 1
                                        arena = bot_message[arena_start:arena_end]
                                        arena = arena.lower()
                                        if arena_message == None:
                                            arena_message = default_message.replace('%','rpg arena')
                                        else:
                                            arena_message = arena_message.replace('%','rpg arena')
                                        cooldowns.append(['arena',arena,arena_message,])
                                if dungmb_enabled == 1:
                                    if bot_message.find('boss`** (**') > -1:
                                        dungmb_start = bot_message.find('boss`** (**') + 11
                                        dungmb_end = bot_message.find('s**', dungmb_start) + 1
                                        dungmb = bot_message[dungmb_start:dungmb_end]
                                        dungmb = dungmb.lower()
                                        if dungmb_message == None:
                                            dungmb_message = default_message.replace('%','rpg dungeon / miniboss')
                                        else:
                                            dungmb_message = dungmb_message.replace('%','rpg dungeon / miniboss')
                                        cooldowns.append(['dungmb',dungmb,dungmb_message,])
                                if horse_enabled == 1:
                                    if bot_message.find('race`** (**') > -1:
                                        horse_start = bot_message.find('race`** (**') + 11
                                        horse_end = bot_message.find('s**', horse_start) + 1
                                        horse = bot_message[horse_start:horse_end]
                                        horse = horse.lower()
                                        if horse_message == None:
                                            horse_message = default_message.replace('%','rpg horse breed / race')
                                        else:
                                            horse_message = horse_message.replace('%','rpg horse bred / race')
                                        cooldowns.append(['horse',horse,horse_message,])
                                if vote_enabled == 1:
                                    if bot_message.find('Vote`** (**') > -1:
                                        vote_start = bot_message.find('Vote`** (**') + 11
                                        vote_end = bot_message.find('s**', vote_start) + 1
                                        vote = bot_message[vote_start:vote_end]
                                        vote = vote.lower()
                                        if vote_message == None:
                                            vote_message = default_message.replace('%','rpg vote')
                                        else:
                                            vote_message = vote_message.replace('%','rpg vote')
                                        cooldowns.append(['vote',vote,vote_message,])
                                if farm_enabled == 1:
                                    if bot_message.find('Farm`** (**') > -1:
                                        farm_start = bot_message.find('Farm`** (**') + 11
                                        farm_end = bot_message.find('s**', farm_start) + 1
                                        farm = bot_message[farm_start:farm_end]
                                        farm = farm.lower()
                                        if farm_message == None:
                                            farm_message = default_message.replace('%','rpg farm')
                                        else:
                                            farm_message = farm_message.replace('%','rpg farm')
                                        cooldowns.append(['farm',farm,farm_message,])

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
                                    if time_left > 1:
                                        write_status = await global_functions.write_reminder(self.bot, ctx, activity, time_left, message, True)
                                        if write_status in ('inserted','scheduled','updated','do-nothing'):
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
                await ctx.send('Cooldowns detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Cooldowns detection error: {e}')
                return

# Initialization
def setup(bot):
    bot.add_cog(cooldownsCog(bot))