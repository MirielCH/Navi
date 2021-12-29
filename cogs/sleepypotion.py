# sleepypotion.py

import asyncio
from datetime import timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings

 # Change these to change the event prefix
EVENT_NAME = 'xmas'
EVENT_ALIASES = ('christmas',)


class SleepyPotionCog(commands.Cog):
    """Cog that contains the sleepy potion detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_sleepy_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the sleepy potion message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Sleepy detection: {message}')
                if  ((message.find(ctx_author) > -1) and (message.find('has slept for a day') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have a sleepy potion') > -1))\
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

    async def get_boo_message(self, ctx):
        """Waits for the hal boo message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Boo detection: {message}')
                if ((message.find(ctx_author) > -1) and (message.find('failed to scare') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('scared') > -1))\
                or ('bots cannot be scared' in message)\
                or ('you can\'t scare yourself lol' in message)\
                or ('so no chance to scare lol' in message)\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have scared someone recently') > -1))\
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
    @commands.command(name=EVENT_NAME, aliases=EVENT_ALIASES)
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def sleepy_potion(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG sleepy potion messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if not args: return
        args = [arg.lower() for arg in args]
        args_full = ''
        for arg in args:
            args_full = f'{args_full} {arg}'
        if args_full.strip() == 'use sleepy potion':
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled: return
        try:
            task_status = self.bot.loop.create_task(self.get_sleepy_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Sleepy potion detection: {message}')
                        if  ((message.find(ctx_author) > -1) and (message.find('has slept for a day') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have a sleepy potion') > -1))\
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
                    await ctx.send('Sleepy potion detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            if bot_message.find('has slept for a day') > -1:
                await reminders.reduce_reminder_time(ctx.author.id, timedelta(days=1))
                await bot_answer.add_reaction(emojis.NAVI)
            # Ignore if htey don't have a potion
            elif bot_message.find(f'you don\'t have a sleepy potion') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore in the middle of command error
            elif bot_message.find('so no chance to scare lol') > 1:
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
            await ctx.send('Sleepy Potion detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Sleepy potion detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(SleepyPotionCog(bot))