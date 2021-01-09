# bot.py
import os
import discord
import sqlite3
import shutil
import asyncio
import global_data
import emojis
import logging
import logging.handlers
from emoji import demojize
from emoji import emojize

from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from math import ceil

# Check if log file exists, if not, create empty one
logfile = global_data.logfile
if not os.path.isfile(logfile):
    open(logfile, 'a').close()

# Initialize logger
logger = logging.getLogger('discord')
if global_data.debug_mode == True:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(filename=logfile,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Read the bot token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set name of database files
dbfile = global_data.dbfile

# Open connection to the local database    
erg_db = sqlite3.connect(dbfile, isolation_level=None)

# Create task dictionary
running_tasks = {}
         
# --- Database: Get Data ---

# Check database for stored prefix, if none is found, a record is inserted and the default prefix - is used, return all bot prefixes
async def get_prefix_all(bot, ctx):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (ctx.guild.id,))
        record = cur.fetchone()
        
        if record:
            prefixes = (record[1],'rpg ',)
        else:
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, global_data.default_prefix,))
            prefixes = (global_data.default_prefix,'rpg ')
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return commands.when_mentioned_or(*prefixes)(bot, ctx)

# Check database for stored prefix, if none is found, the default prefix - is used, return only the prefix (returning the default prefix this is pretty pointless as the first command invoke already inserts the record)
async def get_prefix(ctx, guild_join=False):
    
    if guild_join == False:
        guild = ctx.guild
    else:
        guild = ctx
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (guild.id,))
        record = cur.fetchone()
        
        if record:
            prefix = record[1]
        else:
            prefix = global_data.default_prefix
    except sqlite3.Error as error:
        if guild_join == False:
            await log_error(ctx, error)
        else:
            await log_error(ctx, error, True)
        
    return prefix

# Get user count
async def get_user_number(ctx):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT COUNT(*) FROM settings_user')
        record = cur.fetchone()
        
        if record:
            user_number = record
        else:
            await log_error(ctx, 'No user data found in database.')
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return user_number
   
# Get settings
async def get_settings(ctx, setting='all'):
    
    current_settings = None
    
    if setting == 'all':
        sql = 'SELECT * FROM settings_user where user_id=?'
    elif setting == 'hunt':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, partner_name, partner_donor_tier, hunt_enabled, hunt_message FROM settings_user where user_id=?'
    elif setting == 'work':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, work_enabled, work_message FROM settings_user where user_id=?'
    elif setting == 'training':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, tr_enabled, tr_message FROM settings_user where user_id=?'
    elif setting == 'adventure':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, adv_enabled, adv_message FROM settings_user where user_id=?'
    elif setting == 'lootbox':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, lb_enabled, lb_message FROM settings_user where user_id=?'
    elif setting == 'quest':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, quest_enabled, quest_message FROM settings_user where user_id=?'
    elif setting == 'daily':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, daily_enabled, daily_message FROM settings_user where user_id=?'
    
    try:
        cur=erg_db.cursor()
        cur.execute(sql, (ctx.author.id,))
        record = cur.fetchone()
    
        if record:
            current_settings = record
    
    except sqlite3.Error as error:
        await log_error(ctx, error)    
  
    return current_settings

# Get cooldown
async def get_cooldown(ctx, activity):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT cooldown, donor_affected FROM cooldowns where activity=?', (activity,))
        record = cur.fetchone()
    
        if record:
            cooldown_data = record
        else:
            await log_error(ctx, f'No cooldown data found for activity \'{activity}\'.')
    
    except sqlite3.Error as error:
        await log_error(ctx, error)    
  
    return cooldown_data

# Get due reminders
async def get_due_reminders():
    
    current_time = datetime.utcnow().replace(microsecond=0)
    end_time = current_time + timedelta(seconds=15)
    end_time = end_time.timestamp()
    current_time = current_time.timestamp()
    triggered = 0
    
    due_reminders = 'None'
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT user_id, activity, end_time, channel_id, message, triggered FROM reminders WHERE triggered = ? AND end_time BETWEEN ? AND ?', (triggered, current_time, end_time,))
        record = cur.fetchall()
        
        if record:
            due_reminders = record
        else:
            due_reminders = 'None'
    except sqlite3.Error as error:
        logger.error(f'Routine \'get_due_reminders\' had the following error: {error}')
    
    return due_reminders

