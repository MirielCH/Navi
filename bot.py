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

# Read the bot token from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE')

# Initialize logger
logger = logging.getLogger('discord')
if DEBUG_MODE == 'ON':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(filename=logfile,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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
            prefixes = (record[1].replace('"',''),'rpg ','Rpg ','rPg ','rpG ','RPg ','rPG ','RpG ','RPG ')
        else:
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, global_data.default_prefix,))
            prefixes = (global_data.default_prefix,'rpg ','Rpg ','rPg ','rpG ','RPg ','rPG ','RpG ','RPG ')
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
async def get_settings(ctx, setting='all', partner_id=None):
    
    current_settings = None
    
    if setting == 'all':
        sql = 'SELECT * FROM settings_user where user_id=?'
    elif setting == 'hunt':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, partner_name, partner_donor_tier, partner_id, hunt_enabled, hunt_message FROM settings_user where user_id=?'
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
        sql = 'SELECT reminders_on, default_message, user_donor_tier, pet_enabled, pet_message FROM settings_user where user_id=?'
    elif setting == 'donor':
        sql = 'SELECT user_donor_tier FROM settings_user where user_id=?'
    elif setting == 'partner':
        sql = 'SELECT partner_donor_tier, partner_id, partner_channel_id FROM settings_user where user_id=?'
    elif setting == 'alert_channel':
        sql = 'SELECT partner_channel_id, reminders_on, alert_enabled FROM settings_user where user_id=?'
    elif setting == 'events':
        sql = 'SELECT reminders_on, default_message, arena_enabled, arena_message, lottery_enabled, lottery_message, miniboss_enabled, miniboss_message, pet_enabled, pet_message FROM settings_user where user_id=?'
        
    try:
        cur=erg_db.cursor()
        if not setting == 'alert_channel':
            cur.execute(sql, (ctx.author.id,))
        else:
            if not partner_id == None:
                cur.execute(sql, (partner_id,))
            else:
                await log_error(ctx, f'Invalid partner_id {partner_id} in get_settings')
                return
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

# Get guild
async def get_guild(ctx, type):
    
    try:
        cur=erg_db.cursor()
        
        if type == 'leader':
            cur.execute('SELECT guild_name, reminders_on, stealth_threshold, stealth_current, guild_channel_id, guild_message FROM guilds where guild_leader=?', (ctx.author.id,))
        elif type == 'member':
            cur.execute('SELECT guild_name, reminders_on, stealth_threshold, stealth_current, guild_channel_id, guild_message FROM guilds where member1_id=? or member2_id=? or member3_id=? or member4_id=? or member5_id=? or member6_id=? or member7_id=? or member8_id=? or member9_id=? or member10_id=?', (ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,))
        record = cur.fetchone()
    
        if record:
            guild_data = record
        else:
            guild_data = None
    
    except sqlite3.Error as error:
        await log_error(ctx, error)    
  
    return guild_data

# Get guild members
async def get_guild_members(guild_name):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT member1_id, member2_id, member3_id, member4_id, member5_id, member6_id, member7_id, member8_id, member9_id, member10_id FROM guilds WHERE guild_name=?', (guild_name,))
        record = cur.fetchone()
    
        if record:
            guild_members = record
        else:
            guild_members = None
    
    except sqlite3.Error as error:
        logger.error(f'Unable to get guild members: {error}')
  
    return guild_members

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
                status = f'Hey! **{ctx.author.name}**! Welcome! Your reminders are now turned **on**.\nDon\'t forget to set your donor tier with `{ctx.prefix}donator`.\nYou can check all of your settings with `{ctx.prefix}settings` or `{ctx.prefix}me`.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set partner
async def set_partner(ctx, partner_id, both=False):
    
    try:
        if both == True:
            cur=erg_db.cursor()
            cur.execute('SELECT partner_id, user_donor_tier FROM settings_user WHERE user_id=?', (ctx.author.id,))
            record = cur.fetchone()
            cur.execute('SELECT partner_id, user_donor_tier FROM settings_user WHERE user_id=?', (partner_id,))
            record_partner = cur.fetchone()
        else:
            cur=erg_db.cursor()
            cur.execute('SELECT partner_id FROM settings_user WHERE user_id=?', (ctx.author.id,))
            record = cur.fetchone()

        if both == True:
            if record and record_partner:
                partner_id_db = record[0]
                partner_user_donor_tier_db = record[1]
                user_id_db = record_partner[0]
                user_user_donor_tier_db = record_partner[1]
                cur.execute('UPDATE settings_user SET partner_id = ?, partner_donor_tier = ? WHERE user_id = ?', (partner_id, user_user_donor_tier_db, ctx.author.id,))
                cur.execute('UPDATE settings_user SET partner_id = ?, partner_donor_tier = ? WHERE user_id = ?', (ctx.author.id, partner_user_donor_tier_db, partner_id,))
                status = 'updated'
            else:
                status = f'One or both of you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
        else:
            if record:
                partner_id_db = record[0]
                if partner_id_db != partner_id:
                    cur.execute('UPDATE settings_user SET partner_id = ? WHERE user_id = ?', (partner_id, ctx.author.id,))
                    status = 'updated'
                else:
                    status = 'unchanged'
            else:
                status = f'**{ctx.author.id}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
                
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Reset partner
async def reset_partner(ctx):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT partner_id FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()

        if record:
            partner_id = record[0]
            cur.execute('UPDATE settings_user SET partner_id = ?, partner_donor_tier = ? WHERE user_id = ?', (None, 0, ctx.author.id,))
            if not partner_id == None:
                cur.execute('UPDATE settings_user SET partner_id = ?, partner_donor_tier = ? WHERE user_id = ?', (None, 0, partner_id,))
            status = 'updated'
        else:
            status = f'**{ctx.author.id}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
                
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set partner for hunt together detection
async def set_hunt_partner(ctx, partner_name):
    
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
        
