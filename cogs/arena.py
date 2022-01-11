# arena.py

import asyncio
from typing import Tuple

import discord
from discord.ext import commands
from datetime import datetime

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings


class ArenaCog(commands.Cog):
    """Cog that contains the arena detection commands"""
    def __init__(self, bot):
        self.bot = bot

    # Arena detection
    async def get_arena_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the arena message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Arena detection: {message}')
                if  ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have started an arena recently') > -1))\
                or (message.find(f'{ctx_author}** started an arena event!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
    # Arena (cooldown detection only)
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def arena(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG arena messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        command = 'rpg arena'

        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.bot_enabled or not user.alert_arena.enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            arena_message = user.alert_arena.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_arena_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Arena detection: {message}')
                        if  ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have started an arena recently') > -1))\
                        or (message.find(f'{ctx_author}** started an arena event!') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                    await ctx.send('Arena detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
            if bot_message.find(f'{ctx_author}\'s cooldown') > -1:
                timestring_start = bot_message.find('wait at least **') + 16
                timestring_end = bot_message.find('**...', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(ctx.author.id, 'arena', time_left,
                                                             ctx.channel.id, arena_message)
                    )
                if reminder.record_exists:
                    await bot_answer.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

        except asyncio.TimeoutError:
            await ctx.send('Arena detection timeout.')
        except Exception as e:
            logs.logger.error(f'Arena detection error: {e}')

# Initialization
def setup(bot):
    bot.add_cog(ArenaCog(bot))