# Get old reminders
async def get_old_reminders():
    
    current_time = datetime.utcnow().replace(microsecond=0)
    delete_time = current_time - timedelta(seconds=20) # This ensures that no reminders get deleted that are triggered but not yet fired.
    delete_time = delete_time.timestamp()
    
    due_reminders = 'None'
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT user_id, activity, triggered FROM reminders WHERE end_time < ?', (delete_time,))
        record = cur.fetchall()
        
        if record:
            old_reminders = record
        else:
            old_reminders = 'None'
    except sqlite3.Error as error:
        logger.error(f'Routine \'get_old_reminders\' had the following error: {error}')
    
    return old_reminders


# --- Database: Write Data ---

# Set new prefix
async def set_prefix(bot, ctx, new_prefix):

    try:
        cur=erg_db.cursor()
        cur.execute('SELECT * FROM settings_guild where guild_id=?', (ctx.guild.id,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE settings_guild SET prefix = ? where guild_id = ?', (new_prefix, ctx.guild.id,))           
        else:
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, new_prefix,))
    except sqlite3.Error as error:
        await log_error(ctx, error)

# Toggle reminders on or off
async def set_reminders(ctx, action):
    
    status = 'Whoops, something went wrong here.'
    
    if action == 'on':
        reminders_on = 1
    elif action == 'off':
        reminders_on = 0
    else:
        await log_error(ctx, f'Unknown action in routine toggle_reminders.')
        return
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT reminders_on FROM settings_user where user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            reminders_status = int(record[0])
            if reminders_status == 1 and reminders_on == 1:
                status = f'**{ctx.author.name}**, your reminders are already turned on.'
            elif reminders_status == 0 and reminders_on == 0:
                status = f'**{ctx.author.name}**, your reminders are already turned off.'
            else:
                if reminders_on == 1:
                    cur.execute('UPDATE settings_user SET reminders_on = ? where user_id = ?', (reminders_on, ctx.author.id,))
                    status = f'**{ctx.author.name}**, your reminders are now turned **on**.'
                else:
                    cur.execute('UPDATE settings_user SET reminders_on = ? where user_id = ?', (reminders_on, ctx.author.id,))
                    status = f'**{ctx.author.name}**, your reminders are now turned **off**.\nPlease note that active reminders that will end within the next ~15 seconds may still ping you.'
        else:
            if reminders_on == 0:
                status = f'**{ctx.author.name}**, your reminders are already turned off.'
            else:
                cur.execute('INSERT INTO settings_user (user_id, reminders_on, default_message) VALUES (?, ?, ?)', (ctx.author.id, reminders_on, global_data.default_message,))
                status = f'Hey! **{ctx.author.name}**! Wecome! Your reminders are now turned **on**.\nDon\'t forget to set your donor tier with `{ctx.prefix}tbd`.\nYou can check all of your settings with `{ctx.prefix}settings` or `{ctx.prefix}me`.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set partner
