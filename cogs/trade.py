# trade.py

import asyncio
from typing import Tuple

import discord
from discord.ext import commands

from database import users
from resources import emojis, exceptions, functions, logs, settings, strings


class TradeCog(commands.Cog):
    """Cog that contains the trade detection commands"""
    def __init__(self, bot):
        self.bot = bot

    # Trade detection
    async def get_trade_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the trade message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_with_fields_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Trade detection: {message}')
                if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('duh the amount has to be') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot trade rubies if you did not unlock area 5') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Alright! Our trade is done then') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message_with_fields(bot_answer)
        return (bot_answer, bot_message)

    # --- Commands ---
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def trade(self, ctx: commands.Context, *args: tuple) -> None:
        """Detects EPIC RPG trade messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if not args: return
        trade_id = args[0].lower()
        if trade_id not in ('e','f'): return
        try:
            user: users.User = await users.get_user(ctx.author.id)
        except exceptions.NoDataFoundError:
            return
        if not user.reminders_enabled or not user.ruby_counter_enabled.enabled: return
        try:
            task_status = self.bot.loop.create_task(self.get_trade_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message_with_fields(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Trade detection: {message}')
                        if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have enough') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('duh the amount has to be') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot trade rubies if you did not unlock area 5') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('Alright! Our trade is done then') > -1))\
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
                    await ctx.send('Trade detection timeout.')
                    return

            if bot_message.find('Our trade is done then') > -1:
                rubies_start = bot_message.find('<:ruby:') + 28
                if trade_id == 'f':
                    rubies_end = bot_message.find(f'\'', rubies_start)
                else:
                    rubies_end = bot_message.find(f'n**', rubies_start) -1
                rubies = bot_message[rubies_start:rubies_end]
                if rubies.isnumeric():
                    rubies = int(rubies)
                    if trade_id == 'f':
                        rubies = user.rubies + int(rubies)
                    else:
                        rubies = user.rubies - int(rubies)
                        if rubies < 0: rubies = 0
                    await user.update(rubies=rubies)
                    if user.rubies == rubies:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        await ctx.send(strings.MSG_ERROR)
                else:
                    await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')

            # Ignore failed trades
            elif (bot_message.find('duh the amount has to be') > -1) or (bot_message.find(f'you don\'t have enough') > -1) or (bot_message.find(f'you cannot trade rubies if you did not unlock area 5') > -1):
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

        except asyncio.TimeoutError:
            await ctx.send('Trade detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Trade detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(TradeCog(bot))