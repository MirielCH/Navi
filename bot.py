# bot.py
import os
import discord
import shutil
import asyncio
import global_data
import global_functions
import emojis
import database

from emoji import demojize
from emoji import emojize

from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from math import ceil

    
    

# --- Tasks ---

# Task to read all due reminders from the database and schedule them
@tasks.loop(seconds=10.0)
async def schedule_reminders(bot):
    
    due_reminders = await database.get_due_reminders()
    
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
                    task = bot.loop.create_task(global_functions.background_task(bot, user, channel, message, time_left, task_name))
                else:
                    task = bot.loop.create_task(global_functions.background_task(bot, user_id, channel, message, time_left, task_name, True))
                global_data.running_tasks[task_name] = task
                
                await database.set_reminder_triggered(None, user_id, activity)
            except Exception as e:
                global_data.logger.error(f'{datetime.now()}: Error scheduling reminder {reminder}: {e}')

# Task to delete old reminders
@tasks.loop(minutes=2.0)
async def delete_old_reminders(bot):
    
    old_reminders = await database.get_old_reminders()
    
    if old_reminders == 'None':
        return
    else:
        for reminder in old_reminders:    
            try:
                try:
                    user_id = int(reminder[0])
                except:
                    user_id = reminder[0]
                activity = reminder[1]
                triggered = int(reminder[2])
                await database.delete_reminder(None, user_id, activity)
                if global_data.DEBUG_MODE == 'ON':
                    if triggered == 1:
                        global_data.logger.info(f'{datetime.now()}: Deleted this old reminder {reminder}')
                    else:
                        global_data.logger.error(f'{datetime.now()}: Deleted this old reminder that was never triggered: {reminder}')
            except:
                global_data.logger.error(f'{datetime.now()}: Error deleting old reminder {reminder}')
            


# --- Command Initialization ---
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=database.get_prefix_all, help_command=None, case_insensitive=True, intents=intents)
cog_extensions = ['cogs.hunt',
                  'cogs.work',
                  'cogs.training',
                  'cogs.adventure',
                  'cogs.farm',
                  'cogs.buy',
                  'cogs.lottery',
                  'cogs.quest',
                  'cogs.daily',
                  'cogs.weekly',
                  'cogs.nsmb-bigarena',
                  'cogs.pets',
                  'cogs.duel',
                  'cogs.arena',
                  'cogs.dung-mb',
                  'cogs.horse',
                  'cogs.cooldowns',
                  'cogs.events',
                  'cogs.trade',
                  'cogs.open',
                  'cogs.inventory',
                  'cogs.sleepypotion',
                  'cogs.guild']
if __name__ == '__main__':
    for extension in cog_extensions:
        bot.load_extension(extension)



# --- Ready & Join Events ---
# Set bot status when ready
@bot.event
async def on_ready():
    
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='your commands'))
    schedule_reminders.start(bot)
    delete_old_reminders.start(bot)
    
# Send message to system channel when joining a server
@bot.event
async def on_guild_join(guild):
    
    try:
        prefix = await database.get_prefix(guild, True)
        
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
        await ctx.reply(f'Sorry **{ctx.author.name}**, you need the permission(s) {missing_perms} to use this command.', mention_author=False)
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
        await ctx.reply(f'You\'re missing some arguments.', mention_author=False)
    else:
        await database.log_error(ctx, error) # To the database you go
       


# --- Server Settings ---
   
# Command "setprefix" - Sets new prefix (if user has "manage server" permission)
@bot.command()
@commands.has_permissions(manage_guild=True)
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def setprefix(ctx, *new_prefix):
    
    if not ctx.prefix == 'rpg ':
        if new_prefix:
            if len(new_prefix)>1:
                await ctx.reply(
                    f'The command syntax is `{ctx.prefix}setprefix [prefix]`.\n'
                    f'If you want to include a space in your prefix, use \" (example: `{ctx.prefix}setprefix "navi "`)',
                    mention_author=False
                )
            else:
                await database.set_prefix(bot, ctx, new_prefix[0])
                await ctx.reply(f'Prefix changed to `{await database.get_prefix(ctx)}`.', mention_author=False)
        else:
            await ctx.reply(
                f'The command syntax is `{ctx.prefix}setprefix [prefix]`.\n'
                f'If you want to include a space in your prefix, use \" (example: `{ctx.prefix}setprefix "navi "`)',
                mention_author=False
            )

# Command "prefix" - Returns current prefix
@bot.command()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def prefix(ctx):
    
    if not ctx.prefix == 'rpg ':
        current_prefix = await database.get_prefix(ctx)
        await ctx.reply(f'The prefix for this server is `{current_prefix}`\nTo change the prefix use `{current_prefix}setprefix`.', mention_author=False)



# --- User Settings ---

