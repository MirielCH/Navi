# buy.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class BuyCog(commands.Cog):
    """Cog that contains the buy detection commands"""
    def __init__(self, bot):
        self.bot = bot

    # Buy detection
    async def get_buy_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the adventure message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Work detection: {message}')
                if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
                or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('check the name of the item again') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you have to be level') > -1))\
                or (message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > -1)\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough coins to do this') > -1))\
                or (message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
    # Buy
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def buy(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG buy messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if not args: return

        command = 'rpg buy lootbox'
        args = [arg.lower() for arg in args]
        arg1 = args[0]
        if len(args) >= 2:
            arg2 = args[1]

        if arg1 == 'lottery' and arg2 == 'ticket':
            command = self.bot.get_command(name='lottery')
            if command is not None:
                await command.callback(command.cog, ctx, args)
            return
        elif (len(args) in (1,2)) and ((arg1 in ('lb','lootbox')) or (arg2 in ('lb','lootbox'))):
            try:
                try:
                    user: users.User = await users.get_user(ctx.author.id)
                except exceptions.NoDataFoundError:
                    return
                if not user.reminders_enabled or not user.alert_lootbox.enabled: return
                user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
                lootbox_message = user.alert_lootbox.message.replace('%',command)
                current_time = datetime.utcnow().replace(microsecond=0)
                task_status = self.bot.loop.create_task(self.get_buy_message(ctx))
                bot_message = None
                message_history = await ctx.channel.history(limit=50).flatten()
                for msg in message_history:
                    if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                        try:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message = await functions.encode_message(msg)
                            if settings.DEBUG_MODE: logs.logger.debug(f'Buy detection: {message}')
                            if  (message.find('lootbox` successfully bought for') > -1) or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already bought a lootbox') > -1))\
                            or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                            or (message.find('You can\'t carry more than 1 lootbox at once!') > -1)\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find('check the name of the item again') > -1))\
                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you have to be level') > -1))\
                            or (message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > -1)\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough coins to do this') > -1))\
                            or (message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
                        await ctx.send('Buy detection timeout.')
                        return
                if not task_status.done(): task_status.cancel()

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
                        await reminders.insert_user_reminder(self.bot, ctx.author.id, 'lootbox', time_left,
                                                             ctx.channel.id, lootbox_message)
                    )
                    if reminder.record_exists:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                # Ignore error message that appears if you already own a lootbox
                elif bot_message.find('You can\'t carry more than 1 lootbox at once!') > -1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                # Ignore error message that you are too low level to buy a lootbox
                elif bot_message.find('you have to be level') > -1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
                # Ignore not enough money info
                elif (bot_message.find(f'you don\'t have enough coins to do this') > -1) or (bot_message.find(f'You don\'t have enough money to buy this lmao') > -1):
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
                # Ignore error when trying to buy omegas or godlys
                elif bot_message.find('You can\'t buy this type of lootboxes, keep trying to drop them!') > 1:
                    await bot_answer.add_reaction(emojis.SAD)
                    return

                # Calculate cooldown
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('lootbox')
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                         * settings.DONOR_COOLDOWNS[user_donor_tier]
                                         - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)

                # Save reminder to database
                reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(self.bot, ctx.author.id, 'lootbox', time_left,
                                                             ctx.channel.id, lootbox_message)
                    )

                # Add reaction
                if reminder.record_exists:
                    await bot_answer.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)
            except asyncio.TimeoutError:
                await ctx.send('Buy detection timeout.')
                return
            except Exception as e:
                logs.logger.error(f'Buy detection error: {e}')
                return


# Initialization
def setup(bot):
    bot.add_cog(BuyCog(bot))