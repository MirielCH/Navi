# nsmb-bigarena.py

import asyncio
from datetime import datetime
from typing import Tuple

import discord
from discord.ext import commands

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings


class NotSoMiniBossBigArenaCog(commands.Cog):
    """Cog that contains the not so mini boss and big arena detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_nsmbba_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the not so mini boss / big arena message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Big arena / Not so miniboss detection: {message}')
                if  ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **big arena** event') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **not so "mini" boss** event') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you are already registered!') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find('You have started an arena recently') > -1))\
                or ((message.find(f'{ctx_author}') > -1) and (message.find('You have been in a fight with a boss recently') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message(bot_answer)
        return (bot_answer, bot_message)

    @commands.command(aliases=('not',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def big(self, ctx, *args):
        """Detects EPIC RPG adventure messages and creates reminders"""
        prefix = ctx.prefix
        invoked = ctx.invoked_with
        invoked = invoked.lower()
        if prefix.lower() != 'rpg ': return
        if not args: return
        full_args = ''
        if invoked == 'ascended':
            args = list(args)
            args.pop(0)
        args = [arg.lower() for arg in args]
        for arg in args:
            if arg == 'miniboss': return
            full_args = f'{full_args}{arg}'
        if full_args == 'sominibossjoin':
            event = 'not-so-mini-boss'
        elif full_args == 'arenajoin':
            event = 'big-arena'
        else:
            return

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled: return
            if not user.alert_big_arena.enabled and event == 'big-arena': return
            if not user.alert_not_so_mini_boss.enabled and event == 'not-so-mini-boss': return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            if event == 'big-arena':
                event_message = user.alert_big_arena.message.format(event='big arena')
            elif event == 'not-so-mini-boss':
                event_message = user.alert_not_so_mini_boss.message.format(event='not so mini boss')
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_nsmbba_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Big arena / Not so mini boss detection: {message}')
                        if  ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **big arena** event') > -1))\
                        or ((message.find(f'{ctx_author}') > -1) and (message.find(f'successfully registered for the next **not so "mini" boss** event') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you are already registered!') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'the ascended command is unlocked with the ascended skill') > -1))\
                        or (message.find('This command is unlocked in') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                        or ((message.find(f'{ctx_author}') > -1) and (message.find('You have started an arena recently') > -1))\
                        or ((message.find(f'{ctx_author}') > -1) and (message.find('You have been in a fight with a boss recently') > -1)):
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
                    await ctx.send('Big arena / Not so mini boss detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check if event message with time in it, if yes, read the time and update/insert the reminder if necessary
            if bot_message.find(f'The next event is in') > -1:
                timestring_start = bot_message.find('event is in **') + 14
                timestring_end = bot_message.find('**,', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(self.bot, ctx.author.id, event, time_left,
                                                         ctx.channel.id, event_message)
                )
                if reminder.record_exists:
                    await bot_answer.add_reaction(emojis.NAVI)
                else:
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
            # Ignore if on cooldown
            elif ((bot_message.find('You have started an arena recently') > 1)
                  or (bot_message.find('You have been in a fight with a boss recently') > 1)):
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

        except asyncio.TimeoutError as error:
            await ctx.send('Big arena / Not so mini boss detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Big arena / Not so mini boss detection error: {e}')
            return

# Initialization
def setup(bot):
    bot.add_cog(NotSoMiniBossBigArenaCog(bot))