async def set_partner(ctx, partner_name):
    
    if partner_name == None:
        await log_error(ctx, f'Can not write an empty partner name.')
        return
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT partner_name FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            partner_db = record[0]
            if partner_db == None or (partner_db != partner_name):
                cur.execute('UPDATE settings_user SET partner_name = ? WHERE user_id = ?', (partner_name, ctx.author.id,))
            else:
                return
        else:
            return
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
# Write reminder
async def write_reminder(ctx, activity, time_left, message, cooldown_update=False):
    
    current_time = datetime.utcnow().replace(microsecond=0)
    status = 'aborted'
    
    if not time_left == 0:
        end_time = current_time + timedelta(seconds=time_left)
        end_time = end_time.timestamp()
        triggered = 0
    else:
        return
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (ctx.author.id, activity,))
        record = cur.fetchone()
        
        if record:
            db_time = float(record[0])
            db_time_datetime = datetime.fromtimestamp(db_time)
            db_triggered = int(record[1])
            time_difference = db_time_datetime - current_time
            if 0 <= time_difference.total_seconds() <= 15 and db_triggered == 1 and cooldown_update == True:
                task_name = f'{ctx.author.id}-{activity}'
                if task_name in running_tasks:
                    running_tasks[task_name].cancel()    
                bot.loop.create_task(background_task(ctx.author, ctx.channel, message, time_left, task_name))
                status = 'scheduled'
            else:
                cur.execute('UPDATE reminders SET end_time = ?, channel_id = ?, message = ?, triggered = ? WHERE user_id = ? AND activity = ?', (end_time, ctx.channel.id, message, triggered, ctx.author.id, activity,))
                status = 'updated'
        else:
            if time_left > 15:
                cur.execute('INSERT INTO reminders (user_id, activity, end_time, channel_id, message) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, activity, end_time, ctx.channel.id, message,))
                status = 'inserted'
            else:
                task_name = f'{ctx.author.id}-{activity}'
                bot.loop.create_task(background_task(ctx.author, ctx.channel, message, time_left, task_name))
                status = 'scheduled'
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return status

# Set reminder triggered state
async def set_reminder_triggered(ctx, user_id, activity, triggered=1):
    
    try:
        cur=erg_db.cursor()
        if activity == 'all':
            cur.execute('SELECT triggered FROM reminders WHERE user_id=?', (user_id,))
            record = cur.fetchall()
        else:
            cur.execute('SELECT triggered FROM reminders WHERE user_id=? AND activity=?', (user_id, activity,))
            record = cur.fetchone() 
        
        if record:
            if activity == 'all':
                cur.execute('UPDATE reminders SET triggered = ? WHERE user_id = ?', (triggered, user_id,))
            else:
                if int(record[0]) != triggered:
                    cur.execute('UPDATE reminders SET triggered = ? WHERE user_id = ? AND activity = ?', (triggered, user_id, activity,))
                
    except sqlite3.Error as error:
            if ctx == None:
                logger.error(f'Routine \'set_reminder_triggered\' had the following error: {error}')
            else:
                await log_error(ctx, error)

# Delete reminder
async def delete_reminder(ctx, user_id, activity):
    
    try:
        cur=erg_db.cursor()
        cur.execute('DELETE FROM reminders WHERE user_id = ? AND activity = ?', (user_id, activity,))
    except sqlite3.Error as error:
        if ctx == None:
            logger.error(f'Routine \'delete_reminder\' had the following error: {error}')
        else:
            await log_error(ctx, error)


# --- Error Logging ---

# Error logging
async def log_error(ctx, error, guild_join=False):
    
    if guild_join == False:
        try:
            settings = ''
            try:
                user_settings = await get_settings(ctx)
                settings = f'Enchant {user_settings[0]}'
            except:
                settings = 'N/A'
            cur=erg_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (ctx.message.created_at, ctx.message.content, str(error), settings))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))
    else:
        try:
            cur=erg_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (datetime.now(), 'Error when joining a new guild', str(error), 'N/A'))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))


# --- Parsing ---
async def parse_timestring(ctx, timestring):
    
    time_left = 0
    
    if timestring.find('d') > -1:
        days_start = 0
        days_end = timestring.find('d')
        days = timestring[days_start:days_end]
        timestring = timestring[days_end+1:].strip()
        try:
            time_left = time_left + (int(days) * 86400)
        except:
            await log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{days}\' to an integer')
        
    if timestring.find('h') > -1:
        hours_start = 0
        hours_end = timestring.find('h')
        hours = timestring[hours_start:hours_end]
        timestring = timestring[hours_end+1:].strip()
        try:
            time_left = time_left + (int(hours) * 3600)
        except:
            await log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{hours}\' to an integer')
        
    if timestring.find('m') > -1:
        minutes_start = 0
        minutes_end = timestring.find('m')
        minutes = timestring[minutes_start:minutes_end]
        timestring = timestring[minutes_end+1:].strip()
        try:
            time_left = time_left + (int(minutes) * 60)
        except:
            await log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{minutes}\' to an integer')
        
    if timestring.find('s') > -1:
        seconds_start = 0
        seconds_end = timestring.find('s')
        seconds = timestring[seconds_start:seconds_end]
        timestring = timestring[seconds_end+1:].strip()
        try:
            time_left = time_left + int(seconds)
        except:
            await log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{seconds}\' to an integer')
    
    return time_left


# --- Command Initialization ---

bot = commands.Bot(command_prefix=get_prefix_all, help_command=None, case_insensitive=True)


# --- Ready & Join Events ---

# Set bot status when ready
@bot.event
async def on_ready():
    
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Epic RPG'))
    schedule_reminders.start(bot)
    delete_old_reminders.start(bot)
    
