# database.py

import sqlite3
import itertools
import global_data

from discord.ext import commands
from datetime import datetime, timedelta
from math import ceil

# Set name of database files
dbfile = global_data.dbfile

# Open connection to the local database    
navi_db = sqlite3.connect(dbfile, isolation_level=None)

# Mixed Case prefix
async def mixedCase(*args):
  mixed_prefixes = []
  for string in args:
    all_prefixes = map(''.join, itertools.product(*((c.upper(), c.lower()) for c in string)))
    for prefix in list(all_prefixes):
        mixed_prefixes.append(prefix)

  return list(mixed_prefixes)


# --- Database: Get Data ---

# Check database for stored prefix, if none is found, a record is inserted and the default prefix - is used, return all bot prefixes
async def get_prefix_all(bot, ctx):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT prefix FROM settings_guild where guild_id=?', (ctx.guild.id,))
        record = cur.fetchone()
        
        if record:
            prefix_db = record[0].replace('"','')
            prefix_db_mixed_case = await mixedCase(prefix_db)
            prefixes = ['rpg ','Rpg ','rPg ','rpG ','RPg ','rPG ','RpG ','RPG ']
            for prefix in prefix_db_mixed_case:
                prefixes.append(prefix)
        else:
            prefix_mixed_case = await mixedCase(global_data.default_prefix)
            prefixes = ['rpg ','Rpg ','rPg ','rpG ','RPg ','rPG ','RpG ','RPG ']
            for prefix in prefix_mixed_case:
                prefixes.append(prefix)
            
            cur.execute('INSERT INTO settings_guild VALUES (?, ?)', (ctx.guild.id, global_data.default_prefix,))
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
        cur=navi_db.cursor()
        cur.execute('SELECT prefix FROM settings_guild where guild_id=?', (guild.id,))
        record = cur.fetchone()
        
        if record:
            prefix = record[0]
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
        cur=navi_db.cursor()
        cur.execute('SELECT COUNT(*) FROM settings_user')
        record = cur.fetchone()
        
        if record:
            user_number = record
        else:
            await log_error(ctx, 'No user data found in database.')
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return user_number
   
# Get dnd state from user id
async def get_dnd(user_id):

    try:
        cur=navi_db.cursor()
        cur.execute('SELECT dnd FROM settings_user where user_id=?', (user_id,))
        record = cur.fetchone()

        if record:
            setting_dnd = record[0]
    
    except sqlite3.Error as error:
        global_data.logger.error(f'Unable to get dnd mode setting: {error}')
  
    return setting_dnd

# Get ruby count
async def get_rubies(ctx):

    try:
        cur=navi_db.cursor()
        cur.execute('SELECT rubies FROM settings_user where user_id=?', (ctx.author.id,))
        record = cur.fetchone()

        if record:
            rubies = record[0]
    
    except sqlite3.Error as error:
        global_data.logger.error(f'Unable to get ruby count: {error}')
  
    return rubies
   