# Set lootbox alert channel
async def set_partner_channel(ctx, partner_channel_id):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT partner_channel_id FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            partner_channel_id_db = record[0]
            if partner_channel_id_db != partner_channel_id:
                cur.execute('UPDATE settings_user SET partner_channel_id = ? WHERE user_id = ?', (partner_channel_id, ctx.author.id,))
                status = 'updated'
            else:
                status = 'unchanged'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status
        
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
        if DEBUG_MODE == 'ON':
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
    elif activity == 'lootbox-alert':
        column = 'alert_enabled'
    else:
        await log_error(ctx, f'Invalid activity {activity} in \'set_specific_reminder\'')
        if DEBUG_MODE == 'ON':
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
                        if not activity == 'lootbox-alert':
                            status = (
                                f'**{ctx.author.name}**, your {activity} reminder is now **{action}d**.\n'
                                f'All active {activity} reminders have been deleted.'
                            )
                        else:
                            status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are now **{action}d**.'
                    else:
                        if not activity == 'lootbox-alert':
                            status = f'**{ctx.author.name}**, your {activity} reminder is now **{action}d**.'
                        else:
                            status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are now **{action}d**.'
                else:
                    if not activity == 'lootbox-alert':
                        status = f'**{ctx.author.name}**, your {activity} reminder is already **{action}d**.'
                    else:
                        status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are already **{action}d**.'
            else:
                cur.execute(f'UPDATE settings_user SET adv_enabled = ?, alert_enabled = ?, daily_enabled = ?, hunt_enabled = ?, lb_enabled = ?,\
                    lottery_enabled = ?, pet_enabled = ?, quest_enabled = ?, tr_enabled = ?, weekly_enabled = ?, work_enabled = ?\
                    WHERE user_id = ?', (enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, ctx.author.id,))
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
async def write_reminder(ctx, activity, time_left, message, cooldown_update=False, no_insert=False):
    
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
            if 0 <= time_difference.total_seconds() <= 15 and db_triggered == 1:
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
                if no_insert == False:
                    cur.execute('INSERT INTO reminders (user_id, activity, end_time, channel_id, message) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, activity, end_time, ctx.channel.id, message,))
                    status = 'inserted'
                else:
                    status = 'ignored'
            else:
                if no_insert == False:
                    cur.execute('INSERT INTO reminders (user_id, activity, end_time, channel_id, message, triggered) VALUES (?, ?, ?, ?, ?, ?)', (ctx.author.id, activity, end_time, ctx.channel.id, message,1))
                    task_name = f'{ctx.author.id}-{activity}'
                    bot.loop.create_task(background_task(ctx.author, ctx.channel, message, time_left, task_name))
                    status = 'scheduled'
                else:
                    status = 'ignored'
                    
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return status

# Write guild reminder
async def write_guild_reminder(ctx, guild_name, guild_channel_id, time_left, message, cooldown_update=False):
    
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
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (guild_name, 'guild',))
        record = cur.fetchone()
        
        if record:
            db_time = float(record[0])
            db_time_datetime = datetime.fromtimestamp(db_time)
            db_triggered = int(record[1])
            time_difference = db_time_datetime - current_time
            if 0 <= time_difference.total_seconds() <= 15 and db_triggered == 1:
                task_name = f'{guild_name}-guild'
                if task_name in running_tasks:
                    running_tasks[task_name].cancel()    
                bot.loop.create_task(background_task(guild_name, guild_channel_id, message, time_left, task_name))
                status = 'scheduled'
            else:
                if cooldown_update == True:
                    cur.execute('UPDATE reminders SET end_time = ?, channel_id = ?, triggered = ? WHERE user_id = ? AND activity = ?', (end_time, guild_channel_id, triggered, guild_name, 'guild',))
                else:
                    cur.execute('UPDATE reminders SET end_time = ?, channel_id = ?, message = ?, triggered = ? WHERE user_id = ? AND activity = ?', (end_time, guild_channel_id, message, triggered, guild_name, 'guild',))
                status = 'updated'
        else:
            if time_left > 15:
                cur.execute('INSERT INTO reminders (user_id, activity, end_time, channel_id, message) VALUES (?, ?, ?, ?, ?)', (guild_name, 'guild', end_time, guild_channel_id, message,))
                status = 'inserted'
            else:
                cur.execute('INSERT INTO reminders (user_id, activity, end_time, channel_id, message, triggered) VALUES (?, ?, ?, ?, ?, ?)', (guild_name, 'guild', end_time, guild_channel_id, message,1))
                task_name = f'{guild_name}-guild'
                bot.loop.create_task(background_task(guild_name, guild_channel_id, message, time_left, task_name))
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

# Update guild
async def update_guild(guild_name, guild_leader, guild_members):

    try:
        cur=erg_db.cursor()
        cur.execute('SELECT * FROM guilds where guild_name=?', (guild_name,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE guilds SET guild_leader = ?, member1_id = ?, member2_id = ?, member3_id = ?, member4_id = ?, member5_id = ?, member6_id = ?, member7_id = ?, member8_id = ?, member9_id = ?, member10_id = ? where guild_name = ?', (guild_leader, guild_members[0], guild_members[1], guild_members[2], guild_members[3], guild_members[4], guild_members[5], guild_members[6], guild_members[7], guild_members[8], guild_members[9], guild_name,))
        else:
            cur.execute('INSERT INTO guilds VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (guild_name, guild_leader, 0, guild_members[0], guild_members[1], guild_members[2], guild_members[3], guild_members[4], guild_members[5], guild_members[6], guild_members[7], guild_members[8], guild_members[9],global_data.guild_stealth,0,None,global_data.default_message,))
    except sqlite3.Error as error:
        logger.error(f'Error updating guild information. Guild name: {guild_name}, guild leader: {guild_leader}, guild members: {guild_members}')

# Set guild alert channel
async def set_guild_channel(ctx, guild_channel_id):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT guild_channel_id FROM guilds WHERE guild_leader=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            guild_channel_id_db = record[0]
            if guild_channel_id_db != guild_channel_id:
                cur.execute('UPDATE guilds SET guild_channel_id = ? WHERE guild_leader = ?', (guild_channel_id, ctx.author.id,))
                status = 'updated'
            else:
                status = 'unchanged'
        else:
            status = f'**{ctx.author.name}**, couldn\'t find your guild.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set guild stealth threshold
async def set_guild_stealth_threshold(ctx, guild_stealth):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT stealth_threshold FROM guilds WHERE guild_leader=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE guilds SET stealth_threshold = ? WHERE guild_leader = ?', (guild_stealth, ctx.author.id,))
            status = 'updated'
        else:
            status = f'**{ctx.author.name}**, couldn\'t find your guild.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set current guild stealth
async def set_guild_stealth_current(ctx, guild_name, guild_stealth):
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT stealth_current FROM guilds WHERE guild_name=?', (guild_name,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE guilds SET stealth_current = ? WHERE guild_name = ?', (guild_stealth, guild_name,))
            status = 'updated'
        else:
            status = f'**{ctx.author.name}**, couldn\'t find your guild.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Toggle guild reminders on or off
async def set_guild_reminders(ctx, guild_name, action):
    
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
        cur.execute('SELECT reminders_on, guild_channel_id FROM guilds where guild_name=?', (guild_name,))
        record = cur.fetchone()
        
        if record:
            guild_channel_id = record[1]
            if guild_channel_id == None:
                status = f'**{ctx.author.name}**, you need to set an alert channel for the guild **{guild_name}** first.\nUse `{ctx.prefix}{ctx.invoked_with} channel set` to do that.'
            else:
                reminders_status = int(record[0])
                if reminders_status == 1 and reminders_on == 1:
                    status = f'**{ctx.author.name}**, reminders for the guild **{guild_name}** are already turned on.'
                elif reminders_status == 0 and reminders_on == 0:
                    status = f'**{ctx.author.name}**, reminders for the guild **{guild_name}** are already turned off.'
                else:
                    cur.execute('UPDATE guilds SET reminders_on = ? where guild_name = ?', (reminders_on, guild_name,))
                    status = f'**{ctx.author.name}**, reminders for the guild **{guild_name}** are now turned **{action}**.'
        else:
            status = f'**{ctx.author.name}**, couldn\'t find your guild.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Weekly guild reset
async def reset_guilds(bot):
    try:
        cur=erg_db.cursor()
        cur.execute('DELETE FROM reminders WHERE activity = ?', ('guild',))
        cur.execute('UPDATE guilds SET stealth_current = ?', (1,))
        cur.execute('SELECT guild_name, guild_channel_id, guild_message FROM guilds')
        records = cur.fetchall()
        if records:
            for record in records:
                guild_name = record[0]
                guild_channel_id = record[1]
                guild_message = record[2]
                guild_message = guild_message.replace('%','rpg guild upgrade')
                task_name = f'{guild_name}-guild'
                await bot.wait_until_ready()
                channel = bot.get_channel(guild_channel_id)
                if task_name in running_tasks:
                    running_tasks[task_name].cancel()    
                
                bot.loop.create_task(background_task(guild_name, channel, guild_message, 60, task_name, True))
        
    except sqlite3.Error as error:
        logger.error('Error resetting guilds.')



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
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=get_prefix_all, help_command=None, case_insensitive=True, intents=intents)



# --- Ready & Join Events ---

# Set bot status when ready
@bot.event
async def on_ready():
    
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='your commands'))
    schedule_reminders.start(bot)
    delete_old_reminders.start(bot)
    reset_guild.start(bot)
    
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
async def background_task(user, channel, message, time_left, task_name, guild=False):
        
    await asyncio.sleep(time_left)
    try:
        if guild == False:
            await bot.wait_until_ready()
            await bot.get_channel(channel.id).send(f'{user.mention} {message}')
        else:
            guild_members = await get_guild_members(user)
            message_mentions = ''
            for member in guild_members:
                if not member == '':
                    await bot.wait_until_ready()
                    member_user = bot.get_user(member)
                    if not member_user == None:
                        message_mentions = f'{message_mentions}{member_user.mention} '
            await bot.wait_until_ready()
            await bot.get_channel(channel.id).send(f'{message_mentions}{message}')
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
                user_id = reminder[0]
                activity = reminder[1]
                end_time = float(reminder[2])
                channel_id = int(reminder[3])
                message = reminder[4]
                await bot.wait_until_ready()
                channel = bot.get_channel(channel_id)
                if not activity == 'guild':
                    await bot.wait_until_ready()
                    user = bot.get_user(user_id)
                
                current_time = datetime.utcnow().replace(microsecond=0)
                end_time_datetime = datetime.fromtimestamp(end_time)
                end_time_difference = end_time_datetime - current_time
                time_left = end_time_difference.total_seconds()
                
                task_name = f'{user_id}-{activity}'
                if not activity == 'guild':
                    task = bot.loop.create_task(background_task(user, channel, message, time_left, task_name))
                else:
                    task = bot.loop.create_task(background_task(user_id, channel, message, time_left, task_name, True))
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
                if DEBUG_MODE == 'ON':
                    if triggered == 1:
                        logger.info(f'{datetime.now()}: Deleted this old reminder {reminder}')
                    else:
                        logger.error(f'{datetime.now()}: Deleted this old reminder that was never triggered: {reminder}')
            except:
                logger.error(f'{datetime.now()}: Error deleting old reminder {reminder}')