# Send message to system channel when joining a server
@bot.event
async def on_guild_join(guild):
    
    try:
        prefix = await get_prefix(guild, True)
        
        welcome_message =   f'Hey! **{guild.name}**! I\'m here to remind you to do your Epic RPG commands!\n\n'\
                            f'Note that reminders are off by default. If you want to get reminded, please use `{prefix}on` to activate me.\n'\
                            f'If you don\'t like this prefix, use `{prefix}setprefix` to change it.\n\n'\
                            f'Tip: If you ever forget the prefix, simply ping me with a command.\n\n'\
        
        await guild.system_channel.send(welcome_message)
    except:
        return



# --- Error Handling ---

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    elif isinstance(error, (commands.MissingPermissions)):
        missing_perms = ''
        for missing_perm in error.missing_perms:
            missing_perm = missing_perm.replace('_',' ').title()
            if not missing_perms == '':
                missing_perms = f'{missing_perms}, `{missing_perm}`'
            else:
                missing_perms = f'`{missing_perm}`'
        await ctx.send(f'Sorry **{ctx.author.name}**, you need the permission(s) {missing_perms} to use this command.')
    elif isinstance(error, (commands.BotMissingPermissions)):
        missing_perms = ''
        for missing_perm in error.missing_perms:
            missing_perm = missing_perm.replace('_',' ').title()
            if not missing_perms == '':
                missing_perms = f'{missing_perms}, `{missing_perm}`'
            else:
                missing_perms = f'`{missing_perm}`'
        await ctx.send(f'Sorry **{ctx.author.name}**, I\'m missing the permission(s) {missing_perms} to work properly.')
    elif isinstance(error, (commands.NotOwner)):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'You\'re missing some arguments.')
    else:
        await log_error(ctx, error) # To the database you go


# --- Server Settings ---
   
# Command "setprefix" - Sets new prefix (if user has "manage server" permission)
@bot.command()
@commands.has_permissions(manage_guild=True)
@commands.bot_has_permissions(send_messages=True)
async def setprefix(ctx, *new_prefix):
    
    if not ctx.prefix == 'rpg ':
        if new_prefix:
            if len(new_prefix)>1:
                await ctx.send(f'The command syntax is `{ctx.prefix}setprefix [prefix]`.')
            else:
                await set_prefix(bot, ctx, new_prefix[0])
                await ctx.send(f'Prefix changed to `{await get_prefix(ctx)}`.')
        else:
            await ctx.send(f'The command syntax is `{ctx.prefix}setprefix [prefix]`.')

# Command "prefix" - Returns current prefix
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def prefix(ctx):
    
    if not ctx.prefix == 'rpg ':
        current_prefix = await get_prefix(ctx)
        await ctx.send(f'The prefix for this server is `{current_prefix}`\nTo change the prefix use `{current_prefix}setprefix [prefix]`.')


# --- User Settings ---

# Command "settings" - Returns current user progress settings
@bot.command(aliases=('me',))
@commands.bot_has_permissions(send_messages=True)
async def settings(ctx):
    
    if not ctx.prefix == 'rpg ':
        current_settings = await get_settings(ctx)
        
        if current_settings:
            enchants = global_data.enchants_list
            enchant_setting = current_settings[0]
            enchant_setting = int(enchant_setting)
            enchant_name = enchants[enchant_setting]
            if enchant_setting > 7:
                enchant_name = enchant_name.upper()
            else:
                enchant_name = enchant_name.title()
            
            await ctx.send(
                f'**{ctx.author.name}**, your target enchant is set to **{enchant_name}**.\n'
                f'Use `{ctx.prefix}set [enchant]` to change it.'
            )
    
# Command "on" - Activates reminders
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def on(ctx, *args):
    
    if not ctx.prefix == 'rpg ':
        status = await set_reminders(ctx, 'on')
        await ctx.send(status)
        
# Command "off" - Deactivates reminders
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def off(ctx, *args):
    
    if not ctx.prefix == 'rpg ':
        status = await set_reminders(ctx, 'off')
        await set_reminder_triggered(ctx, ctx.author.id, 'all')
        await ctx.send(status)
        

# --- Tasks ---

# Background task for scheduling reminders
async def background_task(user, channel, message, time_left, task_name):
        
    await asyncio.sleep(time_left)
    try:
        await bot.wait_until_ready()
        await bot.get_channel(channel.id).send(f'{user.mention} {message}')
        delete_task = running_tasks.pop(task_name, None)
        
    except Exception as e:
        logger.error(f'Error sending reminder: {e}')

