# inventory.py

import asyncio
from typing import Tuple

import discord
from discord.ext import commands

from database import users
from resources import emojis, exceptions, functions, logs, settings, strings


class InventoryCog(commands.Cog):
    """Cog that contains the inventory detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_inventory_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the inventory message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Open detection: {message}')
                if  (message.find(f'{ctx_author}\'s inventory') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
    @commands.command(aliases=('i','inv',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def inventory(self, ctx: commands.Context, *args: tuple) -> None:

        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if args:
            if not args[0].find(f'{ctx.author.id}') > -1: return
        if ctx.message.mentions:
            if ctx.message.mentions[0].id != ctx.author.id:
                return
        try:
            user: users.User = await users.get_user(ctx.author.id)
        except exceptions.NoDataFoundError:
            return
        if not user.reminders_enabled or not user.ruby_counter_enabled: return
        try:
            task_status = self.bot.loop.create_task(self.get_inventory_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Inventory detection: {message}')
                        if  (message.find(f'{ctx_author}\'s inventory') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
                        or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
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
                    await ctx.send('Inventory detection timeout.')
                    return

            if bot_message.find(f'\'s inventory') > -1:
                if bot_message.find('**ruby**:') > -1:
                    rubies_start = bot_message.find('**ruby**:') + 10
                    rubies_end = bot_message.find(f'\\', rubies_start)
                    rubies_end_bottom = bot_message.find(f'\'', rubies_start)
                    rubies = bot_message[rubies_start:rubies_end]
                    rubies_bottom = bot_message[rubies_start:rubies_end_bottom]
                    if rubies.isnumeric():
                        rubies = int(rubies)
                    elif rubies_bottom.isnumeric():
                        rubies = int(rubies_bottom)
                    else:
                        await ctx.send(
                            f'Something went wrong here, wanted to read ruby count, found this instead:\n'
                            f'Mid embed: {rubies}\n'
                            f'Bottom: {rubies_bottom}'
                        )
                        return
                    await user.update(rubies=int(rubies))
                    if user.rubies == int(rubies):
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
                        await ctx.send(strings.MSG_ERROR)
                else:
                    await user.update(rubies=0)
                    if user.rubies == 0:
                        await bot_answer.add_reaction(emojis.NAVI)
                    else:
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
        except asyncio.TimeoutError:
            await ctx.send('Inventory detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Inventory detection error: {e}')
            return

# Initialization
def setup(bot):
    bot.add_cog(InventoryCog(bot))