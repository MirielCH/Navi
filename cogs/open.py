# open.py

import asyncio
from typing import Tuple

import discord
from discord.ext import commands

from database import users
from resources import emojis, exceptions, functions, logs, settings, strings


class OpenCog(commands.Cog):
    """Cog that contains the open detection commands"""
    def __init__(self, bot):
        self.bot = bot

    # Open detection
    async def get_open_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the adventure message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Open detection: {message}')
                if  ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have any of this lootbox type') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what lootbox are you trying to open?') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                or (message.find(f'Huh you don\'t have that many of this lootbox type') > -1)\
                or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('lootbox opened!') > -1))\
                or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('You were about to open a nice lootbox') > -1))\
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
    @commands.command()
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def open(self, ctx, *args):
        """Detects EPIC RPG open messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if not args: return

        try:
            user: users.User = await users.get_user(ctx.author.id)
        except exceptions.NoDataFoundError:
            return
        if not user.bot_enabled or not user.ruby_counter_enabled: return
        try:
            task_status = self.bot.loop.create_task(self.get_open_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Open detection: {message}')
                        if  ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you don\'t have any of this lootbox type') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what lootbox are you trying to open?') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what are you doing??') > -1))\
                        or (message.find(f'Huh you don\'t have that many of this lootbox type') > -1)\
                        or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('lootbox opened!') > -1))\
                        or ((message.find(f'{ctx_author}\'s lootbox') > -1) and (message.find('You were about to open a nice lootbox') > -1))\
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
                    await ctx.send('Open detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            if bot_message.find('lootbox opened!') > -1:
                if bot_message.find('<:ruby:') > -1:
                    rubies_end = bot_message.find('<:ruby:') -1
                    rubies_start = bot_message.rfind('+', 0, rubies_end) + 1
                    rubies = bot_message[rubies_start:rubies_end]
                    if rubies.isnumeric():
                        rubies = user.rubies + int(rubies)
                        await user.update(rubies=rubies)
                        if user.rubies != rubies:
                            await ctx.send(strings.MSG_ERROR)
                    else:
                        await ctx.send(f'Something went wrong here, wanted to read ruby count, found this instead: {rubies}')
                await bot_answer.add_reaction(emojis.NAVI)
            # Ignore failed openings
            elif (bot_message.find('of this lootbox type') > -1) or (bot_message.find('what lootbox') > -1):
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore lootbox event
            elif (bot_message.find('You were about to open a nice lootbox') > -1):
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error message if wrong name
            elif bot_message.find('what are you doing??') > 1:
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

        except asyncio.TimeoutError as error:
            await ctx.send('Lootbox detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Lootbox detection error: {e}')
            return


# Initialization
def setup(bot):
    bot.add_cog(OpenCog(bot))