# Task to read all due reminders from the database and schedule them
@tasks.loop(seconds=10.0)
async def schedule_reminders(bot):
    
    due_reminders = await get_due_reminders()
    
    if due_reminders == 'None':
        return
    else:
        for reminder in due_reminders:    
            try:
                user_id = int(reminder[0])
                activity = reminder[1]
                end_time = float(reminder[2])
                channel_id = int(reminder[3])
                message = reminder[4]
                await bot.wait_until_ready()
                channel = bot.get_channel(channel_id)
                await bot.wait_until_ready()
                user = bot.get_user(user_id)
                
                current_time = datetime.utcnow().replace(microsecond=0)
                end_time_datetime = datetime.fromtimestamp(end_time)
                end_time_difference = end_time_datetime - current_time
                time_left = end_time_difference.total_seconds()
                
                task_name = f'{user_id}-{activity}'
                task = bot.loop.create_task(background_task(user, channel, message, time_left, task_name))
                running_tasks[task_name] = task
                
                await set_reminder_triggered(None, user_id, activity)
            except Exception as e:
                logger.error(f'{datetime.now()}: Error scheduling reminder {reminder}: {e}')

# Task to delete old reminders
@tasks.loop(minutes=2.0)
async def delete_old_reminders(bot):
    
    old_reminders = await get_old_reminders()
    
    if old_reminders == 'None':
        return
    else:
        for reminder in old_reminders:    
            try:
                user_id = int(reminder[0])
                activity = reminder[1]
                triggered = int(reminder[2])
                await delete_reminder(None, user_id, activity)
                if global_data.debug_mode == True:
                    if triggered == 1:
                        logger.info(f'{datetime.now()}: Deleted this old reminder {reminder}')
                    else:
                        logger.error(f'{datetime.now()}: Deleted this old reminder that was never triggered: {reminder}')
            except:
                logger.error(f'{datetime.now()}: Error deleting old reminder {reminder}')


# --- Command detection ---
# Hunt
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def hunt(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Hunt detection: {message}')
            
            if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1))) or ((message.find(f'\'s cooldown') > -1) and (message.find('You have already looked around') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('This command is unlocked in') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ' and len(args) in (0,1,2):
        # Determine if hardmode and/or together was used
        together = False
        command = 'rpg hunt'
        if len(args) > 0:
            arg1 = args[0]
            arg1 = arg1.lower()
            if arg1 in ('t', 'together'):
                together = True
                command = f'{command} together'
            elif arg1 in ('h', 'hardmode'):
                command = f'{command} hardmode'
                if len(args) > 1:
                    arg2 = args[1]
                    arg2 = arg2.lower()
                    if arg2 in ('t', 'together'):
                        together = True
                        command = f'{command} together'
        try:
            settings = await get_settings(ctx, 'hunt')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    partner_name = settings[3]
                    partner_donor_tier = int(settings[4])
                    hunt_enabled = int(settings[5])
                    hunt_message = settings[6]
                    
                    # Set message to send          
                    if hunt_message == None:
                        hunt_message = default_message.replace('%',f'`{command}`')
                    else:
                        hunt_message = hunt_message.replace('%',f'`{command}`')
                    
                    if not hunt_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if it found a cooldown embed, if yes if it is the correct one, if not, ignore it and try to wait for the bot message one more time
                        if bot_message.find(f'\'s cooldown') > 1:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if (bot_message.find(f'{ctx_author}\'s cooldown') > -1) or (bot_message.find(f'{partner_name}\'s cooldown') > -1):    
                                timestring_start = bot_message.find('wait at least **') + 16
                                timestring_end = bot_message.find('**...', timestring_start)
                                timestring = bot_message[timestring_start:timestring_end]
                                timestring = timestring.lower()
                                time_left = await parse_timestring(ctx, timestring)
                                write_status = await write_reminder(ctx, 'hunt', time_left, hunt_message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if global_data.debug_mode == True:
                                        await bot_answer.add_reaction(emojis.cross)
                                return
                            else:
                                bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = 3)
                                try:
                                    bot_message = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                except:
                                    bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        
                        # Read partner name from hunt together message and save it to database if necessary (to make the bot check safer)
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        if together == True:
                            partner_name_start = bot_message.find(f'{ctx_author} and ') + len(ctx_author) + 12
                            partner_name_end = bot_message.find('are hunting together!', partner_name_start) - 3
                            partner_name = str(bot_message[partner_name_start:partner_name_end]).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if not partner_name == '':
                                await set_partner(ctx, partner_name)
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'hunt')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if together == True and donor_affected == True:
                time_left = cooldown*global_data.donor_cooldowns[partner_donor_tier]
            elif together == False and donor_affected == True:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'hunt', time_left, hunt_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            # Add an F if the user died
            if (bot_message.find(f'{ctx_author} lost') > -1) or (bot_message.find('but lost fighting') > -1):
                await bot_answer.add_reaction(emojis.rip_reaction)
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Hunt detection timeout.')
            return

# Work
@bot.command(aliases=('axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor','greenhouse','mine','pickaxe','drill','dynamite',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def chop(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Work detection: {message}')
            
            if  ((message.find(f'**{ctx_author}** got ') > -1) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1) or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1) or (message.find('RUBY') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1)))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        command = f'rpg {ctx.invoked_with}'
        
        try:
            settings = await get_settings(ctx, 'work')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    work_enabled = int(settings[3])
                    work_message = settings[4]
                    
                    # Set message to send          
                    if work_message == None:
                        work_message = default_message.replace('%',f'`{command}`')
                    else:
                        work_message = work_message.replace('%',f'`{command}`')
                    
                    if not work_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'\'s cooldown') > 1:
                            timestring_start = bot_message.find('wait at least **') + 16
                            timestring_end = bot_message.find('**...', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'work', time_left, work_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'work')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'work', time_left, work_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
                if (bot_message.find(f'IS THIS A **DREAM**?????') > -1) or (bot_message.find(f'**HYPER** log') > -1):
                    await bot_answer.add_reaction(emojis.fire_reaction)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                return
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Work detection timeout.')
            return