# Get settings
async def get_settings(ctx, setting='all', partner_id=None):
    
    current_settings = None
    
    if setting == 'all':
        sql = 'SELECT * FROM settings_user s1 INNER JOIN settings_user s2 ON s2.user_id = s1.partner_id where s1.user_id=?'
    elif setting == 'adventure':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, adv_enabled, adv_message FROM settings_user where user_id=?'
    elif setting == 'arena':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, arena_enabled, arena_message FROM settings_user where user_id=?'
    elif setting == 'daily':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, daily_enabled, daily_message FROM settings_user where user_id=?'
    elif setting == 'duel':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, duel_enabled, duel_message FROM settings_user where user_id=?'
    elif setting == 'dungmb':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, dungmb_enabled, dungmb_message FROM settings_user where user_id=?'
    elif setting == 'farm':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, farm_enabled, farm_message FROM settings_user where user_id=?'
    elif setting == 'horse':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, horse_enabled, horse_message, race_enabled FROM settings_user where user_id=?'
    elif setting == 'hunt':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, partner_name, partner_donor_tier, partner_id, hunt_enabled, hunt_message, dnd FROM settings_user where user_id=?'
    elif setting == 'lootbox':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, lb_enabled, lb_message FROM settings_user where user_id=?'
    elif setting == 'lottery':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, lottery_enabled, lottery_message FROM settings_user where user_id=?'
    elif setting == 'nsmb-bigarena':
        sql = 'SELECT reminders_on, user_donor_tier, bigarena_enabled, nsmb_enabled FROM settings_user where user_id=?'
    elif setting == 'race':
        sql = 'SELECT reminders_on, race_enabled FROM settings_user where user_id=?'
    elif setting == 'pet':
        sql = 'SELECT reminders_on, default_message, user_donor_tier, pet_enabled, pet_message FROM settings_user where user_id=?'
    elif setting == 'quest':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, quest_enabled, quest_message FROM settings_user where user_id=?'
    elif setting == 'training':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, tr_enabled, tr_message, rubies, ruby_counter FROM settings_user where user_id=?'
    elif setting == 'vote':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, vote_enabled, vote_message FROM settings_user where user_id=?'
    elif setting == 'weekly':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, weekly_enabled, weekly_message FROM settings_user where user_id=?'
    elif setting == 'work':
        sql = 'SELECT reminders_on, user_donor_tier, default_message, work_enabled, work_message, rubies, ruby_counter FROM settings_user where user_id=?'
    elif setting == 'donor':
        sql = 'SELECT user_donor_tier FROM settings_user where user_id=?'
    elif setting == 'partner':
        sql = 'SELECT partner_donor_tier, partner_id, partner_channel_id FROM settings_user where user_id=?'
    elif setting == 'partner_alert_hardmode':
        sql = 'SELECT partner_channel_id, reminders_on, alert_enabled, hardmode, dnd FROM settings_user where user_id=?'
    elif setting == 'events':
        sql = 'SELECT reminders_on, default_message, bigarena_enabled, lottery_enabled, lottery_message, nsmb_enabled, pet_enabled, pet_message, race_enabled FROM settings_user where user_id=?'
    elif setting == 'hardmode':
        sql = 'SELECT hardmode FROM settings_user where user_id=?'
    elif setting == 'dnd':
        sql = 'SELECT dnd FROM settings_user where user_id=?'
    elif setting == 'rubies':
        sql = 'SELECT rubies, ruby_counter, reminders_on FROM settings_user where user_id=?'
    
    try:
        cur=navi_db.cursor()
        if not setting == 'partner_alert_hardmode':
            cur.execute(sql, (ctx.author.id,))
        else:
            if not partner_id == 0:
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

# Get cooldown (event reduction already calculated because I would have to change a lot of code otherwise)
async def get_cooldown(ctx, activity):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT cooldown, donor_affected, event_reduction FROM cooldowns where activity=?', (activity,))
        record = cur.fetchone()
    
        if record:
            cooldown = record[0]
            donor_affected = record[1]
            event_reduction = record[2]
            cooldown = ceil(cooldown*((100-event_reduction)/100))
            cooldown_data = (int(cooldown),donor_affected,)
        else:
            await log_error(ctx, f'No cooldown data found for activity \'{activity}\'.')
    
    except sqlite3.Error as error:
        await log_error(ctx, error)    
  
    return cooldown_data

# Get all cooldowns
async def get_cooldowns(ctx):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT activity, cooldown, event_reduction FROM cooldowns ORDER BY activity ASC')
        record = cur.fetchall()
    
        if record:
            cooldown_data = record
        else:
            await log_error(ctx, f'No cooldown data found in get_cooldowns.')
    
    except sqlite3.Error as error:
        await log_error(ctx, error)    
  
    return cooldown_data

# Get guild
async def get_guild(ctx, type):
    
    try:
        cur=navi_db.cursor()
        
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
        cur=navi_db.cursor()
        cur.execute('SELECT member1_id, member2_id, member3_id, member4_id, member5_id, member6_id, member7_id, member8_id, member9_id, member10_id FROM guilds WHERE guild_name=?', (guild_name,))
        record = cur.fetchone()
    
        if record:
            guild_members = record
        else:
            guild_members = None
    
    except sqlite3.Error as error:
        global_data.logger.error(f'Unable to get guild members: {error}')
  
    return guild_members