# Command "settings" - Returns current user settings
@bot.command(aliases=('me',))
@commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
async def settings(ctx):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        settings = await database.get_settings(ctx, 'all')
        guild_data = await database.get_guild(ctx, 'member')
        
        if settings == None:
            await ctx.reply(f'**{ctx.author.name}**, you are not registered with this bot yet. Use `{ctx.prefix}on` to activate me first.', mention_author=False)
            return
        else:
            settings = list(settings)
            
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
            arena_enabled = settings[11]
            bigarena_enabled = settings[12]
            daily_enabled = settings[13]
            duel_enabled = settings[14]
            dungmb_enabled = settings[15]
            farm_enabled = settings[16]
            horse_enabled = settings[17]
            hunt_enabled = settings[18]
            lb_enabled = settings[19]
            lottery_enabled = settings[20]
            nsmb_enabled = settings[21]
            pet_enabled = settings[22]
            quest_enabled = settings[23]
            race_enabled = settings[24]
            tr_enabled = settings[25]
            vote_enabled = settings[26]
            weekly_enabled = settings[27]
            work_enabled = settings[28]
            adv_message = settings[29]
            alert_message = settings[30]
            arena_message = settings[31]
            daily_message = settings[32]
            duel_message = settings[33]
            dungmb_message = settings[34]
            farm_message = settings[35]
            horse_message = settings[36]
            hunt_message = settings[37]
            lb_message = settings[38]
            lottery_message = settings[39]
            pet_message = settings[40]
            quest_message = settings[41]
            tr_message = settings[42]
            vote_message = settings[43]
            weekly_message = settings[44]
            work_message = settings[45]
            hardmode = settings[46]
            dnd = settings[47]
            ruby_counter = settings[48]
            rubies = settings[49]
            
            if not partner_id == 0:
                hardmode_partner = settings[96]
            else:
                hardmode_partner = 'N/A'
        
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
            if not partner_id == 0:
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
                f'{emojis.bp} Reminders: `{reminders_on}`\n'
                f'{emojis.bp} Donator tier: `{user_donor_tier}` ({global_data.donor_tiers[user_donor_tier]})\n'
                f'{emojis.bp} DND mode: `{dnd}`\n'
                f'{emojis.bp} Hardmode mode: `{hardmode}`\n'
                f'{emojis.bp} Ruby counter: `{ruby_counter}`'
            )
            
            partner = (
                f'{emojis.bp} Name: `{partner_name}`\n'
                f'{emojis.bp} Hardmode mode: `{hardmode_partner}`\n'
                f'{emojis.bp} Donator tier: `{partner_donor_tier}` ({global_data.donor_tiers[partner_donor_tier]})\n'
                f'{emojis.bp} Lootbox alert channel: `{partner_channel_name}`'
            )
            
            guild = (
                f'{emojis.bp} Name: `{guild_name}`\n'
                f'{emojis.bp} Reminders: `{guild_reminders_on}`\n'
                f'{emojis.bp} Alert channel: `{guild_channel_name}`\n'
                f'{emojis.bp} Stealth threshold: `{guild_stealth}`'
            )
            
            enabled_reminders = (
                f'{emojis.bp} Adventure: `{adv_enabled}`\n'
                f'{emojis.bp} Arena: `{arena_enabled}`\n'
                f'{emojis.bp} Daily: `{daily_enabled}`\n'
                f'{emojis.bp} Duel: `{duel_enabled}`\n'
                f'{emojis.bp} Dungeon / Miniboss: `{dungmb_enabled}`\n'
                f'{emojis.bp} Farm: `{farm_enabled}`\n'
                f'{emojis.bp} Horse: `{horse_enabled}`\n'
                f'{emojis.bp} Hunt: `{hunt_enabled}`\n'
                f'{emojis.bp} Lootbox: `{lb_enabled}`\n'
                f'{emojis.bp} Lottery: `{lottery_enabled}`\n'
                f'{emojis.bp} Partner lootbox alert: `{alert_enabled}`\n'
                f'{emojis.bp} Pet: `{pet_enabled}`\n'
                f'{emojis.bp} Quest: `{quest_enabled}`\n'
                f'{emojis.bp} Training: `{tr_enabled}`\n'
                f'{emojis.bp} Vote: `{vote_enabled}`\n'
                f'{emojis.bp} Weekly: `{weekly_enabled}`\n'
                f'{emojis.bp} Work: `{work_enabled}`'
            )
            
            enabled_event_reminders = (
                f'{emojis.bp} Big arena: `{bigarena_enabled}`\n'
                f'{emojis.bp} Horse race: `{race_enabled}`\n'
                f'{emojis.bp} Not so mini boss: `{nsmb_enabled}`\n'
            )
            
            if reminders_on == 'Disabled':
                enabled_reminders = f'**These settings are ignored because your reminders are off.**\n{enabled_reminders}'
            
            reminder_messages = (
                f'{emojis.bp} Default message: `{default_message}`\n'
                f'{emojis.bp} Adventure: `{adv_message}`\n'
                f'{emojis.bp} Arena: `{arena_message}`\n'
                f'{emojis.bp} Daily: `{daily_message}`\n'
                f'{emojis.bp} Duel: `{duel_message}`\n'
                f'{emojis.bp} Dungeon / Miniboss: `{dungmb_message}`\n'
                f'{emojis.bp} Farm: `{farm_message}`\n'
                f'{emojis.bp} Horse: `{horse_message}`\n'
                f'{emojis.bp} Hunt: `{hunt_message}`\n'
                f'{emojis.bp} Lootbox: `{lb_message}`\n'
                f'{emojis.bp} Lottery: `{lottery_message}`\n'
                f'{emojis.bp} Pet: `{pet_message}`\n'
                f'{emojis.bp} Quest: `{quest_message}`\n'
                f'{emojis.bp} Training: `{tr_message}`\n'
                f'{emojis.bp} Vote: `{vote_message}`\n'
                f'{emojis.bp} Weekly: `{weekly_message}`\n'
                f'{emojis.bp} Work: `{work_message}`'
            )
        
            embed = discord.Embed(
                color = global_data.color,
                title = f'{user_name}\'S SETTINGS',
            )    
            embed.add_field(name='USER', value=general, inline=False)
            embed.add_field(name='PARTNER', value=partner, inline=False)
            embed.add_field(name='GUILD', value=guild, inline=False)
            embed.add_field(name='COOLDOWN REMINDERS', value=enabled_reminders, inline=False)
            embed.add_field(name='EVENT REMINDERS', value=enabled_event_reminders, inline=False)
            #embed.add_field(name='REMINDER MESSAGES', value=reminder_messages, inline=False)
        
            await ctx.reply(embed=embed, mention_author=False)

