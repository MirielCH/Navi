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

from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime
from discord.ext.commands import CommandNotFound
from math import ceil

# Check if log file exists, if not, create empty one
logfile = global_data.logfile
if not os.path.isfile(logfile):
    open(logfile, 'a').close()

# Initialize logger
logger = logging.getLogger('discord')
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

         
# --- Database: Get Data ---

# Check database for stored prefix, if none is found, a record is inserted and the default prefix - is used, return all bot prefixes
async def get_prefix_all(ctx):
    
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
        sql = 'SELECT reminders_on, user_donor_tier, partner_donor_tier, hunt_enabled, hunt_message FROM settings_user where user_id=?'
    
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
        reminders_on = True
    elif action == 'off':
        reminders_on = False
    else:
        await log_error(ctx, f'Unknown action in routine toggle_reminders.')
        return
    
    try:
        cur=erg_db.cursor()
        cur.execute('SELECT reminders_on FROM settings_user where user_id=?', (ctx.author.id,))
        record = cur.fetchone()
        
        if record:
            reminders_status = record[1]
            if reminders_status == 'True' and reminders_on == True:
                status = f'**{ctx.author.name}**, your reminders are already turned on.'
                return
            elif reminders_status == 'False' and reminders_on == False:
                status = f'**{ctx.author.name}**, your reminders are already turned off.'
                return
            else:
                cur.execute('UPDATE settings_user SET reminders_on = ? where user_id = ?', (reminders_on, ctx.author.id,))
                status = f'**{ctx.author.name}**, your reminders are now turned {action}.'
        else:
            if reminders_on == False:
                status = f'**{ctx.author.name}**, your reminders are already turned off.'
                return
            else:
                cur.execute('INSERT INTO settings_user VALUES (?, ?, ?, ?)', (ctx.author.id, reminders_on, 0, 0,))
                status = f'**{ctx.author.name}**, your reminders are now turned {action}.'
    except sqlite3.Error as error:
        await log_error(ctx, error)
    
    return status


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



# --- Command Initialization ---

bot = commands.Bot(command_prefix=get_prefix_all, help_command=None, case_insensitive=True)


# --- Ready & Join Events ---

# Set bot status when ready
@bot.event
async def on_ready():
    
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Epic RPG'))
    
# Send message to system channel when joining a server
@bot.event
async def on_guild_join(guild):
    
    try:
        prefix = await get_prefix(bot, guild, True)
        
        welcome_message =   f'Hello! **{guild.name}**! Hey! I\'m here to remind you to do your Epic RPG commands!\n\n'\
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
    elif isinstance(error, FirstTimeUser):
        return
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
                await ctx.send(f'Prefix changed to `{await get_prefix(bot, ctx)}`.')
        else:
            await ctx.send(f'The command syntax is `{ctx.prefix}setprefix [prefix]`.')

# Command "prefix" - Returns current prefix
@bot.command()
@commands.bot_has_permissions(send_messages=True)
async def prefix(ctx):
    
    if not ctx.prefix == 'rpg ':
        current_prefix = await get_prefix(bot, ctx)
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
        

# --- Task Scheduler ---
async def background_task(user, channel, message, time_left):
        
    await asyncio.sleep(time_left)
    await bot.get_channel(channel).send(f'{user.mention} {message}')

# --- Hunt commands ---
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True)
async def hunt(ctx, *args):
    
    def epic_rpg_check(m):
        correct_message = False
        try:
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            m = str(m).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            if (m.find(ctx_author) > 1) and ((m.find('found and killed') > 1) or (m.find(f'are hunting together!') > 1)):
                correct_message = True
            else:
                correct_message = False
        except:
            correct_message = False
        
        return m.author.id == 555955826880413696 and m.channel == ctx.channel and correct_message

    
    if ctx.prefix == 'rpg ' and len(args) in (0,1,2):
        hardmode = False
        together = False
        command = 'rpg hunt'
        if len(args) > 0:
            arg1 = args[0]
            arg1 = arg1.lower()
            if arg1 in ('t', 'together'):
                together = True
                command = 'rpg hunt t'
            elif arg1 in ('h', 'hardmode'):
                hardmode = True
                command = 'rpg hunt h'
                if len(args) > 1:
                    arg2 = args[1]
                    arg2 = arg2.lower()
                    if arg2 in ('t', 'together'):
                        together = True
                        command = 'rpg hunt h t'
        try:
            bot_answer = await bot.wait_for('message', check=epic_rpg_check, timeout = 5)
            bot_answer = str(bot_answer)
        
            settings = await get_settings(ctx, 'hunt')
            if not settings == None:
                reminders_on = settings[0]
                if not reminders_on == 'False' and not hunt_enabled == 'False':
                    user_donor_tier = int(settings[1])
                    partner_donor_tier = int(settings[2])
                    hunt_enabled = settings[3]
                    hunt_message = settings[4]
                    if hunt_message == '':
                        hunt_message = global_data.default_message.replace('%',f'`{command}`')
                    cooldown_data = await get_cooldown(ctx, 'hunt')
                    cooldown = int(cooldown_data[0])
                    donor_affected = cooldown_data[1]
                    if together == True and donor_affected == True:
                        time_left = cooldown*global_data.donor_cooldowns[partner_donor_tier]
                    elif together == False and donor_affected == True:
                        time_left = cooldown*global_data.donor_cooldowns[user_donor_tier]
                    else:
                        time_left = cooldown
                                        
                    bot.loop.create_task(background_task(ctx.author, ctx.channel, hunt_message, time_left))
                    
                else:
                    return
            else:
                return
        except asyncio.TimeoutError as error:
            return

# --- Main menus ---

# Main menu
@bot.command(aliases=('g','h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def help(ctx):
    
    if not ctx.prefix == 'rpg ':
        prefix = await get_prefix(bot, ctx)
                    
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