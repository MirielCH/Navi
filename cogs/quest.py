# quest.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import cooldowns, reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class QuestCog(commands.Cog):
    """Cog that contains the quest detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_quest_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the quest and quest message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Quest detection: {message}')
                if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('WAVE #1') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('epic quest cancelled') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you did not accept the quest') > -1))\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find(f'If you don\'t want this quest anymore') > -1))\
                or ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('Are you ready to start the EPIC quest') > -1))\
                or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or (message.find('You need a **special horse** to do this') > -1):
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
    @commands.command(aliases=('quest',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def epic(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG quest and epic quest messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        command = 'rpg quest'
        if args:
            arg = args[0].lower()
            invoked = ctx.invoked_with
            invoked = invoked.lower()
            if invoked == 'epic':
                if arg == 'quest':
                    command = 'rpg epic quest'
                else:
                    return
            else:
                if arg == 'quit': return
        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.bot_enabled or not user.alert_quest.enabled: return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            quest_message = user.alert_quest.message.replace('%',command)
            current_time = datetime.utcnow().replace(microsecond=0)
            epic_quest = False
            quest_declined = None
            task_status = self.bot.loop.create_task(self.get_quest_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Quest detection: {message}')
                        if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('WAVE #1') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('epic quest cancelled') > -1))\
                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you did not accept the quest') > -1))\
                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                        or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find(f'If you don\'t want this quest anymore') > -1))\
                        or ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('Are you ready to start the EPIC quest') > -1))\
                        or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                        or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                        or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                        or (message.find('You need a **special horse** to do this') > -1):
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
                    await ctx.send('Quest detection timeout.')
                    return
            if not task_status.done(): task_status.cancel()

            # Check what quest it is and if normal quest if the user accepts or denies the quest (different cooldowns)
            if (bot_message.find('Are you looking for a quest?') > -1) or (bot_message.find('Are you ready to start the EPIC quest') > -1):
                task_status = self.bot.loop.create_task(self.get_quest_message(ctx))
                bot_first_answer = bot_answer
                bot_message = None
                message_history = await ctx.channel.history(limit=50).flatten()
                for msg in message_history:
                    if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > bot_first_answer.created_at):
                        try:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message = await functions.encode_message(msg)
                            if settings.DEBUG_MODE: logs.logger.debug(f'Quest detection: {message}')
                            if  ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('WAVE #1') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('epic quest cancelled') > -1))\
                            or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Are you looking for a quest?') > -1)) or ((message.find(f'{ctx.author.id}') > -1) and (message.find('you did not accept the quest') > -1))\
                            or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find('Completed!') > -1)) or (message.find(f'**{ctx_author}** got a **new quest**!') > -1)\
                            or ((message.find(f'{ctx_author}\'s quest') > -1) and (message.find(f'If you don\'t want this quest anymore') > -1))\
                            or ((message.find(f'{ctx_author}\'s epic quest') > -1) and (message.find('Are you ready to start the EPIC quest') > -1))\
                            or ((message.find(f'{ctx_author}\'s cooldown') > -1) and (message.find('You have already claimed a quest') > -1)) or (message.find('You cannot do this if you have a pending quest!') > -1)\
                            or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                            or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                            or (message.find('You need a **special horse** to do this') > -1):
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
                        await ctx.send('Quest detection timeout.')
                        return
                if not task_status.done(): task_status.cancel()

                if bot_message.find('you did not accept the quest') > -1:
                    quest_declined = True
                elif bot_message.find('got a **new quest**!') > -1:
                    quest_declined = False
                elif bot_message.find('WAVE #1') > -1:
                    epic_quest = True
                else:
                    if settings.DEBUG_MODE: await ctx.send('I could not find out if the quest was accepted or declined.')
                    return
            # Check if it found a cooldown embed, if yes, read the time and update/insert the reminder if necessary
            elif bot_message.find(f'\'s cooldown') > 1:
                timestring_start = bot_message.find('wait at least **') + 16
                timestring_end = bot_message.find('**...', timestring_start)
                timestring = bot_message[timestring_start:timestring_end]
                time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left-time_elapsed
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(ctx.author.id, 'quest', time_left,
                                                         ctx.channel.id, quest_message)
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
            # Ignore quest cancellation as it does not reset the cooldown
            elif bot_message.find('epic quest cancelled') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when trying to do epic quest with active quest
            elif bot_message.find(f'You cannot do this if you have a pending quest!') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore active quest
            elif bot_message.find(f'If you don\'t want this quest anymore') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore completed quest
            elif bot_message.find(f'Completed!') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore trying epic quest without a special horse
            elif bot_message.find('You need a **special horse** to do this') > -1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return
            # Ignore error when another command is active
            elif bot_message.find('end your previous command') > 1:
                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                return

            # Calculate cooldown
            cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest')
            if not epic_quest and quest_declined is None:
                logs.logger.error(f'Quest detection error: Neither quest_declined nor epic_quest had a value that allowed me to determine what the user did. epic_quest: {epic_quest}, quest_declined: {quest_declined}')
                return
            if epic_quest:
                cooldown_seconds = cooldown.actual_cooldown()
            else:
                cooldown_seconds = 3600 if quest_declined else cooldown.actual_cooldown()
            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            if cooldown.donor_affected:
                time_left_seconds = (cooldown.actual_cooldown()
                                     * settings.DONOR_COOLDOWNS[user_donor_tier]
                                     - time_elapsed.total_seconds())
            else:
                time_left_seconds = cooldown-time_elapsed.total_seconds()
            time_left = timedelta(seconds=time_left_seconds)

            # Save reminder to database
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(ctx.author.id, 'quest', time_left,
                                                     ctx.channel.id, quest_message)
            )

            # Add reaction
            if reminder.record_exists:
                await bot_answer.add_reaction(emojis.NAVI)
            else:
                if settings.DEBUG_MODE: await ctx.send(strings.MSG_ERROR)
        except asyncio.TimeoutError:
            await ctx.send('Quest detection timeout.')
            return
        except Exception as e:
            logs.logger.error(f'Quest detection error: {e}')
            return

# Initialization
def setup(bot):
    bot.add_cog(QuestCog(bot))