# Get active reminders
async def get_active_reminders(ctx):
    
    current_time = datetime.utcnow().replace(microsecond=0)
    current_time = current_time.timestamp()
    
    active_reminders = []
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT activity, end_time, message FROM reminders WHERE user_id = ? AND end_time > ? ORDER BY end_time', (ctx.author.id,current_time,))
        record_reminders_user = cur.fetchall()
        guild_data = await get_guild(ctx,'member')
        if not guild_data == None:
            guild_name = guild_data[0]
            cur.execute('SELECT activity, end_time, message, user_id FROM reminders WHERE user_id = ? AND end_time > ?', (guild_name,current_time,))
            record_reminder_guild = cur.fetchone()
        
        if record_reminders_user:
            active_reminders = record_reminders_user
        if record_reminder_guild:
            active_reminders.append(record_reminder_guild)
        
    except sqlite3.Error as error:
        global_data.logger.error(f'Routine \'get_active_reminders\' had the following error: {error}')
    
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
        cur=navi_db.cursor()
        cur.execute('SELECT user_id, activity, end_time, channel_id, message, triggered FROM reminders WHERE triggered = ? AND end_time BETWEEN ? AND ?', (triggered, current_time, end_time,))
        record = cur.fetchall()
        
        if record:
            due_reminders = record
        else:
            due_reminders = 'None'
    except sqlite3.Error as error:
        global_data.logger.error(f'Routine \'get_due_reminders\' had the following error: {error}')
    
    return due_reminders

# Get all reminders of a user
async def get_all_reminders(ctx):
    
    reminders = 'None'
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT user_id, activity, end_time FROM reminders WHERE user_id = ?', (ctx.author.id,))
        record = cur.fetchall()
        
        if record:
            reminders = record
        else:
            reminders = 'None'
    except sqlite3.Error as error:
        global_data.logger.error(f'Routine \'get_all_reminders\' had the following error: {error}')
    
    return reminders

# Get old reminders
async def get_old_reminders():
    
    current_time = datetime.utcnow().replace(microsecond=0)
    delete_time = current_time - timedelta(seconds=20) # This ensures that no reminders get deleted that are triggered but not yet fired.
    delete_time = delete_time.timestamp()
    
    due_reminders = 'None'
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT user_id, activity, triggered FROM reminders WHERE end_time < ?', (delete_time,))
        record = cur.fetchall()
        
        if record:
            old_reminders = record
        else:
            old_reminders = 'None'
    except sqlite3.Error as error:
        global_data.logger.error(f'Routine \'get_old_reminders\' had the following error: {error}')
    
    return old_reminders

# Get guild leaderboard
async def get_guild_leaderboard(ctx):
    
    try:
        record_leaderboard_worst = None
        record_leaderboard_best = None
        cur=navi_db.cursor()
        cur.execute('SELECT guild_name FROM guilds where member1_id=? or member2_id=? or member3_id=? or member4_id=? or member5_id=? or member6_id=? or member7_id=? or member8_id=? or member9_id=? or member10_id=?', (ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,ctx.author.id,))
        record_guild_name = cur.fetchone()
        if record_guild_name:
            guild_name = record_guild_name[0]
            cur.execute('SELECT user_id, energy FROM guilds_leaderboard WHERE guild_name = ? AND energy >= 30 ORDER BY energy DESC LIMIT 5', (guild_name,))
            record_leaderboard_best = cur.fetchall()
            if len(record_leaderboard_best) == 0:
                record_leaderboard_best = None
            cur.execute('SELECT user_id, energy FROM guilds_leaderboard WHERE guild_name = ? AND energy < 30 ORDER BY energy LIMIT 5', (guild_name,))
            record_leaderboard_worst = cur.fetchall()
            if len(record_leaderboard_worst) == 0:
                record_leaderboard_worst = None
        else:
            guild_name = None

    except sqlite3.Error as error:
        global_data.logger.error(f'Routine \'get_guild_leaderboard\' had the following error: {error}')
    
    return (guild_name, record_leaderboard_best, record_leaderboard_worst)