# Command "on" - Activates bot
@bot.command(aliases=('start',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def on(ctx, *args):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        status = await database.set_reminders(ctx, 'on')
        await ctx.reply(status, mention_author=False)
        
# Command "off" - Deactivates bot
@bot.command(aliases=('stop',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def off(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        await ctx.reply(f'**{ctx.author.name}**, turning off the bot will delete all of your active reminders. Are you sure? `[yes/no]`', mention_author=False)
        try:
            answer = await bot.wait_for('message', check=check, timeout=30)
            if answer.content.lower() in ['yes','y']:
                status = await database.set_reminders(ctx, 'off')
                await ctx.send(status)
            else:
                await ctx.send('Aborted.')
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        
# Command "donator" - Sets user donor tier
@bot.command(aliases=('donator',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
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
    
    settings = await database.get_settings(ctx, 'donor')
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
                            await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}', mention_author=False)
                            return
                        if 0 <= partner_donor_tier <= 7:
                            status = await database.set_donor_tier(ctx, partner_donor_tier, True)
                            await ctx.reply(status, mention_author=False)
                            return
                        else:
                            await ctx.reply(f'This is not a valid tier.\n\n{possible_tiers}', mention_author=False)
                            return
                    else:
                        await ctx.reply(
                            f'**{ctx.author.name}**, the EPIC RPG donator tier of your partner is **{partner_donor_tier}** ({global_data.donor_tiers[partner_donor_tier]}).\n'
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}',
                            mention_author=False
                        )
                else:
                    try:
                        donor_tier = int(arg1)
                    except:
                        await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}', mention_author=False)
                        return
                    if 0 <= donor_tier <= 7:
                        status = await database.set_donor_tier(ctx, donor_tier)
                        await ctx.reply(status, mention_author=False)
                        return
                    else:
                        await ctx.reply(f'This is not a valid tier.\n\n{possible_tiers}', mention_author=False)
                        return
            else:
                await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [tier]` or `{ctx.prefix}{ctx.invoked_with} partner [tier]`.\n\n{possible_tiers}', mention_author=False)
                return
                    
        else:
            await ctx.reply(
                f'**{ctx.author.name}**, your current EPIC RPG donator tier is **{user_donor_tier}** ({global_data.donor_tiers[user_donor_tier]}).\n'
                f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} [tier]`.\n\n{possible_tiers}',
                mention_author=False
            )

# Command "partner" - Sets marriage partner settings
@bot.command()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
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
    
    settings = await database.get_settings(ctx, 'partner')
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
                            await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} donator [tier]`', mention_author=False)
                            return
                        if 0 <= partner_donor_tier <= 7:
                            status = await database.set_donor_tier(ctx, partner_donor_tier, True)
                            await ctx.reply(status, mention_author=False)
                            return
                        else:
                            await ctx.reply(f'This is not a valid tier.\n\n{possible_tiers}', mention_author=False)
                            return
                    else:
                        await ctx.reply(
                            f'**{ctx.author.name}**, the EPIC RPG donator tier of your partner is **{partner_donor_tier}** ({global_data.donor_tiers[partner_donor_tier]}).\n'
                            f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} donator [tier]`.\n\n{possible_tiers}',
                            mention_author=False
                        )
                elif arg1 == 'channel':
                    if len(args) == 2:
                        arg2 = args[1]
                        if arg2 == 'set':
                            if not partner_id == 0:
                                await ctx.reply(f'**{ctx.author.name}**, set `{ctx.channel.name}` as your lootbox alert channel? `[yes/no]`', mention_author=False)
                                answer = await bot.wait_for('message', check=check, timeout=30)
                                if answer.content.lower() in ['yes','y']:
                                    status = await database.set_partner_channel(ctx, ctx.channel.id)
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
                                await ctx.reply(
                                    f'You don\'t have a partner set.\n'
                                    f'If you want to set a partner, use `{ctx.prefix}{ctx.invoked_with} [@User]`',
                                    mention_author=False
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
                                    
                                await ctx.reply(f'**{ctx.author.name}**, do you want to remove **{channel_name}** as your lootbox alert channel? `[yes/no]`', mention_author=False)
                                answer = await bot.wait_for('message', check=check, timeout=30)
                                if answer.content.lower() in ['yes','y']:
                                    status = await database.set_partner_channel(ctx, None)
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
                                await ctx.reply(f'You don\'t have a lootbox alert channel set, there is no need to reset it.', mention_author=False)
                                return
                    else:
                        await bot.wait_until_ready()
                        channel = bot.get_channel(partner_channel)
                        if not channel == None:
                            await ctx.reply(
                                f'Your current lootbox alert channel is `{channel.name}` (ID `{channel.id}`).\n'
                                f'If you want to change this, use `{ctx.prefix}{ctx.invoked_with} channel set` within your new alert channel.\n'
                                f'To remove the alert channel entirely, use `{ctx.prefix}{ctx.invoked_with} channel reset`',
                                mention_author=False
                            )
                            return
                        else:
                            await ctx.reply(
                                f'You don\'t have a lootbox alert channel set.\n'
                                f'If you want to set one, use `{ctx.prefix}{ctx.invoked_with} channel set`',
                                mention_author=False
                            )
                            return
                elif arg1 == 'alerts':
                    pass # I'm pissed, so I'll do this another day
                elif arg1 == 'reset':
                    await ctx.reply(f'**{ctx.author.name}**, this will reset both your partner **and** your partner\'s partner (which is you, heh). Do you accept? `[yes/no]`', mention_author=False)
                    answer = await bot.wait_for('message', check=check, timeout=30)
                    if answer.content.lower() in ['yes','y']:
                        status = await database.reset_partner(ctx)
                        
                        if status == 'updated':
                            await ctx.send(f'Your partner settings were reset.\n')
                            return
                        else:
                            await ctx.send(status)
                            return
                else:
                    if len(ctx.message.mentions) == 1:
                        settings = await database.get_settings(ctx, 'partner')
                        partner_id = settings[1]
                        if not partner_id == 0:
                            await ctx.reply(
                                f'**{ctx.author.name}**, you already have a partner.\n'
                                f'Use `{ctx.prefix}{ctx.invoked_with} reset` to remove your old one first.',
                                mention_author=False
                            )
                            return
                        
                        new_partner = ctx.message.mentions[0]
                        new_partner_id = new_partner.id
                        new_partner_name = f'{new_partner.name}#{new_partner.discriminator}'
                        await ctx.reply(f'{new_partner.mention}, **{ctx.author.name}** wants to set you as his partner. Do you accept? `[yes/no]`', mention_author=False)
                        answer = await bot.wait_for('message', check=partner_check, timeout=30)
                        if answer.content.lower() in ['yes','y']:
                            status = await database.set_partner(ctx, new_partner_id, True)
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
                        await ctx.reply(
                            f'Invalid parameter.\n'
                            f'If you want to set a partner, ping them (`{ctx.prefix}{ctx.invoked_with} [@User]`)',
                            mention_author=False
                        )
                        return
        else:
            await bot.wait_until_ready()
            partner = bot.get_user(partner_id)
            if not partner == None:
                partner_name = f'{partner.name}#{partner.discriminator}'
                await ctx.reply(
                    f'Your current partner is **{partner_name}**.\n'
                    f'If you want to change this, use this command to ping your new partner (`{ctx.prefix}{ctx.invoked_with} [@User]`)\n'
                    f'To remove your partner entirely, use `{ctx.prefix}{ctx.invoked_with} reset`.',
                    mention_author=False
                )
                return
            else:
                await ctx.reply(
                    f'You don\'t have a partner set.\n'
                    f'If you want to set a partner, use this command to ping her or him (`{ctx.prefix}{ctx.invoked_with} [@User]`)',
                    mention_author=False
                )
                return
                         
# Command "enable/disable" - Enables/disables specific reminders
@bot.command(aliases=('disable',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def enable(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        activity_list = 'Possible activities:'
        for index in range(len(global_data.activities)):    
            
            activity = global_data.activities[index]
            if activity == 'dungmb':
                activity = 'dungeon'
            elif activity == 'nsmb':
                activity = 'notsominiboss'
            elif activity == 'race':
                activity = 'horserace'
            
            activity_list = f'{activity_list}\n{emojis.bp} `{activity}`'
        
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
                    'lb-alert': 'lootbox-alert',
                    'notsominiboss': 'nsmb',
                    'notsomini': 'nsmb',
                    'big': 'bigarena',
                    'voting': 'vote',
                    'dungeon': 'dungmb',
                    'miniboss': 'dungmb',
                    'mb': 'dungmb',
                    'horserace': 'race',
                    'horseracing': 'race',
                    'horsebreed': 'horse',
                    'horsebreeding': 'horse',
                    'breed': 'horse',
                    'breeding': 'horse',
                    'racing': 'race',
                    'dueling': 'duel',
                    'duelling': 'duel',
                    'horserace': 'race'
                }

                activity = args[0]
                activity = activity.lower()
                
                action = ctx.invoked_with
                
                if activity == 'all' and action == 'disable':
                    await ctx.reply(f'**{ctx.author.name}**, turning off all reminders will delete all of your active reminders. Are you sure? `[yes/no]`', mention_author=False)
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
                    status = await database.set_specific_reminder(ctx, activity, action)
                    await ctx.reply(status, mention_author=False)
                else:
                    await ctx.reply(f'There is no reminder for activity `{activity}`.\n\n{activity_list}', mention_author=False)
                    return
            else:
                await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity]`.\n\n{activity_list}', mention_author=False)
                return
        else:
            await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity]`.\n\n{activity_list}', mention_author=False)
            return
        
# Command "list" - Lists all active reminders
@bot.command(name='list',aliases=('reminders',))
@commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
async def list_cmd(ctx):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        active_reminders = await database.get_active_reminders(ctx)

        if active_reminders == 'None':
            reminders = f'{emojis.bp} You have no active reminders'
        else:
            reminders = ''
            for reminder in active_reminders:
                activity = reminder[0]
                end_time = reminder[1]
                if activity == 'pett':
                    activity = 'Pet tournament'
                elif activity.find('pet-') > -1:
                    pet_id = activity.replace('pet-','')
                    activity = f'Pet {pet_id}'
                elif activity == 'bigarena':
                    activity = 'Big arena'
                elif activity == 'nsmb':
                    activity = 'Not so mini boss'
                elif activity == 'dungmb':
                    activity = 'Dungeon / Miniboss'
                elif activity == 'race':
                    activity = 'Horse race'
                else:
                    activity = activity.capitalize()
                current_time = datetime.utcnow().replace(microsecond=0)
                end_time_datetime = datetime.fromtimestamp(end_time)
                end_time_difference = end_time_datetime - current_time
                time_left = end_time_difference.total_seconds()
                timestring = await global_functions.parse_seconds(time_left)
                
                reminders = f'{reminders}\n{emojis.bp}**`{activity}`** (**{timestring}**)'
                
        reminders = reminders.strip()
        user_name = ctx.author.name
        user_name = user_name.upper()
    
        embed = discord.Embed(
            color = global_data.color,
            title = f'{user_name}\'S REMINDERS',
            description = reminders
        )    
        
        await ctx.reply(embed=embed, mention_author=False)

# Command "hardmode" - Sets hardmode mode
@bot.command(aliases=('hm',))
@commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
async def hardmode(ctx, *args):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        if args:
            arg = args[0]
            if arg in ('on','enable','start'):
                status = await database.set_hardmode(bot, ctx, 1)
            elif arg in ('off','disable','stop'):
                status = await database.set_hardmode(bot, ctx, 0)
            else:
                status = f'**{ctx.author.name}**, the correct syntax is `{prefix}hardmode on` / `off`.'
            await ctx.reply(status, mention_author=False)
        else:
            settings = await database.get_settings(ctx, 'hardmode')
            hm = settings[0]
            if hm == 1:
                hm = 'on'
            elif hm == 0:
                hm = 'off'
            await ctx.reply(f'**{ctx.author.name}**, hardmode mode is currently turned **{hm}**.\nUse `{prefix}hardmode on` / `off` to change it.', mention_author=False)

# Command "dnd" - Sets dnd state
@bot.command()
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def dnd(ctx, *args):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        if args:
            arg = args[0]
            if arg in ('on','enable','start'):
                status = await database.set_dnd(ctx, 1)
            elif arg in ('off','disable','stop'):
                status = await database.set_dnd(ctx, 0)
            else:
                status = f'**{ctx.author.name}**, the correct syntax is `{prefix}dnd on` / `off`.'
            await ctx.reply(status, mention_author=False)
        else:
            settings = await database.get_settings(ctx, 'dnd')
            dnd = settings[0]
            if dnd == 1:
                dnd = 'on'
            elif dnd == 0:
                dnd = 'off'
            await ctx.reply(f'**{ctx.author.name}**, DND mode is currently turned **{dnd}**.\nUse `{prefix}dnd on` / `off` to change it.', mention_author=False)

# Command "ruby" - Checks rubies and sets ruby counter state
@bot.command(aliases=('rubies',))
@commands.bot_has_permissions(send_messages=True, embed_links=True)
async def ruby(ctx, *args):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        
        if args:
            arg = args[0]
            if arg in ('on','enable','start'):
                status = await database.set_ruby_counter(ctx, 1)
            elif arg in ('off','disable','stop'):
                status = await database.set_ruby_counter(ctx, 0)
            else:
                status = f'**{ctx.author.name}**, the correct syntax is `{prefix}ruby on` / `off`.'
            await ctx.reply(status, mention_author=False)
        else:
            settings = await database.get_settings(ctx, 'rubies')
            if not settings == None:
                rubies = settings[0]
                ruby_counter = settings[1]
            else:
                return
            if ruby_counter == 1:
                await ctx.reply(f'**{ctx.author.name}**, you have {rubies} {emojis.ruby} rubies.', mention_author=False)
            elif ruby_counter == 0:
                await ctx.reply(f'**{ctx.author.name}**, the ruby counter is currently turned **off**.\nUse `{prefix}ruby on` to turn it on.', mention_author=False)

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
            
            await database.update_guild(guild_name, guild_leader, guild_members_list)
            await message_after.add_reaction(emojis.navi)


# --- Main menus ---
# Main menu
@bot.command(aliases=('h',))
@commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
async def help(ctx):
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        prefix = await database.get_prefix(ctx)
        
        reminder_management = (
            f'{emojis.bp} `{prefix}list` : List all your active reminders'
        )
                    
        user_settings = (
            f'{emojis.bp} `{prefix}on` / `off` : Turn the bot on/off\n'
            f'{emojis.bp} `{prefix}settings` : Check your settings\n'
            f'{emojis.bp} `{prefix}donator` : Set your EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}enable` / `disable` : Enable/disable specific reminders\n'
            f'{emojis.bp} `{prefix}dnd on` / `off` : Turn DND mode on/off (disables pings)\n'
            f'{emojis.bp} `{prefix}hardmode on` / `off` : Turn hardmode mode on/off (tells your partner to hunt solo)\n'
            f'{emojis.bp} `{prefix}ruby on` / `off` : Turn the ruby counter on/off\n'
            f'{emojis.bp} `{prefix}ruby` : Check your current ruby count'
        )
        
        partner_settings = (
            f'{emojis.bp} `{prefix}partner` : Set your marriage partner\n'
            f'{emojis.bp} `{prefix}partner donator` : Set your partner\'s EPIC RPG donator tier\n'
            f'{emojis.bp} `{prefix}partner channel` : Set the channel for incoming lootbox alerts'
        )
        
        guild_settings = (
            f'{emojis.bp} `{prefix}guild leaderboard` : Check the weekly raid leaderboard\n'
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
        
        await ctx.reply(embed=embed, mention_author=False)



# --- Command detection --- 
# Ascended commands
@bot.command()
@commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
async def ascended(ctx, *args):

    prefix = ctx.prefix
    if prefix.lower() == 'rpg ' and len(args) >= 1:
        
        
        
        arg1 = args[0]
        args = list(args)
        
        if arg1 == 'hunt':
            command = bot.get_command(name='hunt')
        elif arg1 in ('adventure','adv',):
            command = bot.get_command(name='adventure')
        elif arg1 in ('tr','training','ultr','ultraining'):
            command = bot.get_command(name='training')
        elif arg1 in ('chop','axe','bowsaw','chainsaw','fish','net','boat','bigboat','pickup','ladder','tractor','greenhouse','mine','pickaxe','drill','dynamite',):
            command = bot.get_command(name='chop')
        elif arg1 in ('big','not',):
            command = bot.get_command(name='big')
        elif arg1 in ('farm',):
            command = bot.get_command(name='farm')
        else:
            command = None
        
        if not command == None:
            await command.callback(command.cog, ctx, args)



# --- Miscellaneous ---
# Statistics command
@bot.command(aliases=('statistic','statistics,','devstat','ping','about','info','stats'))
@commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
async def devstats(ctx):

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        guilds = len(list(bot.guilds))
        user_number = await database.get_user_number(ctx)
        latency = bot.latency
        
        embed = discord.Embed(
            color = global_data.color,
            title = 'BOT STATISTICS',
            description =   f'{emojis.bp} {guilds:,} servers\n'\
                            f'{emojis.bp} {user_number[0]:,} users\n'\
                            f'{emojis.bp} {round(latency*1000):,} ms latency'
        )
        
        await ctx.reply(embed=embed, mention_author=False)
  
# Hey! Listen!
@bot.command(aliases=('listen',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def hey(ctx):
    
    if not ctx.prefix == 'rpg ':
        await ctx.reply('https://tenor.com/view/navi-hey-listen-gif-4837431', mention_author=False)
    



# --- Owner Commands ---
# Shutdown command (only I can use it obviously)
@bot.command()
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def shutdown(ctx):

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':    
        try:
            await ctx.reply(f'**{ctx.author.name}**, are you **SURE**? `[yes/no]`', mention_author=False)
            answer = await bot.wait_for('message', check=check, timeout=30)
            if answer.content.lower() in ['yes','y']:
                await ctx.send(f'Shutting down.')
                await ctx.bot.logout()
            else:
                await ctx.send(f'Phew, was afraid there for a second.')
        except asyncio.TimeoutError as error:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            
# Sleepy potion text command
@bot.command()
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def sleepy(ctx, arg):
    
    prefix = ctx.prefix
    
    if arg:
        try:
            arg = int(arg)
        except:
            await ctx.send(f'Syntax: `{prefix}sleepy [seconds]`')
            return
        status = await global_functions.reduce_reminder_time(ctx, arg)
        await ctx.send(status)
    else:
        await ctx.send(f'Syntax: `{prefix}sleepy [seconds]`')
        return

# Command "cooldowns" - Sets cooldowns of all activities
@bot.command(aliases=('cd-setup','setup-cd','setup-cooldown','cd-s',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def setup_cooldown(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        if not ctx.author.id in (285399610032390146, 619879176316649482):
            await ctx.reply('You are not allowed to use this command.', mention_author=False)
            return
        
        activity_list = 'Possible activities:'
        for index in range(len(global_data.cooldown_activities)):
            activity_list = f'{activity_list}\n{emojis.bp} `{global_data.cooldown_activities[index]}`'
        
        if args:
            if len(args) in (1,2):
                
                activity_aliases = {
                    'adv': 'adventure',
                    'lb': 'lootbox',
                    'tr': 'training',
                    'chop': 'work',
                    'farming': 'farm',
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
                    'mb': 'miniboss'
                }

                activity = args[0]
                activity = activity.lower()
                
                action = ctx.invoked_with
                
                if len(args) == 2:
                    seconds = args[1]
                    if seconds.isnumeric():
                        seconds = int(seconds)
                    else:
                        if activity.isnumeric():
                            seconds = int(activity)
                            activity = args[1]
                
                    if activity in activity_aliases:
                        activity = activity_aliases[activity]
                    
                    if activity in global_data.cooldown_activities:
                        await ctx.reply(f'**{ctx.author.name}**, this will change the base cooldown (before donor reduction!) of activity **{activity}** to **{seconds:,}** seconds. Continue? [`yes/no`]', mention_author=False)
                        try:
                            answer = await bot.wait_for('message', check=check, timeout=30)
                            if not answer.content.lower() in ['yes','y']:
                                await ctx.send('Aborted')
                                return
                        except asyncio.TimeoutError as error:
                            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                        
                        status = await database.set_cooldown(ctx, activity, seconds)
                        await ctx.reply(status, mention_author=False)
                
                else:
                    cooldown_data = await database.get_cooldowns(ctx)
                    message = 'Current cooldowns:'
                    for cd in cooldown_data:
                        message = f'{message}\n{emojis.bp} {cd[0]}: {cd[1]:,}s'
                        
                    message = f'{message}\n\nUse `{ctx.prefix}{ctx.invoked_with} [activity] [seconds]` to change a cooldown.'
                    await ctx.reply(message, mention_author=False)
            else:
                await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity] [seconds]`.\n\n{activity_list}', mention_author=False)
                return
        else:
            cooldown_data = await database.get_cooldowns(ctx)
            message = 'Current cooldowns:'
            for cd in cooldown_data:
                message = f'{message}\n{emojis.bp} {cd[0]}: {cd[1]:,}s'
                
            message = f'{message}\n\nUse `{ctx.prefix}{ctx.invoked_with} [activity] [seconds]` to change a cooldown.'
            await ctx.reply(message, mention_author=False)
            
# Command "event-reduction" - Sets event reductions of all activities
@bot.command(aliases=('er','event-r','e-r','reduction',))
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def setup_event_reduction(ctx, *args):
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    prefix = ctx.prefix
    if not prefix.lower() == 'rpg ':
        if not ctx.author.id in (285399610032390146, 619879176316649482):
            await ctx.reply('You are not allowed to use this command.', mention_author=False)
            return
        
        activity_list = 'Possible activities:'
        for index in range(len(global_data.cooldown_activities)):
            activity_list = f'{activity_list}\n{emojis.bp} `{global_data.cooldown_activities[index]}`'
        
        if args:
            if len(args) in (1,2):
                
                activity_aliases = {
                    'adv': 'adventure',
                    'lb': 'lootbox',
                    'tr': 'training',
                    'chop': 'work',
                    'farming': 'farm',
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
                    'mb': 'miniboss'
                }

                activity = args[0]
                activity = activity.lower()
                
                action = ctx.invoked_with
                
                if activity == 'reset':
                    await ctx.reply(f'**{ctx.author.name}**, this will change **all** event reductions to **0.0%**. Continue? [`yes/no`]', mention_author=False)
                    try:
                        answer = await bot.wait_for('message', check=check, timeout=30)
                        if not answer.content.lower() in ['yes','y']:
                            await ctx.send('Aborted')
                            return
                    except asyncio.TimeoutError as error:
                        await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                        
                    status = await database.set_event_reduction(ctx, 'all', 0.0)
                    await ctx.reply(status, mention_author=False)
                    return
                
                if len(args) == 2:
                    reduction = args[1]
                    reduction = reduction.replace('%','')
                    try:
                        reduction = float(reduction)
                    except:
                        try:
                            reduction = float(activity)
                            activity = args[1]
                        except:
                            await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity] [reduction in %]`.\n\n{activity_list}', mention_author=False)
                            return
                        
                    if not 0 <= reduction <= 99:
                        await ctx.reply(f'**{ctx.author.name}**, a reduction of **{reduction}%** doesn\'t make much sense, does it.', mention_author=False)
                        return
                
                    if activity in activity_aliases:
                        activity = activity_aliases[activity]
                    
                    if activity in global_data.cooldown_activities:
                        await ctx.reply(f'**{ctx.author.name}**, this will change the event reduction of activity **{activity}** to **{reduction}%**. Continue? [`yes/no`]', mention_author=False)
                        try:
                            answer = await bot.wait_for('message', check=check, timeout=30)
                            if not answer.content.lower() in ['yes','y']:
                                await ctx.send('Aborted')
                                return
                        except asyncio.TimeoutError as error:
                            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                        
                        status = await database.set_event_reduction(ctx, activity, reduction)
                        await ctx.reply(status, mention_author=False)
                
                else:
                    cooldown_data = await database.get_cooldowns(ctx)
                    message = 'Current event reductions:'
                    for cd in cooldown_data:
                        cooldown = cd[1]
                        reduction = cd[2]
                        cooldown = int(ceil(cooldown*((100-reduction)/100)))
                        if not reduction == 0:
                            message = f'{message}\n{emojis.bp} **{cd[0]}: {reduction}% ({cooldown:,}s)**'
                        else:
                            message = f'{message}\n{emojis.bp} {cd[0]}: {reduction}% ({cooldown:,}s)'
                        
                    message = f'{message}\n\nUse `{ctx.prefix}{ctx.invoked_with} [activity] [reduction in %]` to change an event reduction.'
                    await ctx.reply(message, mention_author=False)
            else:
                await ctx.reply(f'The syntax is `{ctx.prefix}{ctx.invoked_with} [activity] [reduction in %]`.\n\n{activity_list}', mention_author=False)
                return
        else:
            cooldown_data = await database.get_cooldowns(ctx)
            message = 'Current event reductions:'
            for cd in cooldown_data:
                cooldown = cd[1]
                reduction = cd[2]
                cooldown = int(ceil(cooldown*((100-reduction)/100)))
                if not reduction == 0:
                    message = f'{message}\n{emojis.bp} **{cd[0]}: {reduction}% ({cooldown:,}s)**'
                else:
                    message = f'{message}\n{emojis.bp} {cd[0]}: {reduction}% ({cooldown:,}s)'
                
            message = f'{message}\n\nUse `{ctx.prefix}{ctx.invoked_with} [activity] [reduction in %]` to change a cooldown.'
            await ctx.reply(message, mention_author=False)

# Command timestring to calculate a time left from a timestamp
@bot.command(aliases=('ts',))
@commands.is_owner()
@commands.bot_has_permissions(send_messages=True, read_message_history=True)
async def timestring(ctx, *args):

    error_syntax = f'It\'s `{ctx.prefix}timestring [timestamp]`, you dummy.'

    if args:
        timestamp = args[0]
        if timestamp.isnumeric():
            try:
                timestamp = float(timestamp)
                current_time = datetime.utcnow().replace(microsecond=0)
                end_time_datetime = datetime.fromtimestamp(timestamp)
                end_time_difference = end_time_datetime - current_time
                time_left = end_time_difference.total_seconds()
                timestring = await global_functions.parse_seconds(time_left)
                await ctx.reply(f'That is **{timestring}** from now.', mention_author=False)
            except:
                await ctx.reply(f'That really didn\'t calculate to anything useful.', mention_author=False)
                return
        else:
            await ctx.reply(error_syntax, mention_author=False)    
    else:
        await ctx.reply(error_syntax, mention_author=False)


bot.run(global_data.TOKEN)