# Training
@bot.command(aliases=('tr','ultraining','ultr',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def training(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Training detection: {message}')
            
            if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        if args:
            arg = args[0]
            if arg in ('p','progress',):
                return
        
        if ctx.invoked_with in ('tr', 'training',):
            command = f'rpg training'
        elif ctx.invoked_with in ('ultr', 'ultraining',):
            command = f'rpg ultraining'
        
        try:
            settings = await get_settings(ctx, 'training')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    tr_enabled = int(settings[3])
                    tr_message = settings[4]
                    
                    # Set message to send          
                    if tr_message == None:
                        tr_message = default_message.replace('%',f'`{command}`')
                    else:
                        tr_message = tr_message.replace('%',f'`{command}`')
                    
                    if not tr_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout_longer)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'\'s cooldown') > 1:
                            timestring_start = bot_message.find('wait at least **') + 16
                            timestring_end = bot_message.find('**...', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'training', time_left, tr_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'training')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'training', time_left, tr_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Training detection timeout.')
            return     

# Adventure
@bot.command(aliases=('adv',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def adventure(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Adventure detection: {message}')
            
            if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already been in an adventure') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        command = f'rpg adventure'
        
        if args:
            arg = args[0]
            if arg in ('h','hardmode',):
                command = f'{command} hardmode'
        
        try:
            settings = await get_settings(ctx, 'adventure')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    adv_enabled = int(settings[3])
                    adv_message = settings[4]
                    
                    # Set message to send          
                    if adv_message == None:
                        adv_message = default_message.replace('%',f'`{command}`')
                    else:
                        adv_message = adv_message.replace('%',f'`{command}`')
                    
                    if not adv_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'\'s cooldown') > 1:
                            timestring_start = bot_message.find('wait at least **') + 16
                            timestring_end = bot_message.find('**...', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'adventure', time_left, adv_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'adventure')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'adventure', time_left, adv_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Adventure detection timeout.')
            return   

# Lootbox
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def buy(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Lootbox detection: {message}')
            
            if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ' and args:     
        command = f'rpg buy lootbox'
        if len(args) == 2:
            arg2 = args[1]
            if arg2 in ('lb','lootbox',):
                try:
                    settings = await get_settings(ctx, 'lootbox')
                    if not settings == None:
                        reminders_on = settings[0]
                        if not reminders_on == 0:
                            user_donor_tier = int(settings[1])
                            default_message = settings[2]
                            lb_enabled = int(settings[3])
                            lb_message = settings[4]
                            
                            # Set message to send          
                            if lb_message == None:
                                lb_message = default_message.replace('%',f'`{command}`')
                            else:
                                lb_message = lb_message.replace('%',f'`{command}`')
                            
                            if not lb_enabled == 0:
                                bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                                try:
                                    message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message_description = str(bot_answer.embeds[0].description)
                                    try:
                                        message_fields = str(bot_answer.embeds[0].fields)
                                        message_title = str(bot_answer.embeds[0].title)
                                    except:
                                        message_fields = ''
                                    bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                                except:
                                    bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                                # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                                if bot_message.find(f'\'s cooldown') > 1:
                                    timestring_start = bot_message.find('wait at least **') + 16
                                    timestring_end = bot_message.find('**...', timestring_start)
                                    timestring = bot_message[timestring_start:timestring_end]
                                    timestring = timestring.lower()
                                    time_left = await parse_timestring(ctx, timestring)
                                    write_status = await write_reminder(ctx, 'lootbox', time_left, lb_message, True)
                                    if write_status in ('inserted','scheduled','updated'):
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore anti spam embed
                                elif bot_message.find('Huh please don\'t spam') > 1:
                                    if global_data.debug_mode == True:
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                # Ignore failed Epic Guard event
                                elif bot_message.find('is now in the jail!') > 1:
                                    if global_data.debug_mode == True:
                                        await bot_answer.add_reaction(emojis.cross)
                                    await bot_answer.add_reaction(emojis.rip_reaction)
                                    return
                            else:
                                return
                        else:
                            return
                    else:
                        return
                    
                    # Calculate cooldown
                    cooldown_data = await get_cooldown(ctx, 'lootbox')
                    cooldown = int(cooldown_data[0])
                    donor_affected = int(cooldown_data[1])
                    if donor_affected == 1:
                        time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
                    else:
                        time_left = cooldown
                    
                    # Save task to database
                    write_status = await write_reminder(ctx, 'lootbox', time_left, lb_message)
                    
                    # Add reaction
                    if not write_status == 'aborted':
                        await bot_answer.add_reaction(emojis.navi)
                    else:
                        if global_data.debug_mode == True:
                            await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                    
                except asyncio.TimeoutError as error:
                    if global_data.debug_mode == True:
                        await ctx.send('Lootbox detection timeout.')
                    return   
            else:
                return
        else:
            return
    else:
        return

# Quest
@bot.command(aliases = ('quest',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def epic(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                try:
                    message_title = str(m.embeds[0].title)
                except:
                    message_title = ''
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Quest detection: {message}')
            
            if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('FIRST WAVE') > -1)) or ((message.find(str(ctx.author.id)) > -1) and (message.find('epic quest cancelled') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(str(ctx.author.id)) > -1) and (message.find('you did not accept the quest') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('If you don\'t want this quest anymore') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':     
        command = f'rpg quest'
        if args:
            arg = args[0]
            if arg == 'quit':
                return
        try:
            settings = await get_settings(ctx, 'quest')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    quest_enabled = int(settings[3])
                    quest_message = settings[4]
                    
                    # Set message to send          
                    if quest_message == None:
                        quest_message = default_message.replace('%',f'`{command}`')
                    else:
                        quest_message = quest_message.replace('%',f'`{command}`')
                    
                    if not quest_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout_longer)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if the user accepts or denies the quest (different cooldowns)
                        if bot_message.find('Are you looking for a quest?') > -1:
                            bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                            try:
                                message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                message_description = str(bot_answer.embeds[0].description)
                                try:
                                    message_fields = str(bot_answer.embeds[0].fields)
                                    message_title = str(bot_answer.embeds[0].title)
                                except:
                                    message_fields = ''
                                    bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                            except:
                                bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            
                            if bot_message.find('you did not accept the quest') > -1:
                                quest_declined = True
                            elif bot_message.find('got a **new quest**!') > -1:
                                quest_declined = False
                            else:
                                if global_data.debug_mode == True:
                                    await ctx.send('I could not find out if the quest was accepted or declined.')
                                return                      
                        # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                        elif bot_message.find(f'\'s cooldown') > 1:
                            timestring_start = bot_message.find('wait at least **') + 16
                            timestring_end = bot_message.find('**...', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'quest', time_left, quest_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                        # Ignore quest cancellation as it does not reset the cooldown
                        elif bot_message.find('epic quest cancelled') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when trying to do epic quest with active quest
                        elif bot_message.find(f'You cannot do this if you have a pending quest!') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore active quest
                        elif bot_message.find(f'If you don\'t want this quest anymore') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore completed quest
                        elif bot_message.find(f'Completed!') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'quest')
            if quest_declined == True:
                cooldown = 3600
            else:
                cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
                
            # Save task to database
            write_status = await write_reminder(ctx, 'quest', time_left, quest_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Quest detection timeout.')
            return   
    else:
        return
    
# Daily
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def daily(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if  (message.find(f'{ctx_author}\'s daily reward') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have claimed your daily rewards already') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        command = f'rpg daily'
        
        try:
            settings = await get_settings(ctx, 'daily')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    default_message = settings[2]
                    daily_enabled = int(settings[3])
                    daily_message = settings[4]
                    
                    # Set message to send          
                    if daily_message == None:
                        daily_message = default_message.replace('%',f'`{command}`')
                    else:
                        daily_message = daily_message.replace('%',f'`{command}`')
                    
                    if not daily_enabled == 0:
                        bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                        try:
                            message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message_description = str(bot_answer.embeds[0].description)
                            try:
                                message_fields = str(bot_answer.embeds[0].fields)
                                message_title = str(bot_answer.embeds[0].title)
                            except:
                                message_fields = ''
                            bot_message = f'{message_author}{message_description}{message_fields}{message_title}'
                        except:
                            bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                        # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'\'s cooldown') > 1:
                            timestring_start = bot_message.find('wait at least **') + 16
                            timestring_end = bot_message.find('**...', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'daily', time_left, daily_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip_reaction)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
            # Calculate cooldown
            cooldown_data = await get_cooldown(ctx, 'daily')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'daily', time_left, daily_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Daily detection timeout.')
            return   
        
        
        
    



# Ascended commands, used as a test command atm
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def ascended(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message_description = str(m.embeds[0].description)
                try:
                    message_fields = str(m.embeds[0].fields)
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}'
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if global_data.debug_mode == True:
                logger.debug(f'Ascended detection: {message}')
            
            if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                or (message.find(f'{ctx_author}\'s cooldown') > -1) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        try:
            bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Ascended detection timeout.')
            return   

# --- Main menus ---

# Main menu
@bot.command(aliases=('g','h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def help(ctx):
    
    if not ctx.prefix == 'rpg ':
        prefix = await get_prefix(ctx)
                    
        user_settings = (
            f'{emojis.bp} `{prefix}settings` / `{prefix}me` : Check your target enchant\n'
            f'{emojis.bp} `{prefix}set` : Set your target enchant'
        )  
        
        server_settings = (
            f'{emojis.bp} `{prefix}prefix` : Check the bot prefix\n'
            f'{emojis.bp} `{prefix}setprefix` / `{prefix}sp` : Set the bot prefix'
        )  
        
        embed = discord.Embed(
            color = global_data.color,
            title = 'ARCHMAGE',
            description =   f'Well **{ctx.author.name}**, need to do some enchanting?'
        )    
        embed.set_footer(text=await global_data.default_footer(prefix))
        embed.add_field(name='USER SETTINGS', value=user_settings, inline=False)
        embed.add_field(name='SERVER SETTINGS', value=server_settings, inline=False)
        
        await ctx.send(embed=embed)



# --- Miscellaneous ---

# Statistics command
@bot.command(aliases=('statistic','statistics,','devstat','ping','about','info','stats'))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def devstats(ctx):

    if not ctx.prefix == 'rpg ':
        guilds = len(list(bot.guilds))
        user_number = await get_user_number(ctx)
        latency = bot.latency
        
        embed = discord.Embed(
            color = global_data.color,
            title = f'BOT STATISTICS',
            description =   f'{emojis.bp} {guilds:,} servers\n'\
                            f'{emojis.bp} {user_number[0]:,} users\n'\
                            f'{emojis.bp} {round(latency*1000):,} ms latency'
        )
        
        await ctx.send(embed=embed)
  


# --- Owner Commands ---

# Shutdown command (only I can use it obviously)
@bot.command()
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True)
async def shutdown(ctx):

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    if not ctx.prefix == 'rpg ':    
        await ctx.send(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`')
        answer = await bot.wait_for('message', check=check, timeout=30)
        if answer.content.lower() in ['yes','y']:
            await ctx.send(f'Shutting down.')
            await ctx.bot.logout()
        else:
            await ctx.send(f'Phew, was afraid there for a second.')

bot.run(TOKEN)