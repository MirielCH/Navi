# global_data.py

import os, sys, inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
import database
import logging
import logging.handlers
import global_data
import asyncio

from datetime import datetime, timedelta

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
            await database.log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{days}\' to an integer')
        
    if timestring.find('h') > -1:
        hours_start = 0
        hours_end = timestring.find('h')
        hours = timestring[hours_start:hours_end]
        timestring = timestring[hours_end+1:].strip()
        try:
            time_left = time_left + (int(hours) * 3600)
        except:
            await database.log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{hours}\' to an integer')
        
    if timestring.find('m') > -1:
        minutes_start = 0
        minutes_end = timestring.find('m')
        minutes = timestring[minutes_start:minutes_end]
        timestring = timestring[minutes_end+1:].strip()
        try:
            time_left = time_left + (int(minutes) * 60)
        except:
            await database.log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{minutes}\' to an integer')
        
    if timestring.find('s') > -1:
        seconds_start = 0
        seconds_end = timestring.find('s')
        seconds = timestring[seconds_start:seconds_end]
        timestring = timestring[seconds_end+1:].strip()
        try:
            time_left = time_left + int(seconds)
        except:
            await database.log_error(ctx, f'Error parsing timestring \'{timestring}\', couldn\'t convert \'{seconds}\' to an integer')
    
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



# --- Tasks ---
# Background task for scheduling reminders
async def background_task(bot, user, channel, message, time_left, task_name, guild=False):
    
    await asyncio.sleep(time_left)
    try:
        if guild == False:
            setting_dnd = await database.get_dnd(user.id)
            
            await bot.wait_until_ready()
            if setting_dnd == 0:
                await bot.get_channel(channel.id).send(f'{user.mention} {message}')
            else:
                await bot.get_channel(channel.id).send(f'**{user.name}**, {message}')
        else:
            guild_members = await database.get_guild_members(user)
            message_mentions = ''
            for member in guild_members:
                if not member == '':
                    await bot.wait_until_ready()
                    member_user = bot.get_user(member)
                    if not member_user == None:
                        message_mentions = f'{message_mentions}{member_user.mention} '
            await bot.wait_until_ready()
            await bot.get_channel(channel.id).send(f'{message}\n{message_mentions}')
        delete_task = global_data.running_tasks.pop(task_name, None)
        
    except Exception as e:
        global_data.logger.error(f'Error sending reminder: {e}')
        
    
    
# --- Reminder processing ---
# Write reminder
async def write_reminder(bot, ctx, activity, time_left, message, cooldown_update=False, no_insert=False):

    status = await database.write_reminder(ctx, activity, time_left, message, cooldown_update, no_insert)

    task_name = f'{ctx.author.id}-{activity}'
    if status == 'delete-schedule-task':
        if task_name in global_data.running_tasks:
            global_data.running_tasks[task_name].cancel()
            delete_task = global_data.running_tasks.pop(task_name, None)
        bot.loop.create_task(background_task(bot, ctx.author, ctx.channel, message, time_left, task_name))
        status = 'scheduled'
    elif status == 'schedule-task':
        task_name = f'{ctx.author.id}-{activity}'
        bot.loop.create_task(background_task(bot, ctx.author, ctx.channel, message, time_left, task_name))
        status = 'scheduled'
    
    return status

#  Write guild reminder
async def write_guild_reminder(bot, ctx, guild_name, guild_channel_id, time_left, message, cooldown_update=False):

    status = await database.write_guild_reminder(ctx, guild_name, guild_channel_id, time_left, message, cooldown_update)
    
    if status == 'delete-schedule-task':
        task_name = f'{guild_name}-guild'
        if task_name in global_data.running_tasks:
            global_data.running_tasks[task_name].cancel()
            delete_task = global_data.running_tasks.pop(task_name, None)
        bot.loop.create_task(background_task(bot, guild_name, guild_channel_id, message, time_left, task_name))
        status = 'scheduled'
    elif status == 'schedule-task':
        bot.loop.create_task(background_task(bot, guild_name, guild_channel_id, message, time_left, task_name))
        status = 'scheduled'
    
    return status

# Reduce all reminders of a user by a certain amount of time and delete reminders that would instantly finish
async def reduce_reminder_time(ctx, time_reduction):
    
    current_time = datetime.utcnow().replace(microsecond=0)
    all_status = []
    return_status = 'ok'
    
    reminders = await database.get_all_reminders(ctx)
    
    if not reminders == 'None':
        for reminder in reminders:
            reminder_activity = reminder[1]
            reminder_end_time = reminder[2]
            reminder_end_time_datetime = datetime.fromtimestamp(reminder_end_time)
            time_difference = reminder_end_time_datetime - current_time
            if not (reminder_activity.find('pet') > -1) and not (reminder_activity in ('vote','bigarena','nsmb','lottery','race',)):
                if time_difference.total_seconds() <= time_reduction:
                    delete_status = await database.delete_reminder(ctx, ctx.author.id, reminder_activity)
                    if not delete_status == 'deleted':
                        if delete_status == 'notfound':
                            global_data.logger.error(f'{datetime.now()}: Tried to delete this reminder, but could not find it: {reminder}')
                        else:
                            global_data.logger.error(f'{datetime.now()}: Had an error deleting this reminder: {reminder}')
                    task_name = f'{ctx.author.id}-{reminder_activity}'
                    delete_task = global_data.running_tasks.pop(task_name, None)
                    all_status.append('deleted')
                else:
                    reminder_end_time_datetime = reminder_end_time_datetime - timedelta(seconds=time_reduction)
                    time_left = reminder_end_time_datetime - current_time
                    time_left = time_left.total_seconds()
                    status = await database.update_reminder_time(ctx, reminder_activity, time_left)
                    all_status.append(status)
            else:
                all_status.append('ignored')
    
    for status in all_status:
        if not status in ('ignored','updated','deleted'):
            return_status = status
            
    return return_status


# --- Message processing ---

# Encode message (async)
async def encode_message(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title)
        try:
            message_fields = str(bot_message.embeds[0].fields)
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message

# Encode message (guild, async)
async def encode_message_guild(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_footer = str(bot_message.embeds[0].footer).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        try:
            message_fields = str(bot_message.embeds[0].fields)
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message

# Encode message (async, encoded fields)
async def encode_message_with_fields(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title)
        try:
            message_fields = str(bot_message.embeds[0].fields).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message

# Encode message (non async)
def encode_message_non_async(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title)
        try:
            message_fields = str(bot_message.embeds[0].fields)
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message

# Encode message (guild, non async)
def encode_message_guild_non_async(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_footer = str(bot_message.embeds[0].footer).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        try:
            message_fields = str(bot_message.embeds[0].fields)
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}{message_footer}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message

# Encode message (non async, encoded fields)
def encode_message_with_fields_non_async(bot_message):
    try:
        message_author = str(bot_message.embeds[0].author).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_description = str(bot_message.embeds[0].description).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        message_title = str(bot_message.embeds[0].title)
        try:
            message_fields = str(bot_message.embeds[0].fields).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
        except:
            message_fields = ''
        message = f'{message_author}{message_description}{message_fields}{message_title}'
    except:
        message = str(bot_message.content).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
    
    return message