# Get guild weekly report
async def get_guild_leaderboard_weekly_report(bot):
    
    try:
        guild_report_data = []
        energy_total = 0
        cur=navi_db.cursor()
        cur.execute('SELECT guild_name, guild_channel_id FROM guilds')
        record_guilds = cur.fetchall()
        if not len(record_guilds) == 0:
            for guild in record_guilds:
                try:
                    guild_name = guild[0]
                    guild_channel_id = guild[1]
                    energy_total = 0
                    cur.execute('SELECT text FROM guilds_leaderboard_praises ORDER BY RANDOM() LIMIT 1')
                    record_praise = cur.fetchone()
                    cur.execute('SELECT text FROM guilds_leaderboard_roasts ORDER BY RANDOM() LIMIT 1')
                    record_roast = cur.fetchone()
                    cur.execute('SELECT user_id, energy FROM guilds_leaderboard WHERE guild_name = ? ORDER BY energy DESC LIMIT 1', (guild_name,))
                    record_best_raid = cur.fetchone()
                    cur.execute('SELECT user_id, energy FROM guilds_leaderboard WHERE guild_name = ? ORDER BY energy LIMIT 1', (guild_name,))
                    record_worst_raid = cur.fetchone()
                    cur.execute('SELECT energy FROM guilds_leaderboard WHERE guild_name = ?', (guild_name,))
                    record_all_raids_energy = cur.fetchall()
                    if record_all_raids_energy:
                        for raid_energy in record_all_raids_energy:
                            energy_total = energy_total + raid_energy[0]
                    praise = record_praise[0]
                    roast = record_roast[0]
                    if record_worst_raid:
                        raid_worst_user_id = record_worst_raid[0]
                        raid_worst_energy = record_worst_raid[1]
                    else:
                        raid_worst_user_id = 0
                        raid_worst_energy = 0
                    if record_best_raid:
                        raid_best_user_id = record_best_raid[0]
                        raid_best_energy = record_best_raid[1]
                    else:
                        raid_best_user_id = 0
                        raid_best_energy = 0
                    guild_report_data.append((guild_name,guild_channel_id,energy_total,raid_worst_user_id,raid_worst_energy, roast, raid_best_user_id, raid_best_energy, praise))

                except sqlite3.Error as error:
                    global_data.logger.error(f'Error getting weekly guild report for guild {guild_name}: {error}')

    except sqlite3.Error as error:
        global_data.logger.error(f'Error getting guild data for guild report: {error}')
        
    return guild_report_data



# --- Database: Write Data ---

