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
            prefixes = (record[1].replace('"',''),'rpg ',)
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
    elif setting == 'weekly':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, weekly_enabled, weekly_message FROM settings_user where user_id=?'
    elif setting == 'lottery':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, lottery_enabled, lottery_message FROM settings_user where user_id=?'
    elif setting == 'minibossarena':
        sql = 'SELECT reminders_on, user_donor_tier, arena_enabled, miniboss_enabled FROM settings_user where user_id=?'
    elif setting == 'pet':
        sql = 'SELECT reminders_on, user_donor_tier, pet_enabled, pet_message FROM settings_user where user_id=?'
    elif setting == 'donor':
        sql = 'SELECT user_donor_tier, partner_donor_tier FROM settings_user where user_id=?'
        
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

# Get active reminders
async def get_active_reminders(ctx):
    
    current_time = datetime.utcnow().replace(microsecond=0)
    current_time = current_time.timestamp()
    
    active_reminders = 'None'
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT activity, end_time FROM reminders WHERE user_id = ? AND end_time > ? ORDER BY end_time', (ctx.author.id,current_time,))
        record = cur.fetchall()
        
        if record:
            active_reminders = record
        else:
            active_reminders = 'None'
    except sqlite3.Error as error:
        logger.error(f'Routine \'get_active_reminders\' had the following error: {error}')
    
    return active_reminders

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
                    cur.execute('DELETE FROM reminders WHERE user_id = ?', (ctx.author.id,))
                
                    status = (
                        f'**{ctx.author.name}**, your reminders are now turned **off**. All active reminders were deleted.\n'
                        f'Please note that reminders that are about to end within the next ~15s will still trigger.'
                    )
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
        
# Set donor tier
async def set_donor_tier(ctx, donor_tier, partner=False):
    
    if not 0 <= donor_tier <= 7:
        await log_error(ctx, f'Invalid donor tier {donor_tier}, can\'t write that to database.')
        return
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT user_donor_tier, partner_donor_tier FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            user_donor_tier = record[0]
            partner_donor_tier = record[1]
            if partner == True:
                if partner_donor_tier != donor_tier:
                    cur.execute('UPDATE settings_user SET partner_donor_tier = ? WHERE user_id = ?', (donor_tier, ctx.author.id,))
                    status = f'**{ctx.author.name}**, your partner\'s donator tier is now set to **{donor_tier}** ({global_data.donor_tiers[donor_tier]})'
                else:
                    status = f'**{ctx.author.name}**, your partner\'s donator tier is already set to **{donor_tier}** ({global_data.donor_tiers[donor_tier]})'
            else:
                if user_donor_tier != donor_tier:
                    cur.execute('UPDATE settings_user SET user_donor_tier = ? WHERE user_id = ?', (donor_tier, ctx.author.id,))
                    status = f'**{ctx.author.name}**, your donator tier is now set to **{donor_tier}** ({global_data.donor_tiers[donor_tier]})'
                else:
                    status = f'**{ctx.author.name}**, your donator tier is already set to **{donor_tier}** ({global_data.donor_tiers[donor_tier]})'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Enable/disable specific reminder
