# clan.py
# Contains clan detection commands

import asyncio
from typing import Tuple

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from database import clans, cooldowns, reminders
from resources import emojis, exceptions, functions, logs, settings, strings


class ClanCog(commands.Cog):
    """Cog that contains the clan detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_clan_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the clan message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_clan_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Clan detection: {message}')
                if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1)\
                or (message.find('Guild successfully upgraded!') > -1) or (message.find('Guild upgrade failed!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('end your previous command') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('your guild has already 100') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message_clan(bot_answer)
        return (bot_answer, bot_message)

    # --- Commands ---
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def clan_detection(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG clan messages and creates reminders"""
        if args:
            arg = args[0]
            arg = arg.lower()
            if arg in ('raid', 'upgrade'):
                try:
                    try:
                        clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
                    except exceptions.NoDataFoundError:
                        return
                    if not clan.alert_enabled: return
                    current_time = datetime.utcnow().replace(microsecond=0)
                    task_status = self.bot.loop.create_task(self.get_clan_message(ctx))
                    bot_message = None
                    message_history = await ctx.channel.history(limit=50).flatten()
                    for msg in message_history:
                        if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                            try:
                                ctx_author = (str(ctx.author.name)
                                                 .encode('unicode-escape', errors='ignore')
                                                 .decode('ASCII')
                                                 .replace('\\',''))
                                message = await functions.encode_message_clan(msg)
                                if settings.DEBUG_MODE: logs.logger.debug(f'Clan detection: {message}')
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
                    if bot_message is None:
                        task_result = await task_status
                        if task_result is not None:
                            bot_answer = task_result[0]
                            bot_message = task_result[1]
                        else:
                            await ctx.send('Guild detection timeout.')
                            return
                    if not task_status.done(): task_status.cancel()
                    clan_upgraded = False

                    # Check if stealth was upgraded
                    if (bot_message.find('Guild successfully upgraded!') > -1) or (bot_message.find('Guild upgrade failed!') > -1):
                        stealth_start = bot_message.find('--> **') + 6
                        stealth_end = bot_message.find('**', stealth_start)
                        stealth = bot_message[stealth_start:stealth_end]
                        clan_stealth_before = clan.stealth_current
                        clan_upgraded = True
                        await clan.update(stealth_current=int(stealth))

                    # Add raid to the leaderboard if there was a raid
                    if bot_message.find(' RAIDED ') > 1:
                        energy_start = bot_message.find('earned **') + 9
                        energy_end = bot_message.find(':low_brightness:', energy_start) - 3
                        energy = bot_message[energy_start:energy_end]
                        clan_raid = await clans.insert_clan_raid(clan.clan_name, ctx.author.id, int(energy), current_time)
                        if not clan_raid.record_exists:
                            if settings.DEBUG_MODE:
                                await ctx.send(
                                    'There was an error adding the raid to the leaderboard. Please tell Miri he\'s an idiot.'
                                )

                    # Set message to send
                    if clan.stealth_current >= clan.stealth_threshold:
                        clan_message = clan.alert_message.replace('%','rpg guild raid')
                    else:
                        clan_message = clan.alert_message.replace('%','rpg guild upgrade')

                    # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
                    if bot_message.find(f'\'s cooldown') > 1:
                        timestring_start = bot_message.find('wait at least **') + 16
                        timestring_end = bot_message.find('**...', timestring_start)
                        timestring = bot_message[timestring_start:timestring_end]
                        time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                        bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                        time_elapsed = current_time - bot_answer_time
                        time_left = time_left - time_elapsed
                        reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                             clan.channel_id, clan_message)
                        )
                        if reminder.record_exists:
                            await bot_answer.add_reaction(emojis.NAVI)
                        else:
                            if settings.DEBUG_MODE:
                                await ctx.send(strings.MSG_ERROR)
                            return
                    # Ignore message that guild is fully upgraded
                    elif bot_message.find('your guild has already 100') > 1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return
                    # Ignore anti spam embed
                    elif bot_message.find('Huh please don\'t spam') > 1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return
                    # Ignore failed Epic Guard event
                    elif bot_message.find('is now in the jail!') > 1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        await bot_answer.add_reaction(emojis.RIP)
                        return
                    # Ignore error when another command is active
                    elif bot_message.find('end your previous command') > 1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return

                    # Calculate cooldown
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                    reminder: reminders.Reminder = await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                                                        clan.channel_id, clan_message)

                    # Add reaction
                    if reminder.record_exists:
                        await bot_answer.add_reaction(emojis.NAVI)
                        if clan_upgraded and clan.stealth_current >= clan.stealth_threshold:
                            await bot_answer.add_reaction(emojis.YAY)
                        if clan_upgraded and clan.stealth_current == clan_stealth_before:
                            await bot_answer.add_reaction(emojis.ANGRY)
                    if not reminder.record_exists and settings.DEBUG_MODE:
                        await ctx.send(strings.MSG_ERROR)
                except asyncio.TimeoutError:
                    await ctx.send('Guild detection timeout.')
                    return
                except Exception as error:
                    logs.logger.error(f'Clan detection error: {error}')
                    return
        if not args:
            try:
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
                except exceptions.NoDataFoundError:
                    return
                task_status = self.bot.loop.create_task(self.get_clan_message(ctx))
                bot_message = None
                message_history = await ctx.channel.history(limit=50).flatten()
                for msg in message_history:
                    if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                        try:
                            ctx_author = (
                                str(ctx.author.name)
                                .encode('unicode-escape',errors='ignore')
                                .decode('ASCII')
                                .replace('\\','')
                            )
                            message = await functions.encode_message_clan(msg)
                            if settings.DEBUG_MODE: logs.logger.debug(f'Clan detection: {message}')
                            if  (message.find('Your guild was raided') > -1) or (message.find(f'**{ctx_author}** RAIDED ') > -1)\
                            or (message.find('Guild successfully upgraded!') > -1) or (message.find('Guild upgrade failed!') > -1)\
                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('end your previous command') > -1))\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('your guild has already 100') > -1))\
                            or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('Your guild has already raided or been upgraded') > -1)):
                                bot_answer = msg
                                bot_message = message
                        except Exception as error:
                            await ctx.send(f'Error reading message history: {error}')

                if bot_message is None:
                    task_result = await task_status
                    if task_result is not None:
                        bot_answer = task_result[0]
                        bot_message = task_result[1]
                    else:
                        await ctx.send('Guild detection timeout.')
                        return
                if not task_status.done(): task_status.cancel()

                # Check if correct embed
                if bot_message.find('Your guild was raided') > -1:
                    if clan.alert_enabled:
                        # Upgrade stealth (no point in upgrading that without active reminders)
                        stealth_start = bot_message.find('**STEALTH**: ') + 13
                        stealth_end = bot_message.find('\\n', stealth_start)
                        stealth = bot_message[stealth_start:stealth_end]
                        await clan.update(stealth_current=int(stealth))

                        # Set message to send
                        if clan.stealth_current >= clan.stealth_threshold:
                            clan_message = clan.alert_message.replace('%','rpg guild raid')
                        else:
                            clan_message = clan.alert_message.replace('%','rpg guild upgrade')

                        # Update reminder
                        timestring_start = bot_message.find(':clock4: ') + 11
                        timestring_end = bot_message.find('**', timestring_start)
                        timestring = bot_message[timestring_start:timestring_end]
                        timestring = timestring.lower()
                        time_left = await functions.parse_timestring_to_timedelta(ctx, timestring)
                        reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                             clan.channel_id, clan_message)
                        )
                        if reminder.record_exists:
                            await bot_answer.add_reaction(emojis.NAVI)
                        else:
                            if settings.DEBUG_MODE:
                                await ctx.send(strings.MSG_ERROR)
                            return
                # Ignore anti spam embed
                elif bot_message.find('Huh please don\'t spam') > 1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                # Ignore failed Epic Guard event
                elif bot_message.find('is now in the jail!') > 1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    await bot_answer.add_reaction(emojis.RIP)
                    return
                # Ignore error when another command is active
                elif bot_message.find('end your previous command') > 1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                else:
                    return
            except asyncio.TimeoutError as error:
                await ctx.send('Guild detection timeout.')
                return
            except Exception as e:
                logs.logger.error(f'Guild detection error: {e}')
                return


# Initialization
def setup(bot):
    bot.add_cog(ClanCog(bot))