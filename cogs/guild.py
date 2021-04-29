# guild.py
# Contains settings AND detection commands

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

# guild commands (cog)
class guildCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.reset_guild.start(self.bot)
    
    
    # --- Tasks ---
    # Task to reset guild
    @tasks.loop(minutes=1.0)
    async def reset_guild(self, bot):
        
        reset_weekday = global_data.guild_reset[0]
        reset_hour = global_data.guild_reset[1]
        reset_minute = global_data.guild_reset[2]
        
        today = datetime.today().weekday()
        
        if datetime.today().weekday() == reset_weekday:
            now = datetime.utcnow()
            if now.hour == reset_hour and now.minute == reset_minute:
                guilds = await database.reset_guilds(bot)
                for guild in guilds:
                    guild_name = guild[0]
                    guild_channel_id = guild[1]
                    guild_message = guild[2]
                    guild_message = guild_message.replace('%','rpg guild upgrade')
                    task_name = f'{guild_name}-guild'
                    await bot.wait_until_ready()
                    channel = bot.get_channel(guild_channel_id)
                    if task_name in global_data.running_tasks:
                        global_data.running_tasks[task_name].cancel()    
                    
                    bot.loop.create_task(global_functions.background_task(bot, guild_name, channel, guild_message, 60, task_name, True))
        
    # Guild detection
    async def get_guild_message(self, ctx):
        
        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_guild_non_async(m)
                
                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Guild detection: {message}')
                
                if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1) or (message.find('Guild successfully upgraded!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('end your previous command') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('your guild has already 100') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            
            return m.author.id == global_data.epic_rpg_id and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
        bot_message = await global_functions.encode_message_guild(bot_answer)
            
        return (bot_answer, bot_message,)
            
    
    
    # --- Commands ---
    # Guild
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def guild(self, ctx, *args):
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
    
        prefix = ctx.prefix
        if not prefix.lower() == 'rpg ':
            
            error_not_leader = (
                f'**{ctx.author.name}**, you are not registered as a guild leader. Only guild leaders can do this.\n'
                f'If you are a guild leader, run `rpg guild list` first to add or update your guild in my database.'
            )
            
            if args:
                guild_data = await database.get_guild(ctx, 'leader')
                if not guild_data == None:
                    guild_name = guild_data[0]
                    guild_stealth = guild_data[2]
                    guild_channel = guild_data[4]
                
                arg1 = args[0]
                arg1 = arg1.lower()
                if arg1 == 'channel':
                    if guild_data == None:
                        await ctx.reply(error_not_leader,mention_author=False)
                        return
                    if len(args) == 2:
                        arg2 = args[1] 
                        if arg2 == 'set':             
                            await ctx.reply(f'**{ctx.author.name}**, set `{ctx.channel.name}` as the alert channel for the guild **{guild_name}**? `[yes/no]`', mention_author=False)
                            answer = await self.bot.wait_for('message', check=check, timeout=30)
                            if answer.content.lower() in ['yes','y']:
                                status = await database.set_guild_channel(ctx, ctx.channel.id)
                                if status == 'updated':
                                    await ctx.send(f'**{ctx.author.name}**, `{ctx.channel.name}` is now set as the alert channel for the guild **{guild_name}**.')
                                    return
                                elif status == 'unchanged':
                                    await ctx.send(f'**{ctx.author.name}**, `{ctx.channel.name}` is already set as the alert channel for the guild **{guild_name}**.')
                                    return
                                else:
                                    await ctx.send(status)
                                    return
                            else:
                                await ctx.send('Aborted.')
                                return
                        elif arg2 == 'reset':        
                            if guild_channel == None:
                                await ctx.reply(f'The guild **{guild_name}** doesn\'t have an alert channel set, there is no need to reset it.', mention_author=False)
                                return
                        
                            await self.bot.wait_until_ready()
                            channel = self.bot.get_channel(guild_channel)
                            if channel == None:
                                channel_name = 'Invalid channel'
                            else:
                                channel_name = channel.name
                                
                            await ctx.reply(f'**{ctx.author.name}**, do you want to remove `{channel_name}` as the alert channel for the guild **{guild_name}**? `[yes/no]`', mention_author=False)
                            answer = await self.bot.wait_for('message', check=check, timeout=30)
                            if answer.content.lower() in ['yes','y']:
                                status = await database.set_guild_channel(ctx, None)
                                if status == 'updated':
                                    await ctx.send(f'**{ctx.author.name}**, the guild **{guild_name}** doesn\'t have an alert channel set anymore.')
                                    return
                                else:
                                    await ctx.send(status)
                                    return
                            else:
                                await ctx.send('Aborted.')
                                return
                    else:
                        await self.bot.wait_until_ready()
                        channel = self.bot.get_channel(guild_channel)
                        if not channel == None:
                            await ctx.reply(
                                f'The current alert channel for the guild **{guild_name}** is `{channel.name}` (ID `{channel.id}`).\n'
                                f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} channel set` within your new alert channel.\n'
                                f'To remove the alert channel entirely, use `{ctx.prefix}{ctx.invoked_with} channel reset`',
                                mention_author=False
                            )
                            return
                        else:
                            await ctx.reply(
                                f'The guild **{guild_name}** doesn\'t have an alert channel set.\n'
                                f'If you want to set one, use `{ctx.prefix}{ctx.invoked_with} channel set`',
                                mention_author=False
                            )
                            return
                elif arg1 == 'stealth':
                    if guild_data == None:
                            await ctx.reply(error_not_leader,mention_author=False)
                            return
                    if len(args) == 2:
                        arg2 = args[1] 
                        if arg2.isnumeric():
                            new_stealth = int(arg2)
                            if 1 <= new_stealth <= 100:
                                status = await database.set_guild_stealth_threshold(ctx, new_stealth)
                                if status == 'updated':
                                    await ctx.reply(f'**{ctx.author.name}**, stealth threshold for the guild **{guild_name}** is now **{new_stealth}**.', mention_author=False)
                                    return
                                else:
                                    await ctx.reply(status, mention_author=False)
                                    return
                            else:
                                await ctx.reply(f'**{ctx.author.name}**, the stealth threshold needs to be between 1 and 100.', mention_author=False)
                                return
                        else:
                            await ctx.reply(f'**{ctx.author.name}**, the stealth threshold needs to be a number between 1 and 100.', mention_author=False)
                            return
                    else:
                        await ctx.reply(
                            f'The current stealth threshold for the guild **{guild_name}** is **{guild_stealth}**.\n'
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} stealth [1-100]`.',
                            mention_author=False
                        )
                elif arg1 in ('on','off'):
                    if guild_data == None:
                        await ctx.reply(error_not_leader,mention_author=False)
                        return
                    status = await database.set_guild_reminders(ctx, guild_name, arg1)
                    await ctx.reply(status, mention_author=False)
                elif arg1 in ('leaderboard','lb'):
                    leaderboard_data = await database.get_guild_leaderboard(ctx)
                    guild_name = leaderboard_data[0]
                    best_raids = leaderboard_data[1]
                    worst_raids = leaderboard_data[2]
                    
                    if guild_name == None:
                        await ctx.reply(
                            f'**{ctx.author.name}**, you are not registered as a member of a guild.\n'
                            f'If you are in a guild, run `rpg guild list` first to add or update your guild in my database.',
                            mention_author=False
                        )
                        return
                    
                    leaderboard_best = ''
                    leaderboard_worst = ''
                    
                    if not best_raids == None:
                        counter = 0
                        for best_raid in best_raids:
                            counter = counter + 1
                            if counter == 1:
                                emoji = emojis.one
                            elif counter == 2:
                                emoji = emojis.two
                            elif counter == 3:
                                emoji = emojis.three
                            elif counter == 4:
                                emoji = emojis.four
                            elif counter == 5:
                                emoji = emojis.five
                            else:
                                emoji = emojis.bp
                            user_id = best_raid[0]
                            energy = best_raid[1]
                            await self.bot.wait_until_ready()
                            best_user = self.bot.get_user(user_id)
                            leaderboard_best = (
                                f'{leaderboard_best}\n'
                                f'{emoji} **{energy:,}** {emojis.energy} by {best_user.mention}'
                            )
                    else:
                        leaderboard_best = f'{emojis.bp} _No cool raids yet._'
                    
                    if not worst_raids == None:
                        counter = 0
                        for worst_raid in worst_raids:
                            counter = counter + 1
                            if counter == 1:
                                emoji = emojis.one
                            elif counter == 2:
                                emoji = emojis.two
                            elif counter == 3:
                                emoji = emojis.three
                            elif counter == 4:
                                emoji = emojis.four
                            elif counter == 5:
                                emoji = emojis.five
                            else:
                                emoji = emojis.bp
                            user_id = worst_raid[0]
                            energy = worst_raid[1]
                            await self.bot.wait_until_ready()
                            worst_user = self.bot.get_user(user_id)
                            leaderboard_worst = (
                                f'{leaderboard_worst}\n'
                                f'{emoji} **{energy:,}** {emojis.energy} by {worst_user.mention}'
                            )
                    else:
                        leaderboard_worst = f'{emojis.bp} _No lame raids yet._'
                    
                    embed = discord.Embed(
                        color = global_data.color,
                        title = f'{guild_name} WEEKLY LEADERBOARD',
                    )    
                    embed.set_footer(text='Imagine being on the lower list.')
                    embed.add_field(name=f'COOL RAIDS {emojis.best_raids}', value=leaderboard_best, inline=False)
                    embed.add_field(name=f'WHAT THE HELL IS THIS {emojis.worst_raids}', value=leaderboard_worst, inline=False)
            
                    await ctx.reply(embed=embed, mention_author=False)
                    
        # Guild command detection
        else:
            prefix = ctx.prefix
            
            if args:
                arg = args[0]
                if arg in ('raid', 'upgrade'):
                    try:
                        guild_data = await database.get_guild(ctx, 'member')
                        
                        if not guild_data == None:
                            guild_name = guild_data[0]
                            guild_reminders_on = guild_data[1]
                            guild_stealth_threshold = guild_data[2]
                            guild_stealth_current = guild_data[3]
                            guild_channel_id = guild_data[4]
                            guild_message = guild_data[5]
                            
                            command = f'rpg guild {arg}'

                            if not guild_reminders_on == 0:
                                task_status = self.bot.loop.create_task(self.get_guild_message(ctx))
                                bot_message = None
                                message_history = await ctx.channel.history(limit=50).flatten()
                                for msg in message_history:
                                    if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                        try:
                                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                            message = await global_functions.encode_message_guild(msg)
                                            
                                            if global_data.DEBUG_MODE == 'ON':
                                                global_data.logger.debug(f'Guild detection: {message}')
                                            
                                            if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1)\
                                            or (message.find('Guild successfully upgraded!') > -1) or (message.find('Guild upgrade failed!') > -1)\
                                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('end your previous command') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('your guild has already 100') > -1))\
                                            or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
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
                                        await ctx.send('Guild detection timeout.')
                                        return

                                guild_upgraded = False
                                
                                # Check if stealth was upgraded
                                if (bot_message.find('Guild successfully upgraded!') > -1) or (bot_message.find('Guild upgrade failed!') > -1):
                                    stealth_start = bot_message.find('--> **') + 6
                                    stealth_end = bot_message.find('**', stealth_start)
                                    stealth = bot_message[stealth_start:stealth_end]
                                    guild_stealth_before = guild_stealth_current
                                    guild_stealth_current = int(stealth)
                                    guild_upgraded = True
                                    status = await database.set_guild_stealth_current(ctx, guild_name, guild_stealth_current)
                                    
                                # Add raid to the leaderboard if there was a raid
                                if bot_message.find(' RAIDED ') > 1:
                                    energy_start = bot_message.find('earned **') + 9
                                    energy_end = bot_message.find(':low_brightness:', energy_start) - 3
                                    energy = bot_message[energy_start:energy_end]
                                    energy = int(energy)
                                    status = await database.write_raid_energy(ctx, guild_name, energy)
                                
                                # Set message to send
                                if guild_stealth_current >= guild_stealth_threshold:
                                    if guild_message == None:
                                        guild_message = global_data.default_message.replace('%','rpg guild raid')
                                    else:
                                        guild_message = guild_message.replace('%','rpg guild raid')
                                else:
                                    if guild_message == None:
                                        guild_message = global_data.default_message.replace('%','rpg guild upgrade')
                                    else:
                                        guild_message = guild_message.replace('%','rpg guild upgrade')

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
                                    write_status = await global_functions.write_guild_reminder(self.bot, ctx, guild_name, guild_channel_id, time_left, guild_message, True)
                                    if write_status in ('inserted','scheduled','updated'):
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
                                        if global_data.DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore message that guild is fully upgraded
                                elif bot_message.find('your guild has already 100') > 1:
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
                    
                        # Calculate cooldown
                        cooldown_data = await database.get_cooldown(ctx, 'guild')
                        cooldown = int(cooldown_data[0])
                        bot_answer_time = bot_answer.created_at.replace(microsecond=0)                
                        current_time = datetime.utcnow().replace(microsecond=0)
                        time_elapsed = current_time - bot_answer_time
                        time_elapsed_seconds = time_elapsed.total_seconds()
                        cooldown = cooldown - time_elapsed.total_seconds()
                        write_status = await global_functions.write_guild_reminder(self.bot, ctx, guild_name, guild_channel_id, cooldown, guild_message)
                        
                        # Add reaction
                        if not write_status == 'aborted':
                            await bot_answer.add_reaction(emojis.navi)
                            if guild_upgraded == True and guild_stealth_current >= guild_stealth_threshold:
                                await bot_answer.add_reaction(emojis.yay)
                            
                            if guild_upgraded == True and guild_stealth_current == guild_stealth_before:
                                await bot_answer.add_reaction(emojis.angry)
                        else:
                            if global_data.DEBUG_MODE == 'ON':
                                await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                    except asyncio.TimeoutError as error:
                        await ctx.send('Guild detection timeout.')
                        return 
                    except Exception as e:
                        global_data.logger.error(f'Guild detection error: {e}')
                        return
            else:
                try:
                    guild_data = await database.get_guild(ctx, 'member')
                    
                    if not guild_data == None:
                        guild_name = guild_data[0]
                        guild_reminders_on = guild_data[1]
                        guild_stealth_threshold = guild_data[2]
                        guild_stealth_current = guild_data[3]
                        guild_channel_id = guild_data[4]
                        guild_message = guild_data[5]
                        
                        task_status = self.bot.loop.create_task(self.get_guild_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await global_functions.encode_message_guild(msg)
                                    
                                    if global_data.DEBUG_MODE == 'ON':
                                        global_data.logger.debug(f'Guild detection: {message}')
                                    
                                    if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1)\
                                    or (message.find('Guild successfully upgraded!') > -1) or (message.find('Guild upgrade failed!') > -1)\
                                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('end your previous command') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('your guild has already 100') > -1))\
                                    or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
                                        
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
                                await ctx.send('Guild detection timeout.')
                                return

                        # Check if correct embed
                        if bot_message.find('Your guild was raided') > -1:
                            if not guild_reminders_on == 0:
                                # Upgrade stealth (no point in upgrading that without active reminders)
                                stealth_start = bot_message.find('**STEALTH**: ') + 13
                                stealth_end = bot_message.find('\\n', stealth_start)
                                stealth = bot_message[stealth_start:stealth_end]
                                guild_stealth_current = int(stealth)
                                status = await database.set_guild_stealth_current(ctx, guild_name, guild_stealth_current)

                                # Set message to send
                                if guild_stealth_current >= guild_stealth_threshold:
                                    if guild_message == None:
                                        guild_message = global_data.default_message.replace('%','rpg guild raid')
                                    else:
                                        guild_message = guild_message.replace('%','rpg guild raid')
                                else:
                                    if guild_message == None:
                                        guild_message = global_data.default_message.replace('%','rpg guild upgrade')
                                    else:
                                        guild_message = guild_message.replace('%','rpg guild upgrade')
                                
                                # Update reminder
                                timestring_start = bot_message.find(':clock4: ') + 9
                                timestring_end = bot_message.find('**', timestring_start)
                                timestring = bot_message[timestring_start:timestring_end]
                                timestring = timestring.lower()
                                time_left = await global_functions.parse_timestring(ctx, timestring)
                                write_status = await global_functions.write_guild_reminder(self.bot, ctx, guild_name, guild_channel_id, time_left, guild_message, True)
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if global_data.DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        else:
                            return
                    else:
                        global_data.logger.error(f'Guild detection error: Couldn\'t find guild data for user {ctx.author.id} ({ctx.author.name})')
                        return   
                except asyncio.TimeoutError as error:
                    await ctx.send('Guild detection timeout.')
                    return
                except Exception as e:
                    global_data.logger.error(f'Guild detection error: {e}')
                    return   
        
# Initialization
def setup(bot):
    bot.add_cog(guildCog(bot))