# Set new prefix
async def set_prefix(bot, ctx, new_prefix):

    try:
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
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
            cur=navi_db.cursor()
            cur.execute('SELECT partner_id, user_donor_tier FROM settings_user WHERE user_id=?', (ctx.author.id,))
            record = cur.fetchone()
            cur.execute('SELECT partner_id, user_donor_tier FROM settings_user WHERE user_id=?', (partner_id,))
            record_partner = cur.fetchone()
        else:
            cur=navi_db.cursor()
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
        cur=navi_db.cursor()
        cur.execute('SELECT partner_id FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()

        if record:
            partner_id = record[0]
            cur.execute('UPDATE settings_user SET partner_id = ?, partner_donor_tier = ? WHERE user_id = ?', (None, 0, ctx.author.id,))
            if not partner_id == 0:
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
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
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

# Set hardmode state
async def set_hardmode(bot, ctx, state):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT s1.partner_id, s1.hardmode, s2.partner_channel_id, s2.dnd FROM settings_user s1 INNER JOIN settings_user s2 ON s2.user_id = s1.partner_id where s1.user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        status = ''
        
        if record:
            partner_id_db = record[0]
            hardmode_state_db = record[1]
            partner_channel_id = record[2]
            partner_dnd = record[3]
            if not partner_id_db == 0:
                await bot.wait_until_ready()
                partner = bot.get_user(partner_id_db)
                if hardmode_state_db == 1 and state == 1:
                    status = f'**{ctx.author.name}**, hardmode mode is already turned **on**.'
                elif hardmode_state_db == 0 and state == 0:
                    status = f'**{ctx.author.name}**, hardmode mode is already turned **off**.'
                else:
                    cur.execute('UPDATE settings_user SET hardmode = ? WHERE user_id = ?', (state, ctx.author.id,))
                    if state == 1:
                        status = f'**{ctx.author.name}**, hardmode mode is now turned **on**.'
                        await bot.wait_until_ready()
                        if partner_dnd == 1:
                            await bot.get_channel(partner_channel_id).send(f'**{partner.name}**, **{ctx.author.name}** just started **hardmoding**.')
                        else:
                            await bot.get_channel(partner_channel_id).send(f'{partner.mention}, **{ctx.author.name}** just started **hardmoding**.')
                    elif state == 0:
                        status = f'**{ctx.author.name}**, hardmode mode is now turned **off**.'
                        await bot.wait_until_ready()
                        if partner_dnd == 1:
                            await bot.get_channel(partner_channel_id).send(f'**{partner.name}**, **{ctx.author.name}** stopped hardmoding. Feel free to take them hunting.')
                        else:
                            await bot.get_channel(partner_channel_id).send(f'{partner.mention}, **{ctx.author.name}** stopped hardmoding. Feel free to take them hunting.')
            else:
                status = f'**{ctx.author.name}**, you do not have a partner set. This setting only does something if you are married and added your partner to this bot.\nUse `{ctx.prefix}partner` to add your partner.'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set dnd state
async def set_dnd(ctx, state):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT dnd FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        status = ''
        
        if record:
            dnd_state_db = record[0]
            
            if dnd_state_db == 1 and state == 1:
                status = f'**{ctx.author.name}**, DND mode is already turned **on**.'
            elif dnd_state_db == 0 and state == 0:
                status = f'**{ctx.author.name}**, DND mode is already turned **off**.'
            else:
                cur.execute('UPDATE settings_user SET dnd = ? WHERE user_id = ?', (state, ctx.author.id,))
                if state == 1:
                    status = f'**{ctx.author.name}**, DND mode is now turned **on**. Reminders will not ping you.'
                elif state == 0:
                    status = f'**{ctx.author.name}**, DND mode is now turned **off**. Reminders will ping you again.'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Turn ruby counter on/off
async def set_ruby_counter(ctx, state):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT ruby_counter FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        status = ''
        
        if record:
            ruby_counter_db = record[0]
            
            if ruby_counter_db == 1 and state == 1:
                status = f'**{ctx.author.name}**, the ruby counter is already turned **on**.'
            elif ruby_counter_db == 0 and state == 0:
                status = f'**{ctx.author.name}**, the ruby counter is already turned **off**.'
            else:
                cur.execute('UPDATE settings_user SET ruby_counter = ? WHERE user_id = ?', (state, ctx.author.id,))
                if state == 1:
                    status = f'**{ctx.author.name}**, the ruby counter is now turned **on**.'
                elif state == 0:
                    status = f'**{ctx.author.name}**, the ruby counter is now turned **off**.'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set ruby count
async def set_rubies(ctx, rubies):
    
    try:
        cur=navi_db.cursor()
        status = ''
        cur.execute('UPDATE user_settings SET rubies = ? WHERE user_id = ?', (rubies, ctx.author.id,))
    except sqlite3.Error as error:
        await log_error(ctx, error)

# Set cooldown of activities
async def set_cooldown(ctx, activity, seconds):
    
    try:
        cur=navi_db.cursor()
        status = ''
        cur.execute('UPDATE cooldowns SET cooldown = ? WHERE activity = ?', (seconds, activity,))
        status = f'**{ctx.author.name}**, the cooldown for activity **{activity}** is now set to **{seconds}**'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status

# Set event reduction of activities
async def set_event_reduction(ctx, activity, reduction):
    
    try:
        cur=navi_db.cursor()
        status = ''
        if not activity == 'all':
            cur.execute('UPDATE cooldowns SET event_reduction = ? WHERE activity = ?', (reduction, activity,))
            status = f'**{ctx.author.name}**, the event reduction for activity **{activity}** is now set to **{reduction}%**.'
        else:
            cur.execute('UPDATE cooldowns SET event_reduction = ?', (reduction,))
            status = f'**{ctx.author.name}**, the event reduction for **all** activities is now set to **{reduction}%**.'
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
        if global_data.DEBUG_MODE == 'ON':
            status = 'Something went wrong here. Check the error log.'
        return
    
    column = ''
    
    activity_columns = {
        'all': 'hunt_enabled',
        'adventure': 'adv_enabled',
        'arena': 'arena_enabled',
        'bigarena': 'bigarena_enabled',
        'daily': 'daily_enabled',
        'duel': 'duel_enabled',
        'dungmb': 'dungmb_enabled',
        'farm': 'farm_enabled',
        'horse': 'horse_enabled',
        'hunt': 'hunt_enabled',
        'lootbox': 'lb_enabled',
        'lootbox-alert': 'alert_enabled',
        'lottery': 'lottery_enabled',
        'nsmb': 'nsmb_enabled',
        'pet': 'pet_enabled',
        'quest': 'quest_enabled',
        'race': 'race_enabled',
        'training': 'tr_enabled',
        'vote': 'vote_enabled',
        'weekly': 'weekly_enabled',
        'work': 'work_enabled',
    }
    
    if activity in activity_columns:
        column = activity_columns[activity]
    else:
        await log_error(ctx, f'Invalid activity {activity} in \'set_specific_reminder\'')
        if global_data.DEBUG_MODE == 'ON':
            status = f'Something went wrong here. Check the error log.'
        return
    
    if activity == 'nsmb':
        activity_name = 'not so mini boss'
    elif activity == 'bigarena':
        activity_name = 'big arena'
    elif activity == 'dungmb':
        activity_name = 'dungeon / miniboss'
    elif activity == 'race':
        activity_name = 'horse race'
    else:
        activity_name = activity
    
    try:
        cur=navi_db.cursor()
        
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
                                f'**{ctx.author.name}**, your {activity_name} reminder is now **{action}d**.\n'
                                f'All active {activity_name} reminders have been deleted.'
                            )
                        else:
                            status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are now **{action}d**.'
                    else:
                        if not activity == 'lootbox-alert':
                            status = f'**{ctx.author.name}**, your {activity_name} reminder is now **{action}d**.'
                        else:
                            status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are now **{action}d**.'
                else:
                    if not activity == 'lootbox-alert':
                        status = f'**{ctx.author.name}**, your {activity_name} reminder is already **{action}d**.'
                    else:
                        status = f'**{ctx.author.name}**, your partner\'s lootbox alerts are already **{action}d**.'
            else:
                cur.execute(f'UPDATE settings_user SET adv_enabled = ?, alert_enabled = ?, daily_enabled = ?, farm_enabled = ?, hunt_enabled = ?, lb_enabled = ?,\
                    lottery_enabled = ?, pet_enabled = ?, quest_enabled = ?, tr_enabled = ?, weekly_enabled = ?, work_enabled = ?, duel_enabled = ?,\
                    arena_enabled = ?, dungmb_enabled = ?, bigarena_enabled = ?, nsmb_enabled = ?, race_enabled = ?, vote_enabled = ?, horse_enabled = ?\
                    WHERE user_id = ?', (enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, enabled, ctx.author.id,))
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
        cur=navi_db.cursor()
        if activity == 'custom':
            cur.execute('SELECT activity FROM reminders WHERE user_id = ? AND activity LIKE ? ORDER BY activity DESC LIMIT 5', (ctx.author.id,'custom%',))
            record_highest_custom_reminder = cur.fetchone()
            if record_highest_custom_reminder:
                highest_custom_db = record_highest_custom_reminder[0].replace('custom','')
                highest_custom_db = int(highest_custom_db)
                activity = f'custom{highest_custom_db+1}'
            else:
                activity = 'custom1'
            
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (ctx.author.id, activity,))    
        
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (ctx.author.id, activity,))
        record = cur.fetchone()
        
        if record:
            db_time = float(record[0])
            db_time_datetime = datetime.fromtimestamp(db_time)
            db_triggered = int(record[1])
            time_difference = db_time_datetime - current_time
            if 0 <= time_difference.total_seconds() <= 15 and db_triggered == 1:
                status = 'delete-schedule-task'
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
                    status = 'schedule-task'
                else:
                    status = 'ignored'
                    
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return status

