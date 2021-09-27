# hunt.py

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

# hunt commands (cog)
class huntCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hunt detection
    async def get_hunt_message(self, ctx):

        def epic_rpg_check(m):
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = global_functions.encode_message_non_async(m)

                if global_data.DEBUG_MODE == 'ON':
                    global_data.logger.debug(f'Hunt detection: {message}')

                if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1)))\
                    or ((message.find(f'\'s cooldown') > -1) and (message.find('You have already looked around') > -1))\
                    or ((message.find(ctx_author) > -1) and (message.find('pretends to be a zombie') > -1))\
                    or ((message.find(ctx_author) > -1) and (message.find('fights the horde') > -1))\
                    or ((message.find(ctx_author) > -1) and (message.find('Thankfully, the horde did not notice') > -1))\
                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you have to be married') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                    or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or (message.find(f'is in the middle of a command') > -1)\
                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find('is in the **jail**') > -1)):
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
    # Hunt
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def hunt(self, ctx, *args):

        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()

        if prefix.lower() == 'rpg ':
            together = False
            if args:
                if invoked == 'ascended':
                    command = 'rpg ascended hunt'
                    args = args[0]
                    args.pop(0)
                else:
                    command = 'rpg hunt'
                args = [arg.lower() for arg in args]
                if any(arg in ['hardmode','h'] for arg in args):
                    command = f'{command} hardmode'
                if any(arg in ['together','t'] for arg in args):
                    command = f'{command} together'
                    together = True
                if ('alone' in args):
                    command = f'{command} alone'
            else:
                command = 'rpg hunt'

            try:
                settings = await database.get_settings(ctx, 'hunt')
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
                        dnd = settings[8]

                        # Set message to send
                        if hunt_message == None:
                            hunt_message = default_message.replace('%',command)
                        else:
                            hunt_message = hunt_message.replace('%',command)

                        if not hunt_enabled == 0:
                            task_status = self.bot.loop.create_task(self.get_hunt_message(ctx))
                            bot_message = None
                            message_history = await ctx.channel.history(limit=50).flatten()
                            for msg in message_history:
                                if (msg.author.id == global_data.epic_rpg_id) and (msg.created_at > ctx.message.created_at):
                                    try:
                                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                        message = await global_functions.encode_message(msg)

                                        if global_data.DEBUG_MODE == 'ON':
                                            global_data.logger.debug(f'Hunt detection: {message}')

                                        if  ((message.find(ctx_author) > -1) and ((message.find('found a') > -1) or (message.find(f'are hunting together!') > -1)))\
                                            or ((message.find(f'\'s cooldown') > -1) and (message.find('You have already looked around') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('pretends to be a zombie') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('fights the horde') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('Thankfully, the horde did not notice') > -1))\
                                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you have to be married') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                                            or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or (message.find(f'is in the middle of a command') > -1)\
                                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('is in the **jail**') > -1)):
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
                                    await ctx.send('Hunt detection timeout.')
                                    return
                            # Check if it found a cooldown embed, if yes if it is the correct one, if not, ignore it and try to wait for the bot message one more time
                            if bot_message.find(f'\'s cooldown') > 1:
                                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                if (bot_message.find(f'{ctx_author}\'s cooldown') > -1) or (bot_message.find(f'{partner_name}\'s cooldown') > -1):
                                    timestring_start = bot_message.find('wait at least **') + 16
                                    timestring_end = bot_message.find('**...', timestring_start)
                                    timestring = bot_message[timestring_start:timestring_end]
                                    timestring = timestring.lower()
                                    time_left = await global_functions.parse_timestring(ctx, timestring)
                                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                                    current_time = datetime.utcnow().replace(microsecond=0)
                                    time_elapsed = current_time - bot_answer_time
                                    time_elapsed_seconds = time_elapsed.total_seconds()
                                    if partner_name is not None and ctx_author in bot_message:
                                        if partner_donor_tier < user_donor_tier:
                                            time_left = (time_left / global_data.donor_cooldowns[user_donor_tier]
                                                         * global_data.donor_cooldowns[partner_donor_tier]
                                                         - time_elapsed_seconds
                                                         + 1)
                                        else:
                                            time_left = time_left - time_elapsed_seconds
                                    else:
                                        time_left = time_left - time_elapsed_seconds
                                    write_status = await global_functions.write_reminder(self.bot, ctx, 'hunt', time_left, hunt_message)
                                    if write_status in ('inserted','scheduled','updated'):
                                        await bot_answer.add_reaction(emojis.navi)
                                    else:
                                        if global_data.DEBUG_MODE == 'ON':
                                            await bot_answer.add_reaction(emojis.cross)

                                    if not partner_id == 0:
                                        partner_settings = await database.get_settings(ctx, 'partner_alert_hardmode', partner_id)
                                        partner_hardmode = partner_settings[3]

                                        if together == True and partner_hardmode == 1:
                                            if dnd == 0:
                                                hm_message = f'{ctx.author.mention} **{partner_name}** is currently **hardmoding**.\nIf you want to hardmode too, please activate hardmode mode and hunt solo.'
                                            else:
                                                hm_message = f'**{ctx.author.name}**, **{partner_name}** is currently **hardmoding**.\nIf you want to hardmode too, please activate hardmode mode and hunt solo.'
                                            await ctx.send(hm_message)

                                        elif together == False and partner_hardmode == 0:
                                            if dnd == 0:
                                                hm_message = f'{ctx.author.mention} **{partner_name}** is not hardmoding, feel free to take them hunting.'
                                            else:
                                                hm_message = f'**{ctx.author.name}**, **{partner_name}** is not hardmoding, feel free to take them hunting.'
                                            await ctx.send(hm_message)
                                    return
                                else:
                                    message = await self.get_hunt_message(ctx)
                                    bot_answer = message[0]
                                    bot_message = message[1]

                            # Check if partner is in the middle of a command, if yes, if it is the correct one, if not, ignore it and try to wait for the bot message one more time
                            elif bot_message.find(f'is in the middle of a command') > -1:
                                if (bot_message.find(partner_name) > -1) and (bot_message.find(f'is in the middle of a command') > -1):
                                    if global_data.DEBUG_MODE == 'ON':
                                        await bot_answer.add_reaction(emojis.cross)
                                    return
                                else:
                                    message = await self.get_hunt_message(ctx)
                                    bot_answer = message[0]
                                    bot_message = message[1]
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
                            # Ignore higher area error
                            elif bot_message.find('This command is unlocked in') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore ascended error
                            elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error when another command is active
                            elif bot_message.find('end your previous command') > 1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore error when using "hunt t" while not married
                            elif bot_message.find('you have to be married') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Ignore message that partner is in jail (YES I HAD TO ADD THAT ONE BECAUSE REASONS)
                            elif bot_message.find('is in the **jail**') > -1:
                                if global_data.DEBUG_MODE == 'ON':
                                    await bot_answer.add_reaction(emojis.cross)
                                return
                            # Read partner name from hunt together message and save it to database if necessary (to make the bot check safer)
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            if together:
                                partner_search_string = f'** and **'
                                partner_name_start = bot_message.find(partner_search_string) + len(partner_search_string)
                                partner_name_end = bot_message.find('** are hunting together!', partner_name_start)
                                partner_name = bot_message[partner_name_start:partner_name_end]
                                if not partner_name == '':
                                    await database.set_hunt_partner(ctx, partner_name)
                        else:
                            return
                    else:
                        return
                else:
                    return

                # Calculate cooldown
                cooldown_data = await database.get_cooldown(ctx, 'hunt')
                cooldown = int(cooldown_data[0])
                donor_affected = int(cooldown_data[1])
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_elapsed_seconds = time_elapsed.total_seconds()
                if together and partner_donor_tier < user_donor_tier:
                    donor_tier = partner_donor_tier
                else:
                    donor_tier = user_donor_tier

                if donor_affected:
                    time_left = cooldown*global_data.donor_cooldowns[donor_tier]-time_elapsed_seconds
                else:
                    time_left = cooldown-time_elapsed_seconds


                # Save task to database
                write_status = await global_functions.write_reminder(self.bot, ctx, 'hunt', time_left, hunt_message)

                # Add reaction
                if not write_status == 'aborted':
                    await bot_answer.add_reaction(emojis.navi)
                else:
                    if global_data.DEBUG_MODE == 'ON':
                        await ctx.send('There was an error scheduling this reminder. Please tell Miri he\'s an idiot.')

                # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
                if together and (f'**{partner_name}** got ' in bot_message):
                    partner_start = bot_message.find(f'**{partner_name}** got ')
                else:
                    partner_start = len(bot_message)

                if not partner_id == 0:
                    partner_settings = await database.get_settings(ctx, 'partner_alert_hardmode', partner_id)
                    partner_hardmode = partner_settings[3]

                    if together == True:
                        await self.bot.wait_until_ready()
                        partner = self.bot.get_user(partner_id)
                        lootbox_alert = ''

                        if f'**{partner_name}** got ' in bot_message:
                            lootboxes = {
                                'common lootbox': emojis.lbcommon,
                                'uncommon lootbox': emojis.lbuncommon,
                                'rare lootbox': emojis.lbrare,
                                'EPIC lootbox': emojis.lbepic,
                                'EDGY lootbox': emojis.lbedgy,
                                'OMEGA lootbox': emojis.lbomega,
                                'GODLY lootbox': emojis.lbgodly
                            }
                            for lootbox_name, lootbox_emoji in lootboxes.items():
                                if (lootbox_name in bot_message) and (bot_message.rfind(lootbox_name) > partner_start):
                                    lootbox_alert = global_data.alert_message.format(user=ctx.author.name,
                                                                                     lootbox=f'a {lootbox_emoji} {lootbox_name}')
                        if lootbox_alert != '':
                            partner_channel_id = partner_settings[0]
                            partner_reminders_on = partner_settings[1]
                            alert_enabled = partner_settings[2]
                            partner_dnd = partner_settings[4]
                            if not partner_channel_id == None and not alert_enabled == 0 and not partner_reminders_on == 0:
                                try:
                                    if partner_dnd == 0:
                                        lb_message = f'{partner.mention} {lootbox_alert}'
                                    else:
                                        lb_message = f'**{partner.name}**, {lootbox_alert}'
                                    await self.bot.wait_until_ready()
                                    await self.bot.get_channel(partner_channel_id).send(lb_message)
                                    await bot_answer.add_reaction(emojis.partner_alert)
                                except Exception as e:
                                    await ctx.send(e)

                        if partner_hardmode == 1:
                            if dnd == 0:
                                hm_message = f'{ctx.author.mention} **{partner_name}** is currently **hardmoding**.\nIf you want to hardmode too, please activate hardmode mode and hunt solo.'
                            else:
                                hm_message = f'**{ctx.author.name}**, **{partner_name}** is currently **hardmoding**.\nIf you want to hardmode too, please activate hardmode mode and hunt solo.'
                            await ctx.send(hm_message)
                    else:
                        if partner_hardmode == 0:
                            if dnd == 0:
                                hm_message = f'{ctx.author.mention} **{partner_name}** is not hardmoding, feel free to take them hunting.'
                            else:
                                hm_message = f'**{ctx.author.name}**, **{partner_name}** is not hardmoding, feel free to take them hunting.'
                            await ctx.send(hm_message)

                if f'**{ctx.author.name}** got' in bot_message:
                    good_lootboxes = {
                        'OMEGA lootbox': emojis.lbomega,
                        'GODLY lootbox': emojis.lbgodly
                    }
                    for lootbox_name, lootbox_emoji in good_lootboxes.items():
                        if (lootbox_name in bot_message) and (bot_message.rfind(lootbox_name) < partner_start):
                            await bot_answer.add_reaction(emojis.fire)

                # Add an F if the user died
                if (bot_message.find(f'**{ctx_author}** lost but ') > -1) or (bot_message.find('but lost fighting') > -1):
                    await bot_answer.add_reaction(emojis.rip)

            except asyncio.TimeoutError as error:
                await ctx.send('Hunt detection timeout.')
                return
            except Exception as e:
                global_data.logger.error(f'Hunt detection error: {e}')
                return

# Initialization
def setup(bot):
    bot.add_cog(huntCog(bot))