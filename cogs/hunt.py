# hunt.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, tracking, users
from resources import emojis, exceptions, functions, logs, settings, strings


class HuntCog(commands.Cog):
    """Cog that contains the hunt detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_hunt_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the hunt message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Hunt detection: {message}')
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
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message(bot_answer)
        return (bot_answer, bot_message)

    # --- Commands ---
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def hunt(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG hunt messages and creates reminders"""
        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()
        if prefix.lower() != 'rpg ': return
        together = False
        if not args:
            command = 'rpg hunt'
        else:
            if invoked == 'ascended':
                args = list(args)
                command = 'rpg ascended hunt'
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

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.bot_enabled: return
            if not user.alert_hunt.enabled and not user.tracking_enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            partner_donor_tier = user.partner_donor_tier if user.partner_donor_tier <= 3 else 3
            hunt_message = user.alert_hunt.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
            task_status = self.bot.loop.create_task(self.get_hunt_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Hunt detection: {message}')
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
            if bot_message is None:
                task_result = await task_status
                if task_result is not None:
                    bot_answer = task_result[0]
                    bot_message = task_result[1]
                else:
                    await ctx.send('Hunt detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check if it found a cooldown embed, if yes if it is the correct one, if not, ignore it and try to wait for the bot message one more time
            if bot_message.find(f'\'s cooldown') > 1:
                if not user.alert_hunt.enabled: return
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                if (bot_message.find(f'{ctx_author}\'s cooldown') > -1) or (bot_message.find(f'{user.partner_name}\'s cooldown') > -1):
                    timestring_start = bot_message.find('wait at least **') + 16
                    timestring_end = bot_message.find('**...', timestring_start)
                    timestring = bot_message[timestring_start:timestring_end]
                    time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left - time_elapsed
                    if together and ctx_author in bot_message:
                        if partner_donor_tier < user_donor_tier:
                            partner_cooldown = (cooldown.actual_cooldown()
                                                * settings.DONOR_COOLDOWNS[partner_donor_tier])
                            user_cooldown = (cooldown.actual_cooldown()
                                             * settings.DONOR_COOLDOWNS[user_donor_tier])
                            time_left_seconds = (time_left.total_seconds()
                                                 + (partner_cooldown - user_cooldown)
                                                 - time_elapsed.total_seconds()
                                                 + 1)
                            time_left = timedelta(seconds=time_left_seconds)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(ctx.author.id, 'hunt', time_left,
                                                             ctx.channel.id, hunt_message)
                    )

                    if reminder.record_exists:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    if user.partner_id is not None:
                        partner: users.User = await users.get_user(user.partner_id)
                        if together and partner.hardmode_mode_enabled:
                            hm_message = ctx.author.mention if user.dnd_mode_enabled else f'**{ctx.author.name}**,'
                            hm_message = (
                                f'{hm_message} **{user.partner_name}** is currently **hardmoding**.\n'
                                f'If you want to hardmode too, please activate hardmode mode and hunt solo.'
                            )
                            await ctx.send(hm_message)
                        elif not together and not partner.hardmode_mode_enabled:
                            hm_message = ctx.author.mention if user.dnd_mode_enabled else f'**{ctx.author.name}**,'
                            hm_message = (
                                f'{hm_message} **{user.partner_name}** is not hardmoding, '
                                f'feel free to take them hunting.'
                            )
                            await ctx.send(hm_message)
                    return
                else:
                    message = await self.get_hunt_message(ctx)
                    bot_answer = message[0]
                    bot_message = message[1]

            # Check if partner is in the middle of a command, if yes, if it is the correct one, if not, ignore it and try to wait for the bot message one more time
            elif bot_message.find(f'is in the middle of a command') > -1:
                if (bot_message.find(user.partner_name) > -1) and (bot_message.find(f'is in the middle of a command') > -1):
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                else:
                    message = await self.get_hunt_message(ctx)
                    bot_answer = message[0]
                    bot_message = message[1]
            # Ignore anti spam embed
            elif bot_message.find('Huh please don\'t spam') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore failed Epic Guard event
            elif bot_message.find('is now in the jail!') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                await bot_answer.add_reaction(emojis.rip)
                return
            # Ignore higher area error
            elif bot_message.find('This command is unlocked in') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore ascended error
            elif bot_message.find('the ascended command is unlocked with the ascended skill') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when another command is active
            elif bot_message.find('end your previous command') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when using "hunt t" while not married
            elif bot_message.find('you have to be married') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore message that partner is in jail (YES I HAD TO ADD THAT ONE BECAUSE REASONS)
            elif bot_message.find('is in the **jail**') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

            # Add record to the tracking log
            if user.tracking_enabled:
                await tracking.insert_log_entry(user.user_id, ctx.guild.id, 'hunt', current_time)
            if not user.alert_hunt.enabled: return

            # Read partner name from hunt together message and save it to database if necessary (to make the bot check safer)
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            if together:
                partner_search_string = f'** and **'
                partner_name_start = bot_message.find(partner_search_string) + len(partner_search_string)
                partner_name_end = bot_message.find('** are hunting together!', partner_name_start)
                partner_name = bot_message[partner_name_start:partner_name_end]
                if partner_name != '' and partner_name_start != -1 and partner_name_end != -1:
                    await user.update(partner_name=partner_name)

            # Calculate cooldown
            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            if together and partner_donor_tier < user_donor_tier:
                donor_tier = partner_donor_tier
            else:
                donor_tier = user_donor_tier
            if cooldown.donor_affected:
                time_left_seconds = (cooldown.actual_cooldown()
                                     * settings.DONOR_COOLDOWNS[donor_tier]
                                     - time_elapsed.total_seconds())
            else:
                time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
            time_left = timedelta(seconds=time_left_seconds)

            # Save task to database
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(ctx.author.id, 'hunt', time_left,
                                                     ctx.channel.id, hunt_message)
            )

            # Add reaction
            if reminder.record_exists:
                await bot_answer.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)

            # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
            if together and (f'**{user.partner_name}** got ' in bot_message):
                partner_start = bot_message.find(f'**{user.partner_name}** got ')
            else:
                partner_start = len(bot_message)

            if user.partner_id is not None:
                partner: users.User = await users.get_user(user.partner_id)
                if together:
                    lootbox_alert = ''
                    if f'**{user.partner_name}** got ' in bot_message:
                        lootboxes = {
                            ' common lootbox': emojis.LB_COMMON,
                            'uncommon lootbox': emojis.LB_UNCOMMON,
                            'rare lootbox': emojis.LB_RARE,
                            'EPIC lootbox': emojis.LB_EPIC,
                            'EDGY lootbox': emojis.LB_EDGY,
                            'OMEGA lootbox': emojis.LB_OMEGA,
                            ' MEGA present': emojis.PRESENT_MEGA,
                            'ULTRA present': emojis.PRESENT_ULTRA,
                            'OMEGA present': emojis.PRESENT_OMEGA,
                            'GODLY present': emojis.PRESENT_GODLY,
                        }
                        for lootbox_name, lootbox_emoji in lootboxes.items():
                            lootbox_start = bot_message.rfind(lootbox_name)
                            if (lootbox_name in bot_message) and (lootbox_start > partner_start):
                                amount_end = bot_message.rfind('<:', 0, lootbox_start) - 1
                                amount_start = bot_message.rfind('got ', 0, amount_end) + 4
                                amount = bot_message[amount_start:amount_end].replace('*','').strip()
                                partner_message = partner.alert_partner.message.format(
                                    user=ctx.author.name,
                                    lootbox=f'{amount} {lootbox_emoji} {lootbox_name}'
                                )
                                lootbox_alert = partner_message if lootbox_alert == '' else f'{lootbox_alert}\nAlso: {partner_message}'

                    if lootbox_alert != '':
                        await self.bot.wait_until_ready()
                        partner_discord = self.bot.get_user(user.partner_id)
                        lootbox_alert = lootbox_alert.strip()
                        if partner.partner_channel_id is not None and partner.alert_partner.enabled and partner.bot_enabled:
                            try:
                                if partner.dnd_mode_enabled:
                                    lb_message = f'**{partner_discord.name}**, {lootbox_alert}'
                                else:
                                    lb_message = f'{partner_discord.mention} {lootbox_alert}'
                                await self.bot.wait_until_ready()
                                await self.bot.get_channel(partner.partner_channel_id).send(lb_message)
                                await bot_answer.add_reaction(emojis.PARTNER_ALERT)
                            except Exception as error:
                                await ctx.send(f'Had the following error while trying to send the partner alert:\n{error}')

                if together and partner.hardmode_mode_enabled:
                    hm_message = ctx.author.mention if user.dnd_mode_enabled else f'**{ctx.author.name}**,'
                    hm_message = (
                        f'{hm_message} **{user.partner_name}** is currently **hardmoding**.\n'
                        f'If you want to hardmode too, please activate hardmode mode and hunt solo.'
                    )
                    await ctx.send(hm_message)
                elif not together and not partner.hardmode_mode_enabled:
                    hm_message = ctx.author.mention if user.dnd_mode_enabled else f'**{ctx.author.name}**,'
                    hm_message = (
                        f'{hm_message} **{user.partner_name}** is not hardmoding, '
                        f'feel free to take them hunting.'
                    )
                    await ctx.send(hm_message)

            if f'**{ctx.author.name}** got' in bot_message:
                found_stuff = {
                    #'common lootbox': emojis.lbcommon,
                    #'uncommon lootbox': emojis.lbuncommon,
                    #'rare lootbox': emojis.lbrare,
                    #'EPIC lootbox': emojis.lbepic,
                    #'EDGY lootbox': emojis.lbedgy,
                    'OMEGA lootbox': emojis.SURPRISE,
                    'GODLY lootbox': emojis.SURPRISE,
                }
                for stuff_name, stuff_emoji in found_stuff.items():
                    if (stuff_name in bot_message) and (bot_message.rfind(stuff_name) < partner_start):
                        await bot_answer.add_reaction(stuff_emoji)

            # Add an F if the user died
            if (bot_message.find(f'**{ctx_author}** lost but ') > -1) or (bot_message.find('but lost fighting') > -1):
                await bot_answer.add_reaction(emojis.RIP)

        except asyncio.TimeoutError as error:
            await ctx.send('Hunt detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Hunt detection error: {e}')
            return

# Initialization
def setup(bot):
    bot.add_cog(HuntCog(bot))