# Update end time of reminder
async def update_reminder_time(ctx, activity, time_left):
    
    current_time = datetime.utcnow().replace(microsecond=0)
    status = 'aborted'
    
    if not time_left == 0:
        end_time = current_time + timedelta(seconds=time_left)
        end_time = end_time.timestamp()
        triggered = 0
    else:
        return
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (ctx.author.id, activity,))
        record = cur.fetchone()
        
        if record:
            db_time = float(record[0])
            db_time_datetime = datetime.fromtimestamp(db_time)
            db_triggered = int(record[1])
            time_difference = db_time_datetime - current_time
            cur.execute('UPDATE reminders SET end_time = ? WHERE user_id = ? AND activity = ?', (end_time, ctx.author.id, activity,))
            status = 'updated'
        else:
            status = f'There was an error in update_reminder_time when updating the {activity }reminder for user {ctx.author.name} (time left: {time_left} seconds)'
                    
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
        cur=navi_db.cursor()
        cur.execute('SELECT end_time, triggered FROM reminders WHERE user_id=? AND activity=?', (guild_name, 'guild',))
        record = cur.fetchone()
        
        if record:
            db_time = float(record[0])
            db_time_datetime = datetime.fromtimestamp(db_time)
            db_triggered = int(record[1])
            time_difference = db_time_datetime - current_time
            if 0 <= time_difference.total_seconds() <= 15 and db_triggered == 1:
                status = 'delete-schedule-task'
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
                status = 'schedule-task'
                    
    except sqlite3.Error as error:
        await log_error(ctx, error)
        
    return status