# Task to reset guild
@tasks.loop(minutes=1.0)
async def reset_guild(bot):
    
    reset_weekday = global_data.guild_reset[0]
    reset_hour = global_data.guild_reset[1]
    reset_minute = global_data.guild_reset[2]
    
    today = datetime.today().weekday()
    
    if datetime.today().weekday() == reset_weekday:
        now = datetime.utcnow()
        if now.hour == reset_hour and now.minute == reset_minute:
            await reset_guilds(bot)
            


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
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def settings(ctx):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        settings = await get_settings(ctx, 'all')
        guild_data = await get_guild(ctx, 'member')
        
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
            partner_id = settings[6]
            partner_channel = settings[7]
            adv_enabled = settings[9]
            alert_enabled = settings[10]
            daily_enabled = settings[12]
            hunt_enabled = settings[13]
            lb_enabled = settings[14]
            lottery_enabled = settings[15]
            pet_enabled = settings[16]
            quest_enabled = settings[17]
            tr_enabled = settings[19]
            weekly_enabled = settings[20]
            work_enabled = settings[21]
            adv_message = settings[22]
            alert_message = settings[23]
            daily_message = settings[25]
            hunt_message = settings[26]
            lb_message = settings[27]
            lottery_message = settings[28]
            pet_message = settings[30]
            quest_message = settings[31]
            tr_message = settings[32]
            weekly_message = settings[33]
            work_message = settings[34]
        
            if not guild_data == None:
                guild_name = guild_data[0]
                guild_reminders_on = guild_data[1]
                if guild_reminders_on == 1:
                    guild_reminders_on = 'Enabled'
                else:
                    guild_reminders_on = 'Disabled'
                guild_stealth = guild_data[2]
                guild_channel = guild_data[4]
            else:
                guild_name = 'None'
                guild_reminders_on = 'Disabled'
                guild_stealth = 'N/A'
                guild_channel = None
        
            user_name = ctx.author.name
            user_name = user_name.upper()
            
            await bot.wait_until_ready()
            if not partner_id == None:
                partner = bot.get_user(partner_id)
                if not partner == None:
                    partner_name = f'{partner.name}#{partner.discriminator}'
                else:
                    partner_name = 'None'
            else:
                partner_name = 'None'
            
            if not partner_channel == None:
                await bot.wait_until_ready()
                partner_channel_name = bot.get_channel(partner_channel)
            else:
                partner_channel_name = 'None'
            
            if not guild_channel == None:
                await bot.wait_until_ready()
                guild_channel_name = bot.get_channel(guild_channel)
            else:
                guild_channel_name = 'None'
            
        
            general = (
                f'{emojis.bp} Bot: `{reminders_on}`\n'
                f'{emojis.bp} Donator tier: `{user_donor_tier}` ({global_data.donor_tiers[user_donor_tier]})\n'
            )
            
            partner = (
                f'{emojis.bp} Partner: `{partner_name}`\n'
                f'{emojis.bp} Partner donator tier: `{partner_donor_tier}` ({global_data.donor_tiers[partner_donor_tier]})\n'
                f'{emojis.bp} Lootbox alert channel: `{partner_channel_name}`'
            )
            
            guild = (
                f'{emojis.bp} Guild: `{guild_name}`\n'
                f'{emojis.bp} Guild reminders: `{guild_reminders_on}`\n'
                f'{emojis.bp} Guild alert channel: `{guild_channel_name}`\n'
                f'{emojis.bp} Guild stealth threshold: `{guild_stealth}`'
            )
            
            enabled_reminders = (
                f'{emojis.bp} Adventure: `{adv_enabled}`\n'
                f'{emojis.bp} Daily: `{daily_enabled}`\n'
                f'{emojis.bp} Hunt: `{hunt_enabled}`\n'
                f'{emojis.bp} Lootbox: `{lb_enabled}`\n'
                f'{emojis.bp} Lottery: `{lottery_enabled}`\n'
                f'{emojis.bp} Partner lootbox alert: `{alert_enabled}`\n'
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
            embed.add_field(name='PARTNER', value=partner, inline=False)
            embed.add_field(name='GUILD', value=guild, inline=False)
            embed.add_field(name='SPECIFIC REMINDERS', value=enabled_reminders, inline=False)
            #embed.add_field(name='REMINDER MESSAGES', value=reminder_messages, inline=False)
        
            await ctx.send(embed=embed)

# Command "on" - Activates bot
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def on(ctx, *args):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        status = await set_reminders(ctx, 'on')
        await ctx.send(status)
        
# Command "off" - Deactivates bot
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def off(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
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
        
# Command "donator" - Sets user donor tier
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
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
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

# Command "partner" - Sets marriage partner settings
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def partner(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    def partner_check(m):
        return m.author in ctx.message.mentions and m.channel == ctx.channel
    
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
    
    settings = await get_settings(ctx, 'partner')
    partner_donor_tier = int(settings[0])
    partner_id = settings[1]
    partner_channel = settings[2]
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        if args:
            if len(args) in (1,2):
                arg1 = args[0]
                if arg1 in ('donator', 'donor'):
                    if len(args) == 2:
                        arg2 = args[1]
                        try:
                            partner_donor_tier = int(arg2)
                        except:
                            await ctx.send(f'The syntax is `{ctx.prefix}{ctx.invoked_with} donator [tier]`')
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
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} donator [tier]`.\n\n{possible_tiers}'
                        )
                elif arg1 == 'channel':
                    if len(args) == 2:
                        arg2 = args[1]
                        if arg2 == 'set':
                            if not partner_id == None:
                                await ctx.send(f'**{ctx.author.name}**, set `{ctx.channel.name}` as your lootbox alert channel? `[yes/no]`')
                                answer = await bot.wait_for('message', check=check, timeout=30)
                                if answer.content.lower() in ['yes','y']:
                                    status = await set_partner_channel(ctx, ctx.channel.id)
                                    if status == 'updated':
                                        await ctx.send(f'**{ctx.author.name}**, `{ctx.channel.name}` is now set as your lootbox alert channel.')
                                        return
                                    elif status == 'unchanged':
                                        await ctx.send(f'**{ctx.author.name}**, `{ctx.channel.name}` is already set as your lootbox alert channel.')
                                        return
                                    else:
                                        await ctx.send(status)
                                        return
                                else:
                                    await ctx.send(f'Aborted.')
                                    return
                            else:
                                await ctx.send(
                                    f'You don\'t have a partner set.\n'
                                    f'If you want to set a partner, use `{ctx.prefix}{ctx.invoked_with} [@User]`'
                                )
                                return
                        elif arg2 == 'reset':
                            if not partner_channel == None:
                                await bot.wait_until_ready()
                                channel = bot.get_channel(partner_channel)
                                if channel == None:
                                    channel_name = 'Invalid channel'
                                else:
                                    channel_name = channel.name
                                    
                                await ctx.send(f'**{ctx.author.name}**, do you want to remove **{channel_name}** as your lootbox alert channel? `[yes/no]`')
                                answer = await bot.wait_for('message', check=check, timeout=30)
                                if answer.content.lower() in ['yes','y']:
                                    status = await set_partner_channel(ctx, None)
                                    if status == 'updated':
                                        await ctx.send(f'**{ctx.author.name}**, you now don\'t have a lootbox alert channel set anymore.')
                                        return
                                    else:
                                        await ctx.send(status)
                                        return
                                else:
                                    await ctx.send(f'Aborted.')
                                    return
                            else:
                                await ctx.send(f'You don\'t have a lootbox alert channel set, there is no need to reset it.')
                                return
                    else:
                        await bot.wait_until_ready()
                        channel = bot.get_channel(partner_channel)
                        if not channel == None:
                            await ctx.send(
                                f'Your current lootbox alert channel is `{channel.name}` (ID `{channel.id}`).\n'
                                f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} channel set` within your new alert channel.\n'
                                f'To remove the alert channel entirely, use `{ctx.prefix}{ctx.invoked_with} channel reset`'
                            )
                            return
                        else:
                            await ctx.send(
                                f'You don\'t have a lootbox alert channel set.\n'
                                f'If you want to set one, use `{ctx.prefix}{ctx.invoked_with} channel set`'
                            )
                            return
                elif arg1 == 'alerts':
                    pass # I'm pissed, so I'll do this another day
                elif arg1 == 'reset':
                    await ctx.send(f'**{ctx.author.name}**, this will reset both your partner **and** your partner\'s partner (which is you, heh). Do you accept? `[yes/no]`')
                    answer = await bot.wait_for('message', check=check, timeout=30)
                    if answer.content.lower() in ['yes','y']:
                        status = await reset_partner(ctx)
                        
                        if status == 'updated':
                            await ctx.send(f'Your partner settings were reset.\n')
                            return
                        else:
                            await ctx.send(status)
                            return
                else:
                    if len(ctx.message.mentions) == 1:
                        settings = await get_settings(ctx, 'partner')
                        partner_id = settings[1]
                        if not partner_id == None:
                            await ctx.send(
                                f'**{ctx.author.name}**, you already have a partner.\n'
                                f'Use `{ctx.prefix}{ctx.invoked_with} reset` to remove your old one first.'
                            )
                            return
                        
                        new_partner = ctx.message.mentions[0]
                        new_partner_id = new_partner.id
                        new_partner_name = f'{new_partner.name}#{new_partner.discriminator}'
                        await ctx.send(f'{new_partner.mention}, **{ctx.author.name}** wants to set you as his partner. Do you accept? `[yes/no]`')
                        answer = await bot.wait_for('message', check=partner_check, timeout=30)
                        if answer.content.lower() in ['yes','y']:
                            status = await set_partner(ctx, new_partner_id, True)
                            if status in ('updated'):
                                await ctx.send(
                                    f'**{ctx.author.name}**, {new_partner.name} is now set as your partner.\n'
                                    f'**{new_partner.name}**, {ctx.author.name} is now set as your partner.\n'
                                    f'You may now kiss the brides.'
                                )
                                return
                            else:
                                await ctx.send(status)
                                return
                        else:
                            await ctx.send(f'Aborted.')
                            return
                    else:
                        await ctx.send(
                            f'Invalid parameter.\n'
                            f'If you want to set a partner, ping them (`{ctx.prefix}{ctx.invoked_with} [@User]`)'
                        )
                        return
        else:
            await bot.wait_until_ready()
            partner = bot.get_user(partner_id)
            if not partner == None:
                partner_name = f'{partner.name}#{partner.discriminator}'
                await ctx.send(
                    f'Your current partner is **{partner_name}**.\n'
                    f'If you want to change this, use this command to ping your new partner (`{ctx.prefix}{ctx.invoked_with} [@User]`)\n'
                    f'To remove your partner entirely, use `{ctx.prefix}{ctx.invoked_with} reset`.'
                )
                return
            else:
                await ctx.send(
                    f'You don\'t have a partner set.\n'
                    f'If you want to set a partner, use this command to ping her or him (`{ctx.prefix}{ctx.invoked_with} [@User]`)'
                )
                return

# Command "guild" - Guild settings & detection
@bot.command()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def guild(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            try:
                message_description = str(m.embeds[0].description)
                message_title = str(m.embeds[0].title)
                message_footer = str(m.embeds[0].footer)
                try:
                    message_fields = str(m.embeds[0].fields)
                    message_author = str(m.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                except:
                    message_fields = ''
                message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'
                logger.debug(f'Guild detection: {message}')
            except:
                message = str(m.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            
            if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1) or (message.find('Guild succesfully upgraded!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        if args:
            guild_data = await get_guild(ctx, 'leader')
            
            if guild_data == None:
                await ctx.send(
                    f'**{ctx.author.name}**, you are not registered as a guild leader. Only guild leaders can run guild commands.\n'
                    f'If you are a guild leader, run `rpg guild list` first to add or update your guild in my database.'
                )
                return
            else:    
                guild_name = guild_data[0]
                guild_stealth = guild_data[2]
                guild_channel = guild_data[4]
            
            arg1 = args[0]
            arg1 = arg1.lower()
            if arg1 == 'channel':
                if len(args) == 2:
                    arg2 = args[1] 
                    if arg2 == 'set':             
                        await ctx.send(f'**{ctx.author.name}**, set `{ctx.channel.name}` as the alert channel for the guild **{guild_name}**? `[yes/no]`')
                        answer = await bot.wait_for('message', check=check, timeout=30)
                        if answer.content.lower() in ['yes','y']:
                            status = await set_guild_channel(ctx, ctx.channel.id)
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
                            await ctx.send(f'Aborted.')
                            return
                    elif arg2 == 'reset':        
                        if guild_channel == None:
                            await ctx.send(f'The guild **{guild_name}** doesn\'t have an alert channel set, there is no need to reset it.')
                            return
                    
                        await bot.wait_until_ready()
                        channel = bot.get_channel(guild_channel)
                        if channel == None:
                            channel_name = 'Invalid channel'
                        else:
                            channel_name = channel.name
                            
                        await ctx.send(f'**{ctx.author.name}**, do you want to remove `{channel_name}` as the alert channel for the guild **{guild_name}**? `[yes/no]`')
                        answer = await bot.wait_for('message', check=check, timeout=30)
                        if answer.content.lower() in ['yes','y']:
                            status = await set_guild_channel(ctx, None)
                            if status == 'updated':
                                await ctx.send(f'**{ctx.author.name}**, the guild **{guild_name}** doesn\'t have an alert channel set anymore.')
                                return
                            else:
                                await ctx.send(status)
                                return
                        else:
                            await ctx.send(f'Aborted.')
                            return
                else:
                    await bot.wait_until_ready()
                    channel = bot.get_channel(guild_channel)
                    if not channel == None:
                        await ctx.send(
                            f'The current alert channel for the guild **{guild_name}** is `{channel.name}` (ID `{channel.id}`).\n'
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} channel set` within your new alert channel.\n'
                            f'To remove the alert channel entirely, use `{ctx.prefix}{ctx.invoked_with} channel reset`'
                        )
                        return
                    else:
                        await ctx.send(
                            f'The guild **{guild_name}** doesn\'t have an alert channel set.\n'
                            f'If you want to set one, use `{ctx.prefix}{ctx.invoked_with} channel set`'
                        )
                        return
            elif arg1 == 'stealth':
                if len(args) == 2:
                    arg2 = args[1] 
                    if arg2.isnumeric():
                        new_stealth = int(arg2)
                        if 1 <= new_stealth <= 100:
                            status = await set_guild_stealth_threshold(ctx, new_stealth)
                            if status == 'updated':
                                await ctx.send(f'**{ctx.author.name}**, stealth threshold for the guild **{guild_name}** is now **{new_stealth}**.')
                                return
                            else:
                                await ctx.send(status)
                                return
                        else:
                            await ctx.send(f'**{ctx.author.name}**, the stealth threshold needs to be between 1 and 100.')
                            return
                    else:
                        await ctx.send(f'**{ctx.author.name}**, the stealth threshold needs to be a number between 1 and 100.')
                        return
                else:
                    await ctx.send(
                        f'The current stealth threshold for the guild **{guild_name}** is **{guild_stealth}**.\n'
                        f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} stealth [1-100]`.'
                    )
            elif arg1 in ('on','off'):
                status = await set_guild_reminders(ctx, guild_name, arg1)
                await ctx.send(status)       
    # Guild command detection
    else:
        prefix = ctx.prefix
        
        if args:
            arg = args[0]
            if arg in ('raid', 'upgrade'):
                try:
                    guild_data = await get_guild(ctx, 'member')
                    
                    if not guild_data == None:
                        guild_name = guild_data[0]
                        guild_reminders_on = guild_data[1]
                        guild_stealth_threshold = guild_data[2]
                        guild_stealth_current = guild_data[3]
                        guild_channel_id = guild_data[4]
                        guild_message = guild_data[5]
                        
                        command = f'rpg guild {arg}'

                        if not guild_reminders_on == 0:
                            bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                            try:
                                message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                message_description = str(bot_answer.embeds[0].description)
                                message_footer = str(bot_answer.embeds[0].footer)
                                try:
                                    message_fields = str(bot_answer.embeds[0].fields)
                                    message_title = str(bot_answer.embeds[0].title)
                                except:
                                    message_fields = ''
                                bot_message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'
                            except:
                                bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                            # Check if stealth was upgraded
                            if bot_message.find('Guild succesfully upgraded!') > 1:
                                stealth_start = bot_message.find('--> **') + 6
                                stealth_end = bot_message.find('**', stealth_start)
                                stealth = bot_message[stealth_start:stealth_end]
                                guild_stealth_current = int(stealth)
                                status = await set_guild_stealth_current(ctx, guild_name, guild_stealth_current)
                            
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
                                time_left = await parse_timestring(ctx, timestring)
                                write_status = await write_guild_reminder(ctx, guild_name, guild_channel_id, time_left, guild_message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore anti spam embed
                            elif bot_message.find('Huh please don\'t spam') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore failed Epic Guard event
                            elif bot_message.find('is now in the jail!') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                await bot_answer.add_reaction(emojis.rip)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                        else:
                            return
                    else:
                        return
                
                    # Calculate cooldown
                    cooldown_data = await get_cooldown(ctx, 'guild')
                    cooldown = int(cooldown_data[0])
                    
                    write_status = await write_guild_reminder(ctx, guild_name, guild_channel_id, cooldown, guild_message)
                    
                    # Add reaction
                    if not write_status == 'aborted':
                        await bot_answer.add_reaction(emojis.navi)
                    else:
                        if DEBUG_MODE == 'ON':
                            await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                except asyncio.TimeoutError as error:
                    if DEBUG_MODE == 'ON':
                        await ctx.send('Guild detection timeout.')
                    return   
        else:
            try:
                guild_data = await get_guild(ctx, 'member')
                
                if not guild_data == None:
                    guild_name = guild_data[0]
                    guild_reminders_on = guild_data[1]
                    guild_stealth_threshold = guild_data[2]
                    guild_stealth_current = guild_data[3]
                    guild_channel_id = guild_data[4]
                    guild_message = guild_data[5]
                    
                    bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = global_data.timeout)
                    try:
                        message_author = str(bot_answer.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message_description = str(bot_answer.embeds[0].description)
                        message_footer = str(bot_answer.embeds[0].footer)
                        try:
                            message_fields = str(bot_answer.embeds[0].fields)
                            message_title = str(bot_answer.embeds[0].title)
                        except:
                            message_fields = ''
                        bot_message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'
                    except:
                        bot_message = str(bot_answer.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')

                    # Check if correct embed
                    if bot_message.find('Your guild was raided') > 1:
                        if not guild_reminders_on == 0:
                            # Upgrade stealth (no point in upgrading that without active reminders)
                            stealth_start = bot_message.find('**STEALTH**: ') + 13
                            stealth_end = bot_message.find('\\n', stealth_start)
                            stealth = bot_message[stealth_start:stealth_end]
                            guild_stealth_current = int(stealth)
                            status = await set_guild_stealth_current(ctx, guild_name, guild_stealth_current)
                            await bot_answer.add_reaction(emojis.navi)

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
                            time_left = await parse_timestring(ctx, timestring)
                            write_status = await write_guild_reminder(ctx, guild_name, guild_channel_id, time_left, guild_message, True)
                            if write_status in ('inserted','scheduled','updated'):
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                    # Ignore anti spam embed
                    elif bot_message.find('Huh please don\'t spam') > 1:
                        if DEBUG_MODE == 'ON':
                            await bot_answer.add_reaction(emojis.cross)
                        return
                    # Ignore failed Epic Guard event
                    elif bot_message.find('is now in the jail!') > 1:
                        if DEBUG_MODE == 'ON':
                            await bot_answer.add_reaction(emojis.cross)
                        await bot_answer.add_reaction(emojis.rip)
                        return
                    # Ignore error when another command is active
                    elif bot_message.find('end your previous command') > 1:
                        if DEBUG_MODE == 'ON':
                            await bot_answer.add_reaction(emojis.cross)
                        return
                    else:
                        return
                else:
                    return
            except asyncio.TimeoutError as error:
                if DEBUG_MODE == 'ON':
                    await ctx.send('Guild detection timeout.')
                return   
            
                         
# Command "enable/disable" - Enables/disables specific reminders
@bot.command(aliases=('disable',))
@commands.bot_has_permissions(send_messages=True)
async def enable(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
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
                    'alert': 'lootbox-alert',
                    'lootboxalert': 'lootbox-alert',
                    'lbalert': 'lootbox-alert',
                    'lb-alert': 'lootbox-alert'
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
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        active_reminders = await get_active_reminders(ctx)

        if active_reminders == 'None':
            reminders = f'{emojis.bp} You have no active reminders'
        else:
            reminders = ''
            for reminder in active_reminders:
                activity = reminder[0]
                end_time = reminder[1]
                if activity == 'pett':
                    activity = f'Pet tournament'
                elif activity.find('pet-') > -1:
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
  
# Update guild
@bot.event
async def on_message_edit(message_before, message_after):
    if message_before.author.id == 555955826880413696:
        if message_before.content.find('loading the EPIC guild member list...') > -1:
            message_guild_name = str(message_after.embeds[0].fields[0].name)
            message_guild_members = str(message_after.embeds[0].fields[0].value)
            message_guild_leader = str(message_after.embeds[0].footer.text)
            
            guild_name = message_guild_name.replace(' members','').replace('**','')
            guild_leader = message_guild_leader.replace('Owner: ','')
            guild_members = message_guild_members.replace('ID: ','').replace('**','')
            guild_members_list_raw = guild_members.split('\n')
            guild_members_list = []
            
            # Get members of current server
            message_guild = message_after.guild
            message_guild_members = message_guild.members
            
            # Get user id of the leader if necessary 
            if guild_leader.isnumeric():
                guild_leader = int(guild_leader)
            else:
                for guild_member in message_guild_members:
                    full_name = f'{guild_member.name}#{guild_member.discriminator}'
                    if full_name == guild_leader:
                        guild_leader = guild_member.id
                        break
            
            # Get all user ids of all guild members
            for member in guild_members_list_raw:
                if member.isnumeric():
                    guild_members_list.append(int(member))
                else:
                    for guild_member in message_guild_members:
                        full_name = f'{guild_member.name}#{guild_member.discriminator}'
                        if full_name == member:
                            guild_members_list.append(guild_member.id)
                            break
            
            if len(guild_members_list) < 10:
                missing_members = 10 - len(guild_members_list)
                for x in range(0, missing_members):
                    guild_members_list.append(None)
            
            await update_guild(guild_name, guild_leader, guild_members_list)
            await message_after.add_reaction(emojis.navi)


# --- Main menus ---
# Main menu
@bot.command(aliases=('h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def help(ctx):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        prefix = await get_prefix(ctx)
        
        reminder_management = (
            f'{emojis.bp} `{prefix}list` : List all your active reminders'
        )
                    
        user_settings = (
            f'{emojis.bp} `{prefix}on` / `off` : Turn the bot on or off\n'
            f'{emojis.bp} `{prefix}settings` : Check your settings\n'
            f'{emojis.bp} `{prefix}donator` : Set your EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}enable` / `disable` : Enable/disable specific reminders'
        )
        
        partner_settings = (
            f'{emojis.bp} `{prefix}partner` : Set your marriage partner\n'
            f'{emojis.bp} `{prefix}partner donator` : Set your partner\'s EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}partner channel` : Set the channel for incoming lootbox alerts'
        )
        
        guild_settings = (
            f'Note: Only the guild leader can use these commands.\n'
            f'{emojis.bp} `rpg guild list` : Add/update your guild\n'
            f'{emojis.bp} `{prefix}guild channel` : Set the channel for guild reminders\n'
            f'{emojis.bp} `{prefix}guild on` / `off` : Turn guild reminders on or off\n'
            f'{emojis.bp} `{prefix}guild stealth` : Set your stealth threshold'
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
        embed.add_field(name='PARTNER SETTINGS', value=partner_settings, inline=False)
        embed.add_field(name='GUILD SETTINGS', value=guild_settings, inline=False)
        embed.add_field(name='SERVER SETTINGS', value=server_settings, inline=False)
        
        await ctx.send(embed=embed)


# --- Command detection ---
# Hunt
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
                logger.debug(f'Hunt detection: {message}')
            
            if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1))) or ((message.find(f'\'s cooldown') > -1) and (message.find('You have already looked around') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you have to be married') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or (message.find(f'is in the middle of a command') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    invoked = ctx.invoked_with
    invoked = invoked.lower()
    
    if prefix.lower() == 'rpg ' and len(args) in (0,1,2):
        # Determine if hardmode and/or together was used
        together = False
        
        if len(args) > 0:
            if invoked == 'ascended':
                command = 'rpg ascended hunt'
                args = args[0]
                args.pop(0)
            else:
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
        else:
            command = 'rpg hunt'
            
        try:
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
                    partner_id = settings[5]
                    hunt_enabled = int(settings[6])
                    hunt_message = settings[7]
                    
                    # Set message to send          
                    if hunt_message == None:
                        hunt_message = default_message.replace('%',command)
                    else:
                        hunt_message = hunt_message.replace('%',command)
                    
                    if not hunt_enabled == 0:
                        # Check if it found a cooldown embed, if yes if it is the correct one, if not, ignore it and try to wait for the bot message one more time
                        if bot_message.find(f'\'s cooldown') > 1:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if (bot_message.find(f'{ctx_author}\'s cooldown') > -1) or (bot_message.find(f'{partner_name}\'s cooldown') > -1):    
                                timestring_start = bot_message.find('wait at least **') + 16
                                timestring_end = bot_message.find('**...', timestring_start)
                                timestring = bot_message[timestring_start:timestring_end]
                                timestring = timestring.lower()
                                time_left = await parse_timestring(ctx, timestring)
                                write_status = await write_reminder(ctx, 'hunt', time_left, hunt_message)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if DEBUG_MODE == 'ON':
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
                                if DEBUG_MODE == 'ON':
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
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore ascended error
                        elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when using "hunt t" while not married
                        elif bot_message.find('you have to be married') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Read partner name from hunt together message and save it to database if necessary (to make the bot check safer)
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        if together == True:
                            partner_name_start = bot_message.find(f'{ctx_author} and ') + len(ctx_author) + 12
                            partner_name_end = bot_message.find('are hunting together!', partner_name_start) - 3
                            partner_name = str(bot_message[partner_name_start:partner_name_end]).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if not partner_name == '':
                                await set_hunt_partner(ctx, partner_name)
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            # Check for lootboxes and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
            if not partner_id == None and together == True:
                await bot.wait_until_ready()
                partner = bot.get_user(partner_id)
                partner_name = partner.name
                lootbox_alert = ''
                if bot_message.find(f'**{partner_name}** got a common lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'a {emojis.lbcommon} common lootbox')
                elif bot_message.find(f'**{partner_name}** got an uncommon lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'an {emojis.lbuncommon} uncommon lootbox')
                elif bot_message.find(f'**{partner_name}** got a rare lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'a {emojis.lbrare} rare lootbox')
                elif bot_message.find(f'**{partner_name}** got an EPIC lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'an {emojis.lbepic} EPIC lootbox')
                elif bot_message.find(f'**{partner_name}** got an EDGY lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'an {emojis.lbedgy} EDGY lootbox')
                elif bot_message.find(f'**{partner_name}** got an OMEGA lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'an {emojis.lobomega} OMEGA lootbox')
                elif bot_message.find(f'**{partner_name}** got a GODLY lootbox') > -1:
                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name, lootbox=f'a {emojis.lbgodly} GODLY lootbox')
                
                if not lootbox_alert == '':
                    channel_settings = await get_settings(ctx, 'alert_channel', partner_id)
                    partner_channel_id = channel_settings[0]
                    partner_reminders_on = channel_settings[1]
                    alert_enabled = channel_settings[2]
                    if not partner_channel_id == None and not alert_enabled == 0 and not partner_reminders_on == 0:
                        try:
                            await bot.wait_until_ready()
                            await bot.get_channel(partner_channel_id).send(f'{partner.mention} {lootbox_alert}')
                            await bot_answer.add_reaction(emojis.partner_alert)
                        except Exception as e:
                            await ctx.send(e)
            
            # Add an F if the user died
            if (bot_message.find(f'{ctx_author} lost') > -1) or (bot_message.find('but lost fighting') > -1):
                await bot_answer.add_reaction(emojis.rip)
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Hunt detection timeout.')
            return

# Work
@bot.command(aliases=('axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor','greenhouse','mine','pickaxe','drill','dynamite',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
                logger.debug(f'Work detection: {message}')
            
            if  ((message.find(f'{ctx_author}** got ') > -1) and ((message.find('wooden log') > -1) or (message.find('EPIC log') > -1) or (message.find('SUPER log') > -1)\
                or (message.find('**MEGA** log') > -1) or (message.find('**HYPER** log') > -1) or (message.find('IS THIS A **DREAM**?????') > -1)\
                or (message.find('normie fish') > -1) or (message.find('golden fish') > -1) or (message.find('EPIC fish') > -1) or (message.find('coins') > -1)\
                or (message.find('RUBY') > -1) or (message.find('apple') > 1) or (message.find('banana') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1)\
                and (message.find('You have already got some resources') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > 1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    invoked = ctx.invoked_with
    invoked = invoked.lower()
    
    if prefix.lower() == 'rpg ':
        if invoked == 'ascended':
            args = args[0]
            command = f'rpg ascended {args[0].lower()}'
        else:
            command = f'rpg {invoked.lower()}'
        
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore ascended error
                        elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                    await bot_answer.add_reaction(emojis.fire)
            else:
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                return
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Work detection timeout.')
            return

# Training
@bot.command(aliases=('tr','ultraining','ultr',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
                logger.debug(f'Training detection: {message}')
            
            if  (message.find(f'Well done, **{ctx_author}**') > -1) or (message.find(f'Better luck next time, **{ctx_author}**') > -1) \
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have trained already') > -1)) or ((message.find(ctx_author) > 1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1)) or (message.find('This command is unlocked in') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    invoked = ctx.invoked_with
    invoked = invoked.lower()
    
    if prefix.lower() == 'rpg ':
        
        if args:
            if invoked == 'ascended':
                args = args[0]
                arg_command = args[0]
                if arg_command in ('tr', 'training',):
                    command = 'rpg ascended training'
                elif arg_command in ('ultr', 'ultraining',):
                    command = 'rpg ascended ultraining'
                args.pop(0)   
        else:
            if invoked in ('tr', 'training',):
                command = 'rpg training'
            elif invoked in ('ultr', 'ultraining',):
                command = 'rpg ultraining'

            if len(args) >= 1 and command.find('ultraining') > -1:
                arg = args[0]
                if arg in ('p','progress',):
                    return
        
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore ascended error
                        elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Training detection timeout.')
            return     

# Adventure
@bot.command(aliases=('adv',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
                logger.debug(f'Adventure detection: {message}')
            
            if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1))) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already been in an adventure') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    invoked = ctx.invoked_with
    invoked = invoked.lower()
    
    if prefix.lower() == 'rpg ':
            
        if args:
            if invoked == 'ascended':
                command = 'rpg ascended adventure'
                args = args[0]
                args.pop(0)
            else:
                command = 'rpg adventure'
            
            if len(args) > 0:
                arg1 = args[0]
                arg1 = arg1.lower()
            
                if arg1 in ('h','hardmode',):
                    command = f'{command} hardmode'
        else:
            command = 'rpg adventure'
        
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore higher area error
                        elif bot_message.find('This command is unlocked in') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore ascended error
                        elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Adventure detection timeout.')
            return   

# Lootbox
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
                logger.debug(f'Lootbox detection: {message}')
            
            if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
            or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you have to be level') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ' and args:     
        command = f'rpg buy lootbox'
        arg1 = ''
        arg2 = ''
        arg1 = args[0]
        if len(args) >= 2:
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
                                    if DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error message that appears if you already own a lootbox
                            elif bot_message.find('You can\'t carry more than 1 lootbox at once!') > -1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error message that you are too low level to buy a lootbox
                            elif bot_message.find('you have to be level') > -1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore anti spam embed
                            elif bot_message.find('Huh please don\'t spam') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore failed Epic Guard event
                            elif bot_message.find('is now in the jail!') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                await bot_answer.add_reaction(emojis.rip)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if DEBUG_MODE == 'ON':
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
                    if DEBUG_MODE == 'ON':
                        await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
                
            except asyncio.TimeoutError as error:
                if DEBUG_MODE == 'ON':
                    await ctx.send('Lootbox detection timeout.')
                return   
        else:
            return
    else:
        return


# Quest
@bot.command(aliases = ('quest',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
            
            if DEBUG_MODE == 'ON':
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

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':     
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
                                if DEBUG_MODE == 'ON':
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore quest cancellation as it does not reset the cooldown
                        elif bot_message.find('epic quest cancelled') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when trying to do epic quest with active quest
                        elif bot_message.find(f'You cannot do this if you have a pending quest!') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore active quest
                        elif bot_message.find(f'If you don\'t want this quest anymore') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore completed quest
                        elif bot_message.find(f'Completed!') > -1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Quest detection timeout.')
            return   
    else:
        return
    
# Daily
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':
        
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Daily detection timeout.')
            return   
        
# Weekly
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':
        
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
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
                if DEBUG_MODE == 'ON':
                    await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')
            
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Weekly detection timeout.')
            return    
        
# Lottery
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':
        
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
                                if DEBUG_MODE == 'ON':
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
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore max bought lottery ticket info
                        elif bot_message.find('you cannot buy more') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Lottery detection timeout.')
            return    

# Big arena / Not so mini boss
@bot.command(aliases=('not',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    invoked = ctx.invoked_with
    invoked = invoked.lower()
    
    if prefix.lower() == 'rpg ':
        
        if args:
            if invoked == 'ascended':
                args = args[0]            

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
                                elif event == 'arena':
                                    write_status = await write_reminder(ctx, 'arena', time_left, arena_message, True)
                                if write_status in ('inserted','scheduled','updated'):
                                    await bot_answer.add_reaction(emojis.navi)
                                else:
                                    if DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore anti spam embed
                            elif bot_message.find('Huh please don\'t spam') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore failed Epic Guard event
                            elif bot_message.find('is now in the jail!') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                await bot_answer.add_reaction(emojis.rip)
                                return
                            # Ignore higher area error
                            elif bot_message.find('This command is unlocked in') > -1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore ascended error
                            elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                        else:
                            return
                    else:
                        return
                else:
                    return
                
            except asyncio.TimeoutError as error:
                if DEBUG_MODE == 'ON':
                    await ctx.send('Big arena / Not so mini boss detection timeout.')
                return    

# Pets
@bot.command(aliases=('pets',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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
                or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

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
                    pet_id = pet_id.upper()
                else:
                    pet_id = ''
                if (arg1 in ('adv', 'adventure',)) and pet_action in ('find', 'learn', 'drill',) and not pet_id == '':
                    command = f'rpg pet adventure'
                    try:
                        settings = await get_settings(ctx, 'pet')
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
                                    if bot_message.find('Your pet has started an adventure and will be back') > -1:
                                        timestring_start = bot_message.find('back in **') + 10
                                        timestring_end = bot_message.find('**!', timestring_start)
                                        timestring = bot_message[timestring_start:timestring_end]
                                        timestring = timestring.lower()
                                        time_left = await parse_timestring(ctx, timestring)
                                        write_status = await write_reminder(ctx, f'pet-{pet_id}', time_left, pet_message, True)
                                        if write_status in ('inserted','scheduled','updated'):
                                            await bot_answer.add_reaction(emojis.navi)
                                        else:
                                            if DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that max amount of pets is on adventures
                                    elif bot_message.find('you cannot send another pet') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that ID is wrong
                                    elif bot_message.find('what pet are you trying to select?') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that pet is already on adventure
                                    elif bot_message.find('this pet is already in an adventure') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore time traveler instant pet return
                                    elif bot_message.find('IT CAME BACK INSTANTLY!') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        await bot_answer.add_reaction(emojis.timetraveler)
                                        return
                                    # Ignore error that pets are not unlocked yet
                                    elif bot_message.find('unlocked after second') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore anti spam embed
                                    elif bot_message.find('Huh please don\'t spam') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore failed Epic Guard event
                                    elif bot_message.find('is now in the jail!') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        await bot_answer.add_reaction(emojis.rip)
                                        return
                                    # Ignore error when another command is active
                                    elif bot_message.find('end your previous command') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                else:
                                    return
                            else:
                                return
                        else:
                            return
                    except asyncio.TimeoutError as error:
                        if DEBUG_MODE == 'ON':
                            await ctx.send('Pet adventure detection timeout.')
                        return  
                elif arg1 in ('tournament'):
                    command = f'rpg pet tournament'
                    try:
                        settings = await get_settings(ctx, 'pet')
                        if not settings == None:
                            reminders_on = settings[0]
                            default_message = settings[1]
                            if not reminders_on == 0:
                                user_donor_tier = int(settings[2])
                                if user_donor_tier > 3:
                                    user_donor_tier = 3
                                pet_enabled = int(settings[3])
                                
                                # Set message to send         
                                if default_message == None:
                                    pet_message = global_data.default_message.replace('%',command)
                                else:
                                    pet_message = default_message.replace('%',command)
                                
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

                                    # Check if pet tournament started, if yes, read the time and update/insert the reminder
                                    if bot_message.find('pet successfully sent to the pet tournament!') > -1:
                                        timestring_start = bot_message.find('is in **') + 8
                                        timestring_end = bot_message.find('**,', timestring_start)
                                        timestring = bot_message[timestring_start:timestring_end]
                                        timestring = timestring.lower()
                                        time_left = await parse_timestring(ctx, timestring)
                                        time_left = time_left + 60 #The event is somethings not perfectly on point, so I added a minute
                                        write_status = await write_reminder(ctx, f'pett', time_left, pet_message, True)
                                        if write_status in ('inserted','scheduled','updated'):
                                            await bot_answer.add_reaction(emojis.navi)
                                        else:
                                            if DEBUG_MODE == 'ON':
                                                await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that pet tournament is already active
                                    elif bot_message.find('You cannot send another pet to the **pet tournament**!') > -1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that ID is wrong
                                    elif bot_message.find('what pet are you trying to select?') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore error that pets are not unlocked yet
                                    elif bot_message.find('unlocked after second') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore anti spam embed
                                    elif bot_message.find('Huh please don\'t spam') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                    # Ignore failed Epic Guard event
                                    elif bot_message.find('is now in the jail!') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        await bot_answer.add_reaction(emojis.rip)
                                        return
                                    # Ignore error when another command is active
                                    elif bot_message.find('end your previous command') > 1:
                                        if DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)
                                        return
                                else:
                                    return
                            else:
                                return
                        else:
                            return
                        
                    except asyncio.TimeoutError as error:
                        if DEBUG_MODE == 'ON':
                            await ctx.send('Pet tournament detection timeout.')
                        return    

# Cooldowns
@bot.command(aliases=('cd',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
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

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':
            
        try:
            settings = await get_settings(ctx, 'all')
            if not settings == None:
                reminders_on = settings[1]
                if not reminders_on == 0:
                    user_donor_tier = int(settings[2])
                    if user_donor_tier > 3:
                        user_donor_tier = 3
                    default_message = settings[3]
                    adv_enabled = settings[9]
                    daily_enabled = settings[12]
                    lb_enabled = settings[14]
                    quest_enabled = settings[18]
                    tr_enabled = settings[19]
                    weekly_enabled = settings[20]
                    adv_message = settings[22]
                    daily_message = settings[25]
                    lb_message = settings[27]
                    quest_message = settings[31]
                    tr_message = settings[32]
                    weekly_message = settings[33]
                    
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
                            
                            write_status_list = []
                            
                            for cooldown in cooldowns:
                                activity = cooldown[0]
                                timestring = cooldown[1]
                                message = cooldown[2]
                                time_left = await parse_timestring(ctx, timestring)
                                if time_left > 1:
                                    write_status = await write_reminder(ctx, activity, time_left, message, True)
                                    if write_status in ('inserted','scheduled','updated'):
                                        write_status_list.append('OK')
                                    else:
                                        write_status_list.append('Fail')
                                else:
                                    write_status_list.append('OK')
                                
                            if not 'Fail' in write_status_list:                       
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if DEBUG_MODE == 'ON':
                                    await ctx.send(f'Something went wrong here. {write_status_list} {cooldowns}')
                                    await bot_answer.add_reaction(emojis.error)
                            return
                    
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Cooldown detection timeout.')
            return
    else:
        x = await list_cmd(ctx)
        return

# Events
@bot.command(aliases=('events',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
async def event(ctx, *args):
    
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
            
            if  ((message.find(f'Normal events') > -1) and (message.find(f'Guild ranking') > -1)) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ':
            
        try:
            settings = await get_settings(ctx, 'events')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 0:
                    default_message = settings[1]
                    arena_enabled = settings[2]
                    lottery_enabled = settings[4]
                    miniboss_enabled = settings[6]
                    pet_enabled = settings[8]
                    arena_message = settings[3]
                    lottery_message = settings[5]
                    miniboss_message = settings[7]
                    pet_message = settings[9]
                    
                    if not ((arena_enabled == 0) and (lottery_enabled == 0) and (miniboss_enabled == 0) and (pet_enabled == 0)):
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

                        # Check if event list, if yes, extract all the timestrings
                        if bot_message.find('Normal events') > 1:
                            
                            cooldowns = []
                            
                            if arena_enabled == 1:
                                if bot_message.find('Big arena**: ') > -1:
                                    arena_start = bot_message.find('Big arena**: ') + 13
                                    arena_end = bot_message.find('s', arena_start) + 1
                                    arena = bot_message[arena_start:arena_end]
                                    arena = arena.lower()
                                    if arena_message == None:
                                        arena_message = global_data.arena_message
                                    cooldowns.append(['arena',arena,arena_message,])
                            if lottery_enabled == 1:
                                if bot_message.find('Lottery**: ') > -1:
                                    lottery_start = bot_message.find('Lottery**: ') + 11
                                    lottery_end = bot_message.find('s', lottery_start) + 1
                                    lottery = bot_message[lottery_start:lottery_end]
                                    lottery = lottery.lower()
                                    if lottery_message == None:
                                        lottery_message = default_message.replace('%','rpg buy lottery ticket')
                                    else:
                                        lottery_message = lottery_message.replace('%','rpg buy lottery ticket')
                                    cooldowns.append(['lottery',lottery,lottery_message,])
                            if miniboss_enabled == 1:
                                if bot_message.find('"mini" boss**: ') > -1:
                                    miniboss_start = bot_message.find('"mini" boss**: ') + 15
                                    miniboss_end = bot_message.find('s', miniboss_start) + 1
                                    miniboss = bot_message[miniboss_start:miniboss_end]
                                    miniboss = miniboss.lower()
                                    if miniboss_message == None:
                                        miniboss_message = global_data.miniboss_message
                                    cooldowns.append(['miniboss',miniboss,miniboss_message,])
                            if pet_enabled == 1:
                                if bot_message.find('tournament**: ') > -1:
                                    pet_start = bot_message.find('tournament**: ') + 14
                                    pet_end = bot_message.find('s', pet_start) + 1
                                    tournament = bot_message[pet_start:pet_end]
                                    tournament = tournament.lower()
                                    if default_message == None:
                                        pet_message = global_data.default_message.replace('%','rpg pet tournament')
                                    else:
                                        pet_message = default_message.replace('%','rpg pet tournament')
                                    cooldowns.append(['pett',tournament,pet_message,])
                            
                            write_status_list = []
                            
                            for cooldown in cooldowns:
                                activity = cooldown[0]
                                timestring = cooldown[1]
                                message = cooldown[2]
                                time_left = await parse_timestring(ctx, timestring)
                                if activity == 'pett':
                                    time_left = time_left + 60 #The event is somethings not perfectly on point, so I added a minute
                                if time_left > 1:
                                    if activity in ('arena','miniboss',):
                                        write_status = await write_reminder(ctx, activity, time_left, message, True, True)
                                    else:
                                        write_status = await write_reminder(ctx, activity, time_left, message, True)
                                    if write_status in ('inserted','scheduled','updated','ignored',):
                                        write_status_list.append('OK')
                                    else:
                                        write_status_list.append('Fail')
                                else:
                                    write_status_list.append('OK')
                                
                            if not 'Fail' in write_status_list:                       
                                await bot_answer.add_reaction(emojis.navi)
                            else:
                                if DEBUG_MODE == 'ON':
                                    await ctx.send(f'Something went wrong here. {write_status_list} {cooldowns}')
                                    await bot_answer.add_reaction(emojis.error)
                            return
                    
                        # Ignore anti spam embed
                        elif bot_message.find('Huh please don\'t spam') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                        # Ignore failed Epic Guard event
                        elif bot_message.find('is now in the jail!') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            await bot_answer.add_reaction(emojis.rip)
                            return
                        # Ignore error when another command is active
                        elif bot_message.find('end your previous command') > 1:
                            if DEBUG_MODE == 'ON':
                                await bot_answer.add_reaction(emojis.cross)
                            return
                    else:
                        return
                else:
                    return
            else:
                return
            
        except asyncio.TimeoutError as error:
            if DEBUG_MODE == 'ON':
                await ctx.send('Event detection timeout.')
            return
    else:
        x = await list_cmd(ctx)
        return



# Ascended commands
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
async def ascended(ctx, *args):

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ' and len(args) >= 1:
        
        arg1 = args[0]
        args = list(args)
        
        if arg1 == 'hunt':
            x = await hunt(ctx, args)
        elif arg1 in ('adventure','adv',):
            x = await adventure(ctx, args)
        elif arg1 in ('tr','training','ultr','ultraining'):
            x = await training(ctx, args)
        elif arg1 in ('chop','axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor','greenhouse','mine','pickaxe','drill','dynamite',):
            x = await chop(ctx, args)
        elif arg1 in ('big','not',):
            x = await big(ctx, args)

# --- Miscellaneous ---

# Statistics command
@bot.command(aliases=('statistic','statistics,','devstat','ping','about','info','stats'))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def devstats(ctx):

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
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
  
# Hey! Listen!
@bot.command(aliases=('listen',))
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def hey(ctx):
    
    if not ctx.prefix == 'rpg ':
        await ctx.send('https://tenor.com/view/navi-hey-listen-gif-4837431')
    



# --- Owner Commands ---

# Shutdown command (only I can use it obviously)
@bot.command()
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True)
async def shutdown(ctx):

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':    
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