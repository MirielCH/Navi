# cooldowns.py

import asyncio
from typing import Tuple

import discord
from discord.ext import commands
from datetime import datetime

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class CooldownsCog(commands.Cog):
    """Cog that contains the cooldowns detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_cooldowns_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the cooldowns message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Cooldown detection: {message}')
                if  (message.find(f'{ctx_author}\'s cooldowns') > -1) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
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
    @commands.command(aliases=('cd','cds','cooldowns',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def cooldown(self, ctx: commands.Context, *args: tuple) -> None:
        """Detects EPIC RPG cooldown messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if args:
            args = [arg.lower() for arg in args]
            if args[0] != 'max' and not (args[0].find(ctx.author.id) > -1): return
        try:
            try:
                user: users.User = await users.get_user(ctx.author.id)
            except exceptions.NoDataFoundError:
                return
            if not user.reminders_enabled: return
            if (not user.alert_adventure.enabled and not user.alert_arena.enabled and not user.alert_daily.enabled
                and not user.alert_duel.enabled and not user.alert_dungeon_miniboss.enabled
                and not user.alert_farm.enabled and not user.alert_horse_breed.enabled and not user.alert_hunt.enabled
                and not user.alert_lootbox.enabled and not user.alert_quest.enabled and not user.alert_training.enabled
                and not user.alert_work.enabled and not user.alert_vote.enabled and not user.alert_weekly.enabled):
                return
            user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
            current_time = datetime.utcnow().replace(microsecond=0)
            task_status = self.bot.loop.create_task(self.get_cooldowns_message(ctx))
            bot_message = None
            message_history = await ctx.channel.history(limit=50).flatten()
            for msg in message_history:
                if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                    try:
                        ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        message = await functions.encode_message(msg)
                        if settings.DEBUG_MODE: logs.logger.debug(f'Cooldowns detection: {message}')
                        if  (message.find(f'{ctx_author}\'s cooldowns') > -1) or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1))\
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
                    await ctx.send('Cooldowns detection timeout.')
                    return

            # Check if cooldown list, if yes, extract all the timestrings
            if bot_message.find(f'\'s cooldowns') > 1:
                cooldowns = []
                if user.alert_daily.enabled:
                    if bot_message.find('Daily`** (**') > -1:
                        daily_start = bot_message.find('Daily`** (**') + 12
                        daily_end = bot_message.find('s**', daily_start) + 1
                        daily = bot_message[daily_start:daily_end]
                        daily_message = user.alert_daily.message.replace('%','rpg daily')
                        cooldowns.append(['daily', daily.lower(), daily_message])
                if user.alert_weekly.enabled:
                    if bot_message.find('Weekly`** (**') > -1:
                        weekly_start = bot_message.find('Weekly`** (**') + 13
                        weekly_end = bot_message.find('s**', weekly_start) + 1
                        weekly = bot_message[weekly_start:weekly_end]
                        weekly_message = user.alert_weekly.message.replace('%','rpg weekly')
                        cooldowns.append(['weekly', weekly.lower(), weekly_message])
                if user.alert_lootbox.enabled:
                    if bot_message.find('Lootbox`** (**') > -1:
                        lb_start = bot_message.find('Lootbox`** (**') + 14
                        lb_end = bot_message.find('s**', lb_start) + 1
                        lootbox = bot_message[lb_start:lb_end]
                        lootbox_message = user.alert_lootbox.message.replace('%','rpg buy lootbox')
                        cooldowns.append(['lootbox', lootbox.lower(), lootbox_message])
                if user.alert_adventure.enabled:
                    if bot_message.find('Adventure`** (**') > -1:
                        adv_start = bot_message.find('Adventure`** (**') + 16
                        adv_end = bot_message.find('s**', adv_start) + 1
                        adventure = bot_message[adv_start:adv_end]
                        adv_message = user.alert_adventure.message.replace('%','rpg adventure')
                        cooldowns.append(['adventure', adventure.lower(), adv_message])
                    elif bot_message.find('Adventure hardmode`** (**') > -1:
                        adv_start = bot_message.find('Adventure hardmode`** (**') + 25
                        adv_end = bot_message.find('s**', adv_start) + 1
                        adventure = bot_message[adv_start:adv_end]
                        adv_message = user.alert_adventure.message.replace('%','rpg adventure hardmode')
                        cooldowns.append(['adventure', adventure.lower(), adv_message])
                if user.alert_training.enabled:
                    if bot_message.find('Training`** (**') > -1:
                        tr_start = bot_message.find('Training`** (**') + 15
                        tr_end = bot_message.find('s**', tr_start) + 1
                        training = bot_message[tr_start:tr_end]
                        tr_message = user.alert_training.message.replace('%','rpg training')
                        cooldowns.append(['training', training.lower(), tr_message])
                    elif bot_message.find('Ultraining`** (**') > -1:
                        tr_start = bot_message.find('Ultraining`** (**') + 17
                        tr_end = bot_message.find('s**', tr_start) + 1
                        training = bot_message[tr_start:tr_end]
                        tr_message = user.alert_training.message.replace('%','rpg ultraining')
                        cooldowns.append(['training', training.lower(), tr_message])
                if user.alert_quest.enabled:
                    if bot_message.find('quest`** (**') > -1:
                        quest_start = bot_message.find('quest`** (**') + 12
                        quest_end = bot_message.find('s**', quest_start) + 1
                        quest = bot_message[quest_start:quest_end]
                        quest_message = user.alert_quest.message.replace('%','rpg quest')
                        cooldowns.append(['quest', quest.lower(), quest_message])
                if user.alert_duel.enabled:
                    if bot_message.find('Duel`** (**') > -1:
                        duel_start = bot_message.find('Duel`** (**') + 11
                        duel_end = bot_message.find('s**', duel_start) + 1
                        duel = bot_message[duel_start:duel_end]
                        duel_message = user.alert_duel.message.replace('%','rpg duel')
                        cooldowns.append(['duel', duel.lower(), duel_message])
                if user.alert_arena.enabled:
                    if bot_message.find('rena`** (**') > -1:
                        arena_start = bot_message.find('rena`** (**') + 11
                        arena_end = bot_message.find('s**', arena_start) + 1
                        arena = bot_message[arena_start:arena_end]
                        arena_message = user.alert_arena.message.replace('%','rpg arena')
                        cooldowns.append(['arena', arena.lower(), arena_message])
                if user.alert_dungeon_miniboss.enabled:
                    if bot_message.find('boss`** (**') > -1:
                        dungmb_start = bot_message.find('boss`** (**') + 11
                        dungmb_end = bot_message.find('s**', dungmb_start) + 1
                        dungmb = bot_message[dungmb_start:dungmb_end]
                        dungmb_message = user.alert_dungeon_miniboss.message.replace('%','rpg dungeon / miniboss')
                        cooldowns.append(['dungmb', dungmb.lower(), dungmb_message])
                if user.alert_horse_breed.enabled:
                    if bot_message.find('race`** (**') > -1:
                        horse_start = bot_message.find('race`** (**') + 11
                        horse_end = bot_message.find('s**', horse_start) + 1
                        horse = bot_message[horse_start:horse_end]
                        horse_message = user.alert_horse_breed.message.replace('%','rpg horse breed / race')
                        cooldowns.append(['horse', horse.lower(), horse_message])
                if user.alert_vote.enabled:
                    if bot_message.find('Vote`** (**') > -1:
                        vote_start = bot_message.find('Vote`** (**') + 11
                        vote_end = bot_message.find('s**', vote_start) + 1
                        vote = bot_message[vote_start:vote_end]
                        vote_message = user.alert_vote.message.replace('%','rpg vote')
                        cooldowns.append(['vote', vote.lower(), vote_message])
                if user.alert_farm.enabled:
                    if bot_message.find('Farm`** (**') > -1:
                        farm_start = bot_message.find('Farm`** (**') + 11
                        farm_end = bot_message.find('s**', farm_start) + 1
                        farm = bot_message[farm_start:farm_end]
                        farm_message = user.alert_farm.message.replace('%','rpg farm')
                        cooldowns.append(['farm', farm.lower(), farm_message])
                for cooldown in cooldowns:
                    activity = cooldown[0]
                    timestring = cooldown[1]
                    message = cooldown[2]
                    time_left = await functions.parse_timestring_to_timedelta(ctx, timestring)
                    bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left - time_elapsed
                    if time_left.total_seconds() > 0:
                        reminder: reminders.Reminder = reminders.insert_user_reminder(ctx.author.id, activity, time_left,
                                                                                      ctx.channel.id, message)
                        if not reminder.record_exists:
                            await ctx.send(strings.MSG_ERROR)
                            return
                await bot_answer.add_reaction(emojis.NAVI)

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
            await ctx.send('Cooldowns detection timeout.')
        except Exception as e:
            logs.logger.error(f'Cooldowns detection error: {e}')

# Initialization
def setup(bot):
    bot.add_cog(CooldownsCog(bot))