# Set reminder triggered state
async def set_reminder_triggered(ctx, user_id, activity, triggered=1):
    
    try:
        cur=navi_db.cursor()
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
                global_data.logger.error(f'Routine \'set_reminder_triggered\' had the following error: {error}')
            else:
                await log_error(ctx, error)

# Delete reminder
async def delete_reminder(ctx, user_id, activity):
    
    status = 'error'
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT activity FROM reminders WHERE user_id = ? AND activity = ?', (user_id, activity,))
        record = cur.fetchone()
        if record:
            cur.execute('DELETE FROM reminders WHERE user_id = ? AND activity = ?', (user_id, activity,))
            status = 'deleted'
        else:
            status = 'notfound'
    except sqlite3.Error as error:
        if ctx == None:
            global_data.logger.error(f'Routine \'delete_reminder\' had the following error: {error}')
        else:
            await log_error(ctx, error)
    
    return status

# Update guild
async def update_guild(guild_name, guild_leader, guild_members):

    try:
        cur=navi_db.cursor()
        cur.execute('SELECT * FROM guilds where guild_name=?', (guild_name,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE guilds SET guild_leader = ?, member1_id = ?, member2_id = ?, member3_id = ?, member4_id = ?, member5_id = ?, member6_id = ?, member7_id = ?, member8_id = ?, member9_id = ?, member10_id = ? where guild_name = ?', (guild_leader, guild_members[0], guild_members[1], guild_members[2], guild_members[3], guild_members[4], guild_members[5], guild_members[6], guild_members[7], guild_members[8], guild_members[9], guild_name,))
        else:
            cur.execute('INSERT INTO guilds VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (guild_name, guild_leader, 0, guild_members[0], guild_members[1], guild_members[2], guild_members[3], guild_members[4], guild_members[5], guild_members[6], guild_members[7], guild_members[8], guild_members[9],global_data.guild_stealth,0,None,global_data.default_message,))
    except sqlite3.Error as error:
        global_data.logger.error(f'Error updating guild information. Guild name: {guild_name}, guild leader: {guild_leader}, guild members: {guild_members}')

# Set guild alert channel
async def set_guild_channel(ctx, guild_channel_id):
    
    try:
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
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

# Set rubies
async def set_rubies(ctx, rubies):
    
    try:
        cur=navi_db.cursor()
        cur.execute('SELECT rubies FROM settings_user WHERE user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            cur.execute('UPDATE settings_user SET rubies = ? WHERE user_id = ?', (rubies, ctx.author.id,))
            status = 'updated'
        else:
            status = f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.'
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
        cur=navi_db.cursor()
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
        cur=navi_db.cursor()
        cur.execute('DELETE FROM reminders WHERE activity = ?', ('guild',))
        cur.execute('DELETE FROM guilds_leaderboard')
        cur.execute('UPDATE guilds SET stealth_current = ?', (1,))
        cur.execute('SELECT guild_name, guild_channel_id, guild_message FROM guilds')
        records = cur.fetchall()
        if records:    
            guilds = records
        else:
            guilds = None
            
    except sqlite3.Error as error:
        global_data.logger.error('Error resetting guilds.')
        
    return guilds

# Write raid to leaderboard
async def write_raid_energy(ctx, guild_name, energy):
    
    datetime = ctx.message.created_at
    timestamp = datetime.timestamp()
    
    try:
        cur=navi_db.cursor()
        status = ''
        cur.execute('INSERT INTO guilds_leaderboard (guild_name, user_id, energy, timestamp) VALUES (?, ?, ?, ?)', (guild_name, ctx.author.id, energy, timestamp,))
    except sqlite3.Error as error:
        await log_error(ctx, error)

        

# --- Error Logging ---

# Error logging
async def log_error(ctx, error, guild_join=False):
    
    if guild_join == False:
        try:
            settings = ''
            try:
                user_settings = await get_settings(ctx)
                settings = f'User ID {user_settings[0]}'
            except:
                settings = 'N/A'
            cur=navi_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (ctx.message.created_at, ctx.message.content, str(error), settings))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))
    else:
        try:
            cur=navi_db.cursor()
            cur.execute('INSERT INTO errors VALUES (?, ?, ?, ?)', (datetime.now(), 'Error when joining a new guild', str(error), 'N/A'))
        except sqlite3.Error as db_error:
            print(print(f'Error inserting error (ha) into database.\n{db_error}'))