async def set_specific_reminder(ctx, activity, action):
    
    if action == 'enable':
        enabled = 1
    elif action == 'disable':
        enabled = 0
    else:
        await log_error(ctx, f'Invalid action {action} in \'set_specific_reminder\'')
        if global_data.debug_mode == True:
            status = f'Something went wrong here. Check the error log.'
        return
    
    column = ''
    
    if activity == 'adventure':
        column = 'adv_enabled'
    elif activity == 'daily':
        column = 'daily_enabled'
    elif activity == 'hunt':
        column = 'hunt_enabled'
    elif activity == 'lootbox':
        column = 'lb_enabled'
    elif activity == 'lottery':
        column = 'lottery_enabled'
    elif activity == 'pet':
        column = 'pet_enabled'
    elif activity == 'quest':
        column = 'quest_enabled'
    elif activity == 'training':
        column = 'tr_enabled'
    elif activity == 'weekly':
        column = 'weekly_enabled'
    elif activity == 'work':
        column = 'work_enabled'
    elif activity == 'all':
        column = 'hunt_enabled'
    else:
        await log_error(ctx, f'Invalid activity {activity} in \'set_specific_reminder\'')
        if global_data.debug_mode == True:
            status = f'Something went wrong here. Check the error log.'
        return
    
    try:
        cur=erg_db.cursor()
        
        cur.execute(f'SELECT {column} FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()        
        
        if record:
            if not activity == 'all':
                enabled_db = record[0]
                if enabled_db != enabled:
                    cur.execute(f'UPDATE settings_user SET {column} = ? WHERE user_id = ?', (enabled, ctx.author.id,))
                    if enabled == 0:
                        if activity == 'pet':
                            cur.execute(f'SELECT activity FROM reminders WHERE user_id=?', (ctx.author.id,))
                            active_reminders = cur.fetchall()
                            if active_reminders:
                                pet_reminders = []
                                for reminder in active_reminders:
                                    active_activity = reminder[0]
                                    if active_activity.find('pet-') > -1:
                                        pet_reminders.append(active_activity)
                                for index in range(len(pet_reminders)):
                                    cur.execute('DELETE FROM reminders WHERE user_id = ? and activity = ?', (ctx.author.id,pet_reminders[index],))
                        else:        
                            cur.execute('DELETE FROM reminders WHERE user_id = ? and activity = ?', (ctx.author.id,activity,))
                        status = (
                            f'**{ctx.author.name}**, your {activity} reminder is now **{action}d**.\n'
                            f'All active {activity} reminders have been deleted.'
                        )
                    else:
                        status = f'**{ctx.author.name}**, your {activity} reminder is now **{action}d**.'
                else:
                    status = f'**{ctx.author.name}**, your {activity} reminder is already **{action}d**.'
            else:
                cur.execute(f'UPDATE settings_user SET adv_enabled = ?, daily_enabled = ?, hunt_enabled = ?, lb_enabled = ?,\
                    lottery_enabled = ?, pet_enabled = ?, quest_enabled = ?, tr_enabled = ?, weekly_enabled = ?, work_enabled = ?\
                    WHERE user_id = ?', (enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, ctx.author.id,))
                if enabled == 0:
                    cur.execute(f'DELETE FROM reminders WHERE user_id=?', (ctx.author.id,))
                    status = (
                        f'**{ctx.author.name}**, all of your reminders are now **{action}d**.\n'        
                        f'All active reminders have been deleted.'
                    )
                else:
                    status = f'**{ctx.author.name}**, all of your reminders are now **{action}d**.'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status
        
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
                if cooldown_update == True:
                    cur.execute('UPDATE reminders SET end_time = ?, channel_id = ?, triggered = ? WHERE user_id = ? AND activity = ?', (end_time, ctx.channel.id, triggered, ctx.author.id, activity,))
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
# Parse timestring to seconds
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

# Parse seconds to timestring
async def parse_seconds(time_left):

    days = time_left // 86400
    days = int(days)
    hours = (time_left % 86400) // 3600
    hours = int(hours)
    minutes = (time_left % 3600) // 60
    minutes = int(minutes)
    seconds = time_left % 60
    seconds = int(seconds)
    
    timestring = ''
    if not days == 0:
        timestring = f'{timestring}{days}d '
    if not hours == 0:
        timestring = f'{timestring}{hours}h '
    timestring = f'{timestring}{minutes}m {seconds}s'
    
    return timestring



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




# --- Server Settings ---
   
# Command "setprefix" - Sets new prefix (if user has "manage server" permission)
@bot.command()
@commands.has_permissions(manage_guild=True)
@commands.bot_has_permissions(send_messages=True)
async def setprefix(ctx, *new_prefix):
    
    if not ctx.prefix == 'rpg ':
        if new_prefix:
            if len(new_prefix)>1:
                await ctx.send(
                    f'The command syntax is `{ctx.prefix}setprefix [prefix]`.\n'
                    f'If you want to include a space in your prefix, use \" (example: `{ctx.prefix}setprefix "navi "`)'
                )
            else:
                await set_prefix(bot, ctx, new_prefix[0])
                await ctx.send(f'Prefix changed to `{await get_prefix(ctx)}`.')
        else:
            await ctx.send(
                f'The command syntax is `{ctx.prefix}setprefix [prefix]`.\n'
                f'If you want to include a space in your prefix, use \" (example: `{ctx.prefix}setprefix "navi "`)'
            )

# Command "prefix" - Returns current prefix
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def prefix(ctx):
    
    if not ctx.prefix == 'rpg ':
        current_prefix = await get_prefix(ctx)
        await ctx.send(f'The prefix for this server is `{current_prefix}`\nTo change the prefix use `{current_prefix}setprefix`.')




# --- User Settings ---

# Command "settings" - Returns current user settings
@bot.command(aliases=('me',))
@commands.bot_has_permissions(send_messages=True)
async def settings(ctx):
    
    if not ctx.prefix == 'rpg ':
        settings = await get_settings(ctx, 'all')
        
        settings = list(settings)
            
        if settings == None:
            await ctx.send(f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.')
            return
        else:
            for index in range(7, len(settings)):
                setting = settings[index]
                if setting == 1:
                    settings[index] = 'Enabled'
                elif setting == 0:
                    settings[index] = 'Disabled'
            for index in range(19, len(settings)):
                setting = settings[index]
                if setting == None:
                    settings[index] = '<Default>'
                
            reminders_on = settings[1]
            if reminders_on == 1:
                reminders_on = 'Enabled'
            else:
                reminders_on = 'Disabled'
            user_donor_tier = settings[2]
            default_message = settings[3]
            partner_donor_tier = settings[5]
            adv_enabled = settings[7]
            daily_enabled = settings[9]
            hunt_enabled = settings[10]
            lb_enabled = settings[11]
            lottery_enabled = settings[12]
            pet_enabled = settings[14]
            quest_enabled = settings[15]
            tr_enabled = settings[16]
            weekly_enabled = settings[17]
            work_enabled = settings[18]
            adv_message = settings[19]
            daily_message = settings[21]
            hunt_message = settings[22]
            lb_message = settings[23]
            lottery_message = settings[24]
            pet_message = settings[26]
            quest_message = settings[27]
            tr_message = settings[28]
            weekly_message = settings[29]
            work_message = settings[30]
        
            user_name = ctx.author.name
            user_name = user_name.upper()
        
            general = (
                f'{emojis.bp} Bot: `{reminders_on}`\n'
                f'{emojis.bp} Donator tier: `{user_donor_tier}` ({global_data.donor_tiers[user_donor_tier]})\n'
                f'{emojis.bp} Partner donator tier: `{partner_donor_tier}` ({global_data.donor_tiers[partner_donor_tier]})'
            )
            
            enabled_reminders = (
                f'{emojis.bp} Adventure: `{adv_enabled}`\n'
                f'{emojis.bp} Daily: `{daily_enabled}`\n'
                f'{emojis.bp} Hunt: `{hunt_enabled}`\n'
                f'{emojis.bp} Lootbox: `{lb_enabled}`\n'
                f'{emojis.bp} Lottery: `{lottery_enabled}`\n'
                f'{emojis.bp} Pet: `{pet_enabled}`\n'
                f'{emojis.bp} Quest: `{quest_enabled}`\n'
                f'{emojis.bp} Training: `{tr_enabled}`\n'
                f'{emojis.bp} Weekly: `{weekly_enabled}`\n'
                f'{emojis.bp} Work: `{work_enabled}`'
            )
            
            if reminders_on == 'Disabled':
                enabled_reminders = f'**These settings are ignored because your reminders are off.**\n{enabled_reminders}'
            
            reminder_messages = (
                f'{emojis.bp} Default message: `{default_message}`\n'
                f'{emojis.bp} Adventure: `{adv_message}`\n'
                f'{emojis.bp} Daily: `{daily_message}`\n'
                f'{emojis.bp} Hunt: `{hunt_message}`\n'
                f'{emojis.bp} Lootbox: `{lb_message}`\n'
                f'{emojis.bp} Lottery: `{lottery_message}`\n'
                f'{emojis.bp} Pet: `{pet_message}`\n'
                f'{emojis.bp} Quest: `{quest_message}`\n'
                f'{emojis.bp} Training: `{tr_message}`\n'
                f'{emojis.bp} Weekly: `{weekly_message}`\n'
                f'{emojis.bp} Work: `{work_message}`'
            )
        
            embed = discord.Embed(
                color = global_data.color,
                title = f'{user_name}\'S SETTINGS',
            )    
            embed.add_field(name='GENERAL', value=general, inline=False)
            embed.add_field(name='SPECIFIC REMINDERS', value=enabled_reminders, inline=False)
            embed.add_field(name='REMINDER MESSAGES', value=reminder_messages, inline=False)
        
            await ctx.send(embed=embed)
    
# Command "on" - Activates bot
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def on(ctx, *args):
    
    if not ctx.prefix == 'rpg ':
        status = await set_reminders(ctx, 'on')
        await ctx.send(status)
        
# Command "off" - Deactivates bot
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def off(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    if not ctx.prefix == 'rpg ':
        
        await ctx.send(f'**{ctx.author.name}**, turning off the bot will delete all of your active reminders. Are you sure? `[yes/no]`')
        try:
            answer = await bot.wait_for('message', check=check, timeout=30)
            if answer.content.lower() in ['yes','y']:
                status = await set_reminders(ctx, 'off')
                await ctx.send(status)
            else:
                await ctx.send('Aborted.')
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        
# Command "donator" - Sets donor tiers
@bot.command(aliases=('donator',))
@commands.bot_has_permissions(send_messages=True)
async def donor(ctx, *args):
    
    possible_tiers = (
        f'Possible tiers:\n'
        f'{emojis.bp}`0` : {global_data.donor_tiers[0]}\n'
        f'{emojis.bp}`1` : {global_data.donor_tiers[1]}\n'
        f'{emojis.bp}`2` : {global_data.donor_tiers[2]}\n'
        f'{emojis.bp}`3` : {global_data.donor_tiers[3]}\n'
        f'{emojis.bp}`4` : {global_data.donor_tiers[4]}\n'
        f'{emojis.bp}`5` : {global_data.donor_tiers[5]}\n'
        f'{emojis.bp}`6` : {global_data.donor_tiers[6]}\n'
        f'{emojis.bp}`7` : {global_data.donor_tiers[7]}\n'
    )
    
    settings = await get_settings(ctx, 'donor')
    user_donor_tier = int(settings[0])
    partner_donor_tier = int(settings[1])
    
    if not ctx.prefix == 'rpg ':
        if args:
            if len(args) in (1,2,3):
                arg1 = args[0]
                if arg1 == 'partner':
                    if len(args) == 2:
                        arg2 = args[1]
                        try:
                            partner_donor_tier = int(arg2)
                        except:
                            await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}')
                            return
                        if 0 <= partner_donor_tier <= 7:
                            status = await set_donor_tier(ctx, partner_donor_tier, True)
                            await ctx.send(status)
                            return
                        else:
                            await ctx.send(f'This is not a valid tier.\n\n{possible_tiers}')
                            return
                    else:
                        await ctx.send(
                            f'**{ctx.author.name}**, the EPIC RPG donator tier of your partner is **{partner_donor_tier}** ({global_data.donor_tiers[partner_donor_tier]}).\n'
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}'
                        )
                else:
                    try:
                        donor_tier = int(arg1)
                    except:
                        await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}')
                        return
                    if 0 <= donor_tier <= 7:
                        status = await set_donor_tier(ctx, donor_tier)
                        await ctx.send(status)
                        return
                    else:
                        await ctx.send(f'This is not a valid tier.\n\n{possible_tiers}')
                        return
            else:
                await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}')
                return
                    
        else:
            await ctx.send(
                f'**{ctx.author.name}**, your current EPIC RPG donator tier is **{user_donor_tier}** ({global_data.donor_tiers[user_donor_tier]}).\n'
                f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} [tier]`.\n\n{possible_tiers}'
            )

# Command "enable/disable" - Enables/disables specific reminders
@bot.command(aliases=('disable',))
@commands.bot_has_permissions(send_messages=True)
async def enable(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
        
    if not ctx.prefix == 'rpg ':
        
        activity_list = 'Possible activities:'
        for index in range(len(global_data.activities)):
            activity_list = f'{activity_list}\n{emojis.bp} `{global_data.activities[index]}`'
        
        if args:
            if len(args) == 1:
                
                activity_aliases = {
                    'adv': 'adventure',
                    'lb': 'lootbox',
                    'tr': 'training',
                    'chop': 'work',
                    'fish': 'work',
                    'mine': 'work',
                    'pickup': 'work',
                    'axe': 'work',
                    'net': 'work',
                    'pickaxe': 'work',
                    'ladder': 'work',
                    'boat': 'work',
                    'bowsaw': 'work',
                    'drill': 'work',
                    'tractor': 'work',
                    'chainsaw': 'work',
                    'bigboat': 'work',
                    'dynamite': 'work',
                    'greenhouse': 'work',
                    'pets': 'pet',
                }

                activity = args[0]
                activity = activity.lower()
                
                action = ctx.invoked_with
                
                if activity == 'all' and action == 'disable':
                    await ctx.send(f'**{ctx.author.name}**, turning off all reminders will delete all of your active reminders. Are you sure? `[yes/no]`')
                    try:
                        answer = await bot.wait_for('message', check=check, timeout=30)
                        if not answer.content.lower() in ['yes','y']:
                            await ctx.send('Aborted')
                            return
                    except asyncio.TimeoutError as error:
                        await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

                if activity in activity_aliases:
                    activity = activity_aliases[activity]
                
                if activity in global_data.activities:
                    status = await set_specific_reminder(ctx, activity, action)
                    await ctx.send(status)
                else:
                    await ctx.send(f'There is no reminder for activity `{activity}`.\n\n{activity_list}')
                    return
            else:
                await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity]`.\n\n{activity_list}')
                return
        else:
            await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity]`.\n\n{activity_list}')
            return
        
# Command "list" - Lists all active reminders
@bot.command(name='list',aliases=('reminders',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def list_cmd(ctx):
    
    if not ctx.prefix == 'rpg ':
        
        active_reminders = await get_active_reminders(ctx)

        if active_reminders == 'None':
            reminders = f'{emojis.bp} You have no active reminders'
        else:
            reminders = ''
            for reminder in active_reminders:
                activity = reminder[0]
                end_time = reminder[1]
                if activity.find('pet-') > -1:
                    pet_id = activity.replace('pet-','')
                    activity = f'Pet {pet_id}'
                else:
                    activity = activity.capitalize()
                current_time = datetime.utcnow().replace(microsecond=0)
                end_time_datetime = datetime.fromtimestamp(end_time)
                end_time_difference = end_time_datetime - current_time
                time_left = end_time_difference.total_seconds()
                timestring = await parse_seconds(time_left)
                
                reminders = f'{reminders}\n{emojis.bp}**`{activity}`** (**{timestring}**)'
                
        reminders = reminders.strip()
        user_name = ctx.author.name
        user_name = user_name.upper()
    
        embed = discord.Embed(
            color = global_data.color,
            title = f'{user_name}\'S REMINDERS',
            description = reminders
        )    
        
        await ctx.send(embed=embed)
  


# --- Main menus ---

# Main menu
@bot.command(aliases=('h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def help(ctx):
    
    if not ctx.prefix == 'rpg ':
        prefix = await get_prefix(ctx)
        
        reminder_management = (
            f'{emojis.bp} `{prefix}list` : List all your active reminders'
        )
                    
        user_settings = (
            f'{emojis.bp} `{prefix}on` / `{prefix}off` : Turn the bot on or off\n'
            f'{emojis.bp} `{prefix}settings` : Check your settings\n'
            f'{emojis.bp} `{prefix}donator` : Set your EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}donator partner` : Set your marriage partner\'s EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}enable` / `{prefix}disable` : Enable/disable specific reminders'
        )  
        
        server_settings = (
            f'{emojis.bp} `{prefix}prefix` : Check the bot prefix\n'
            f'{emojis.bp} `{prefix}setprefix` / `{prefix}sp` : Set the bot prefix'
        )  
        
        embed = discord.Embed(
            color = global_data.color,
            title = 'NAVI',
            description =   f'Hey! **{ctx.author.name}**! Hello!'
        )    
        embed.add_field(name='REMINDERS', value=reminder_management, inline=False)
        embed.add_field(name='USER SETTINGS', value=user_settings, inline=False)
        embed.add_field(name='SERVER SETTINGS', value=server_settings, inline=False)
        
        await ctx.send(embed=embed)


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
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or (message.find(f'is in the middle of a command') > -1):
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
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    partner_name = settings[3]
                    partner_donor_tier = int(settings[4])
                    if partner_donor_tier > 3:
                        partner_donor_tier = 3
                    hunt_enabled = int(settings[5])
                    hunt_message = settings[6]
                    
                    # Set message to send          
                    if hunt_message == None:
                        hunt_message = default_message.replace('%',command)
                    else:
                        hunt_message = hunt_message.replace('%',command)
                    
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
                        # Check if partner is in the middle of a command, if yes, if it is the correct one, if not, ignore it and try to wait for the bot message one more time
                        elif bot_message.find(f'is in the middle of a command') > -1:
                            if (bot_message.find(partner_name) > -1) and (bot_message.find(f'is in the middle of a command') > -1):
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
            
            if  ((message.find(f'{ctx_author}** got ') > -1) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                or (message.find('RUBY') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    work_enabled = int(settings[3])
                    work_message = settings[4]
                    
                    # Set message to send          
                    if work_message == None:
                        work_message = default_message.replace('%',command)
                    else:
                        work_message = work_message.replace('%',command)
                    
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    tr_enabled = int(settings[3])
                    tr_message = settings[4]
                    
                    # Set message to send          
                    if tr_message == None:
                        tr_message = default_message.replace('%',command)
                    else:
                        tr_message = tr_message.replace('%',command)
                    
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    adv_enabled = int(settings[3])
                    adv_message = settings[4]
                    
                    # Set message to send          
                    if adv_message == None:
                        adv_message = default_message.replace('%',command)
                    else:
                        adv_message = adv_message.replace('%',command)
                    
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
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    if ctx.prefix == 'rpg ' and args:     
        command = f'rpg buy lootbox'
        arg1 = ''
        arg2 = ''
        arg1 = args[0]
        if len(args) == 2:
            arg2 = args[1]
        if arg1 == 'lottery' and arg2 == 'ticket':
            x = await lottery(ctx, args)
            return
        elif (len(args) in (1,2)) and ((arg1 in ('lb','lootbox',)) or (arg2 in ('lb','lootbox',))):
            try:
                settings = await get_settings(ctx, 'lootbox')
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
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
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
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    daily_enabled = int(settings[3])
                    daily_message = settings[4]
                    
                    # Set message to send          
                    if daily_message == None:
                        daily_message = default_message.replace('%',command)
                    else:
                        daily_message = daily_message.replace('%',command)
                    
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
        
# Weekly
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def weekly(ctx, *args):
    
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
            
            if  (message.find(f'{ctx_author}\'s weekly reward') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have claimed your weekly rewards already') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        command = f'rpg weekly'
        
        try:
            settings = await get_settings(ctx, 'weekly')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    weekly_enabled = int(settings[3])
                    weekly_message = settings[4]
                    
                    # Set message to send          
                    if weekly_message == None:
                        weekly_message = default_message.replace('%',command)
                    else:
                        weekly_message = weekly_message.replace('%',command)
                    
                    if not weekly_enabled == 0:
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
                            write_status = await write_reminder(ctx, 'weekly', time_left, weekly_message, True)
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
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
            cooldown_data = await get_cooldown(ctx, 'weekly')
            cooldown = int(cooldown_data[0])
            donor_affected = int(cooldown_data[1])
            if donor_affected == 1:
                time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
            else:
                time_left = cooldown
            
            # Save task to database
            write_status = await write_reminder(ctx, 'weekly', time_left, weekly_message)
            
            # Add reaction
            if not write_status == 'aborted':
                await bot_answer.add_reaction(emojis.navi)
            else:
                if global_data.debug_mode == True:
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Weekly detection timeout.')
            return    
        
# Lottery
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def lottery(ctx, *args):
    
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
            
            if  (message.find(f'Join with `rpg lottery buy [amount]`') > -1) or ((message.find(f'{ctx_author}') > -1) and (message.find(f'lottery ticket successfully bought') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot buy more than 10 tickets per lottery') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        command = f'rpg buy lottery ticket'
            
        try:
            settings = await get_settings(ctx, 'lottery')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[1])
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[2]
                    lottery_enabled = int(settings[3])
                    lottery_message = settings[4]
                    
                    # Set message to send          
                    if lottery_message == None:
                        lottery_message = default_message.replace('%',command)
                    else:
                        lottery_message = lottery_message.replace('%',command)
                    
                    if not lottery_enabled == 0:
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

                        # Check if lottery overview, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'**Next draw**') > 1:
                            timestring_start = bot_message.find('**Next draw**:') + 15
                            timestring_end = bot_message.find('s', timestring_start) + 1
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'lottery', time_left, lottery_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Check if lottery ticket confirmation overview, if yes, read the time and update/insert the reminder if necessary
                        if bot_message.find(f'lottery ticket successfully bought') > 1:
                            timestring_start = bot_message.find('winner in **') + 12
                            timestring_end = bot_message.find('**', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            timestring = timestring.lower()
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_reminder(ctx, 'lottery', time_left, lottery_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore max bought lottery ticket info
                        elif bot_message.find('you cannot buy more') > 1:
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Lottery detection timeout.')
            return    

# Big arena / Not so mini boss
@bot.command(aliases=('not',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def big(ctx, *args):
    
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
            
            if  ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **big arena** event') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **not so "mini" boss** event') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you are already registered!') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        if args:
            full_args = ''
            for arg in args:
                full_args = f'{full_args}{arg}'
        else:
            return
                
        if full_args in ('sominibossjoin','arenajoin',):
            if full_args == 'sominibossjoin':
                event = 'miniboss'
            elif full_args == 'arenajoin':
                event = 'arena'
                
            try:
                settings = await get_settings(ctx, 'minibossarena')
                if not settings == None:
                    reminders_on = settings[0]
                    if not reminders_on == 0:
                        user_donor_tier = int(settings[1])
                        if user_donor_tier > 3:
                            user_donor_tier = 3
                        arena_enabled = int(settings[2])
                        miniboss_enabled = int(settings[3])
                        
                        # Set message to send          
                        arena_message = global_data.arena_message
                        miniboss_message = global_data.miniboss_message
                        
                        if not ((event == 'miniboss') and (miniboss_enabled == 0)) or ((event == 'arena') and (miniboss_enabled == 0)):
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

                            # Check if event message with time in it, if yes, read the time and update/insert the reminder if necessary
                            if bot_message.find(f'The next event is in') > -1:
                                timestring_start = bot_message.find('event is in **') + 14
                                timestring_end = bot_message.find('**,', timestring_start)
                                timestring = bot_message[timestring_start:timestring_end]
                                timestring = timestring.lower()
                                time_left = await parse_timestring(ctx, timestring)
                                if event == 'miniboss':
                                    write_status = await write_reminder(ctx, 'miniboss', time_left, miniboss_message, True)
                                elif event == 'bigarena':
                                    write_status = await write_reminder(ctx, 'arena', time_left, arena_message, True)
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
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if global_data.debug_mode == True:
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                        else:
                            return
                    else:
                        return
                else:
                    return
                
            except asyncio.TimeoutError as error:
                if global_data.debug_mode == True:
                    await ctx.send('Big arena / Not so mini boss detection timeout.')
                return    

# Pets
@bot.command(aliases=('pets',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def pet(ctx, *args):
    
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
            
            if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet are you trying to select?') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'this pet is already in an adventure!') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('Your pet started an adventure, it will be back') > -1) or ((message.find('Your pet started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
        
        command = f'rpg pet adventure'
        
        if args:
            if len(args) == 3:
                arg1 = args[0]
                pet_id = args[1]
                pet_id = pet_id.upper()
                pet_action = args[2]
                if (arg1 in ('adv', 'adventure',)) and pet_action in ('dig', 'learn', 'drill',):
                    try:
                        settings = await get_settings(ctx, 'pet')
                        if not settings == None:
                            reminders_on = settings[0]
                            if not reminders_on == 0:
                                user_donor_tier = int(settings[1])
                                if user_donor_tier > 3:
                                    user_donor_tier = 3
                                pet_enabled = int(settings[2])
                                pet_message = settings[3]
                                
                                # Set message to send          
                                if pet_message == None:
                                    pet_message = global_data.pet_message.replace('%',command).replace('$',pet_id)
                                else:
                                    pet_message = pet_message.replace('%',command).replace('$',pet_id)
                                
                                if not pet_enabled == 0:
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

                                    # Check if pet adventure started overview, if yes, read the time and update/insert the reminder
                                    if bot_message.find('Your pet started an adventure, it will be back') > -1:
                                        timestring_start = bot_message.find('back in **') + 10
                                        timestring_end = bot_message.find('**!', timestring_start)
                                        timestring = bot_message[timestring_start:timestring_end]
                                        timestring = timestring.lower()
                                        time_left = await parse_timestring(ctx, timestring)
                                        write_status = await write_reminder(ctx, f'pet-{pet_id}', time_left, pet_message, True)
                                        if write_status in ('inserted','scheduled','updated'):
                                            await bot_answer.add_reaction(emojis.navi)
                                        else:
                                            if global_data.debug_mode == True:
                                                await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that max amount of pets is on adventures
                                    elif bot_message.find('you cannot send another pet') > 1:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that ID is wrong
                                    elif bot_message.find('what pet are you trying to select?') > 1:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that pet is already on adventure
                                    elif bot_message.find('this pet is already in an adventure') > 1:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore time traveler instant pet return
                                    elif bot_message.find('IT CAME BACK INSTANTLY!') > 1:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                        await bot_answer.add_reaction(emojis.timetraveler)
                                        return
                                    # Ignore error that pets are not unlocked yet
                                    elif bot_message.find('unlocked after second') > 1:
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
                                    # Ignore error when another command is active
                                    elif bot_message.find('end your previous command') > 1:
                                        if global_data.debug_mode == True:
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                else:
                                    return
                            else:
                                return
                        else:
                            return
                        
                    except asyncio.TimeoutError as error:
                        if global_data.debug_mode == True:
                            await ctx.send('Pet detection timeout.')
                        return    

# Cooldowns
@bot.command(aliases=('cd',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def cooldown(ctx, *args):
    
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
            
            if  (message.find(f'{ctx_author}\'s cooldowns') > -1) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ':
            
        try:
            settings = await get_settings(ctx, 'all')
            if not settings == None:
                reminders_on = settings[1]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[2])
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[3]
                    adv_enabled = settings[7]
                    daily_enabled = settings[9]
                    lb_enabled = settings[11]
                    quest_enabled = settings[15]
                    tr_enabled = settings[16]
                    weekly_enabled = settings[17]
                    adv_message = settings[19]
                    daily_message = settings[21]
                    lb_message = settings[23]
                    quest_message = settings[27]
                    tr_message = settings[28]
                    weekly_message = settings[29]
                    
                    if not ((adv_enabled == 0) and (daily_enabled == 0) and (lb_enabled == 0) and (quest_enabled == 0) and (tr_enabled == 0) and (weekly_enabled == 0)):
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
                            
                            write_status_list = []
                            
                            for cooldown in cooldowns:
                                activity = cooldown[0]
                                timestring = cooldown[1]
                                message = cooldown[2]
                                time_left = await parse_timestring(ctx, timestring)
                                write_status = await write_reminder(ctx, activity, time_left, message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    write_status_list.append('OK')
                                else:
                                    write_status_list.append('Fail')
                                
                            if not 'Fail' in write_status_list:                       
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if global_data.debug_mode == True:
                                    await ctx.send(f'Something went wrong here. {write_status_list} {cooldowns}')
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
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if global_data.debug_mode == True:
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
        except asyncio.TimeoutError as error:
            if global_data.debug_mode == True:
                await ctx.send('Cooldown detection timeout.')
            return
    else:
        x = await list_cmd(ctx)
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
        try:
            await ctx.send(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`')
            answer = await bot.wait_for('message', check=check, timeout=30)
            if answer.content.lower() in ['yes','y']:
                await ctx.send(f'Shutting down.')
                await ctx.bot.logout()
            else:
                await ctx.send(f'Phew, was afraid there for a second.')
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')

bot.run(TOKEN)