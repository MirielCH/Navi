# pets.py

import asyncio
from datetime import datetime, timedelta
from typing import Tuple

import discord
from discord.ext import commands

from database import reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class PetsCog(commands.Cog):
    """Cog that contains the pets detection commands"""
    def __init__(self, bot):
        self.bot = bot

    async def get_pet_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the pets adventure message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Pet detection: {message}')
                if ((message.find(f'{ctx.author.id}') > -1) and (message.find('you cannot send another pet to an adventure!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('what pet(s) are you trying to select?') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('is already in an adventure!') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('pet adventure(s) cancelled') > -1))\
                or ((message.find(f'{ctx.author.id}') > -1) and (message.find('is not in an adventure') > -1))\
                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):
                    correct_message = True
                else:
                    correct_message = False
            except:
                correct_message = False
            return m.author.id == settings.EPIC_RPG_ID and m.channel == ctx.channel and correct_message

        bot_answer = await self.bot.wait_for('message', check=epic_rpg_check, timeout = settings.TIMEOUT)
        bot_message = await functions.encode_message(bot_answer)
        return (bot_answer, bot_message)

    async def get_pet_list_message(self, ctx: commands.Context) -> Tuple[discord.Message, str]:
        """Waits for the pets list message in the channel and returns it if found."""
        def epic_rpg_check(m: discord.Message) -> bool:
            correct_message = False
            try:
                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                message = functions.encode_message_non_async(m)
                if settings.DEBUG_MODE: logs.logger.debug(f'Pet list detection: {message}')
                if (message.find(f'{ctx_author}\'s pets') > -1)\
                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                    or (message.find('This command is unlocked after the second `time travel`') > -1):
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
    @commands.command(aliases=('pets',))
    @commands.bot_has_permissions(send_messages=True, external_emojis=True, add_reactions=True, read_message_history=True)
    async def pet(self, ctx: commands.Context, *args: str) -> None:
        """Detects EPIC RPG pets messages and creates reminders"""
        prefix = ctx.prefix
        if prefix.lower() != 'rpg ': return
        if args:
            args = [arg.lower() for arg in args]
            arg1 = args[0]
            if arg1 in ('info','fusion','ascend'): return
            pet_action = pet_id = ''
            if len(args) >= 2:
                pet_action = args[1]
            if len(args) >= 3:
                pet_id = args[2].upper()
                if pet_id == 'EPIC': return
            if arg1 in ('adv', 'adventure'):
                if pet_action == 'cancel' and pet_id != '':
                    pet_ids = args[2:]
                    try:
                        try:
                            user: users.User = await users.get_user(ctx.author.id)
                        except exceptions.NoDataFoundError:
                            return
                        if not user.reminders_enabled or not user.alert_pets.enabled: return
                        task_status = self.bot.loop.create_task(self.get_pet_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await functions.encode_message(msg)
                                    if settings.DEBUG_MODE: logs.logger.debug(f'Pet adventure detection: {message}')
                                    if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'pet adventure(s) cancelled') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'is not in an adventure') > -1))\
                                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                    or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1)):
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
                                await ctx.send('Pet cancel detection timeout.')
                                return
                        if not task_status.done(): task_status.cancel()

                        # Check if pet adventure started overview, if yes, read the time and update/insert the reminder
                        if bot_message.find('pet adventure(s) cancelled') > -1:
                            for pet_id in pet_ids:
                                pet_id = pet_id.upper()
                                activity = f'pets-{pet_id}'
                                try:
                                    reminder: reminders.Reminder = (
                                        await reminders.get_user_reminder(ctx.author.id, activity)
                                    )
                                except:
                                    return
                                await reminder.delete()
                                if reminder.record_exists:
                                    logs.logger.error(
                                        f'{datetime.now()}: Had an error deleting the pet reminder with activity '
                                        f'{activity}.'
                                    )
                                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                                else:
                                    await bot_answer.add_reaction(emojis.NAVI)
                            return
                        # Ignore wrong ids
                        elif bot_message.find('is not in an adventure') > 1:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore error that pets are not unlocked yet
                        elif bot_message.find('unlocked after second') > 1:
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
                        await ctx.send('Pet cancel detection timeout.')
                        return
                    except Exception as e:
                        logs.logger.error(f'Pet cancel detection error: {e}')
                        return

                elif pet_action in ('find', 'learn', 'drill') and not pet_id == '':
                    if len(args) > 3: return
                    command = 'rpg pet adventure'
                    try:
                        try:
                            user: users.User = await users.get_user(ctx.author.id)
                        except exceptions.NoDataFoundError:
                            return
                        if not user.reminders_enabled or not user.alert_pets.enabled: return
                        pets_message = user.alert_pets.message.replace('%', command)
                        current_time = datetime.utcnow().replace(microsecond=0)
                        task_status = self.bot.loop.create_task(self.get_pet_message(ctx))
                        bot_message = None
                        message_history = await ctx.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                                try:
                                    ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                    message = await functions.encode_message(msg)
                                    if settings.DEBUG_MODE: logs.logger.debug(f'Pet adventure detection: {message}')
                                    if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet(s) are you trying to select?') > -1))\
                                    or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'is already in an adventure!') > -1))\
                                    or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                    or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                                    or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                    or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):
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
                                await ctx.send('Pet adventure detection timeout.')
                                return
                        if not task_status.done(): task_status.cancel()

                        # Check if pet adventure started overview, if yes, read the time and update/insert the reminder
                        if bot_message.find('Your pet has started an adventure and will be back') > -1:
                            timestring_start = bot_message.find('back in **') + 10
                            timestring_end = bot_message.find('**!', timestring_start)
                            timestring = bot_message[timestring_start:timestring_end]
                            time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                            bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                            time_elapsed = current_time - bot_answer_time
                            time_left = time_left-time_elapsed
                            reminder: reminders.Reminder = (
                                await reminders.insert_user_reminder(ctx.author.id, f'pets-{pet_id}', time_left,
                                                                     ctx.channel.id, pets_message)
                            )
                            if reminder.record_exists:
                                await bot_answer.add_reaction(emojis.NAVI)
                            else:
                                if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore error that max amount of pets is on adventures
                        elif bot_message.find('you cannot send another pet') > 1:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore error that ID is wrong
                        elif bot_message.find('what pet(s) are you trying to select?') > 1:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore error that pet is already on adventure
                        elif bot_message.find('is already in an adventure') > 1:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore time traveler instant pet return
                        elif bot_message.find('IT CAME BACK INSTANTLY!') > 1:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                            return
                        # Ignore error that pets are not unlocked yet
                        elif bot_message.find('unlocked after second') > 1:
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
                        await ctx.send('Pet adventure detection timeout.')
                        return
                    except Exception as e:
                        logs.logger.error(f'Pet adventure detection error: {e}')
                        return

            elif arg1 == 'tournament':
                try:
                    try:
                        user: users.User = await users.get_user(ctx.author.id)
                    except exceptions.NoDataFoundError:
                        return
                    if not user.reminders_enabled or not user.alert_pet_tournament.enabled: return
                    user_donor_tier = user.user_donor_tier if user.user_donor_tier <= 3 else 3
                    pet_tournament_message = user.alert_pet_tournament.message.format(event='pet tournament')
                    current_time = datetime.utcnow().replace(microsecond=0)
                    task_status = self.bot.loop.create_task(self.get_pet_message(ctx))
                    bot_message = None
                    message_history = await ctx.channel.history(limit=50).flatten()
                    for msg in message_history:
                        if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                            try:
                                ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                                message = await functions.encode_message(msg)
                                if settings.DEBUG_MODE: logs.logger.debug(f'Pet tournament detection: {message}')
                                if ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'you cannot send another pet to an adventure!') > -1))\
                                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'what pet(s) are you trying to select?') > -1))\
                                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'this pet is already in an adventure!') > -1))\
                                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                or (message.find('Your pet has started an adventure and will be back') > -1) or ((message.find('Your pet has started an...') > -1) and (message.find('IT CAME BACK INSTANTLY!!') > -1))\
                                or (message.find('This command is unlocked after the second `time travel`') > -1) or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                or (message.find('pet successfully sent to the pet tournament!') > -1) or (message.find('You cannot send another pet to the **pet tournament**!') > -1):
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
                            await ctx.send('Pet tournament detection timeout.')
                            return
                    if not task_status.done(): task_status.cancel()

                    # Check if pet tournament started, if yes, read the time and update/insert the reminder
                    if bot_message.find('pet successfully sent to the pet tournament!') > -1:
                        timestring_start = bot_message.find('is in **') + 8
                        timestring_end = bot_message.find('**,', timestring_start)
                        timestring = bot_message[timestring_start:timestring_end]
                        time_left = await functions.parse_timestring_to_timedelta(ctx, timestring.lower())
                        bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                        current_time = datetime.utcnow().replace(microsecond=0)
                        time_elapsed = current_time - bot_answer_time
                        time_left = time_left - time_elapsed
                        time_left = time_left + timedelta(minutes=1) #The event is somethings not perfectly on point, so I added a minute
                        reminder: reminders.Reminder = (
                            await reminders.insert_user_reminder(ctx.author.id, 'pet-tournament', time_left,
                                                                 ctx.channel.id, pet_tournament_message)
                        )
                        if reminder.record_exists:
                            await bot_answer.add_reaction(emojis.NAVI)
                        else:
                            if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return
                    # Ignore error that pet tournament is already active
                    elif bot_message.find('You cannot send another pet to the **pet tournament**!') > -1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return
                    # Ignore error that ID is wrong
                    elif bot_message.find('what pet are you trying to select?') > 1:
                        if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                        return
                    # Ignore error that pets are not unlocked yet
                    elif bot_message.find('unlocked after second') > 1:
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
                    await ctx.send('Pet tournament detection timeout.')
                    return
                except Exception as e:
                    logs.logger.error(f'Pet tournament detection error: {e}')
                    return
            else:
                args = ()
        if not args:
            try:
                try:
                    user: users.User = await users.get_user(ctx.author.id)
                except exceptions.NoDataFoundError:
                    return
                if not user.reminders_enabled or not user.alert_pets.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                task_status = self.bot.loop.create_task(self.get_pet_list_message(ctx))
                bot_message = None
                message_history = await ctx.channel.history(limit=50).flatten()
                for msg in message_history:
                    if (msg.author.id == settings.EPIC_RPG_ID) and (msg.created_at > ctx.message.created_at):
                        try:
                            ctx_author = str(ctx.author.name).encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                            message = await functions.encode_message(msg)
                            if settings.DEBUG_MODE: logs.logger.debug(f'Pet list detection: {message}')
                            if (message.find(f'{ctx_author}\'s pets') > -1)\
                                or ((message.find(ctx_author) > -1) and (message.find('Huh please don\'t spam') > -1)) or ((message.find(ctx_author) > -1) and (message.find('is now in the jail!') > -1))\
                                or ((message.find(f'{ctx.author.id}') > -1) and (message.find(f'end your previous command') > -1))\
                                or (message.find('This command is unlocked after the second `time travel`') > -1):
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
                        await ctx.send('Pet detection timeout.')
                        return
                if not task_status.done(): task_status.cancel()

                # Check if pets are on adventures
                action = ''
                found_pets = []
                if (bot_message.find('learning | ') > -1) or (bot_message.find('finding | ') > -1) or (bot_message.find('drilling | ') > -1):
                    while True:
                        if (bot_message.find('learning | ') > -1):
                            action = 'learning'
                        elif (bot_message.find('finding | ') > -1):
                            action = 'finding'
                        elif (bot_message.find('drilling | ') > -1):
                            action = 'drilling'
                        else:
                            break
                        action_start = bot_message.find(f'{action} | **')
                        timestring_start = action_start + len(action) + 5
                        timestring_end = bot_message.find('s**', timestring_start) + 1
                        timestring = bot_message[timestring_start:timestring_end]
                        if bot_message.find(', name=\'`ID: ', timestring_end) > -1:
                            id_start = bot_message.find('`ID: ', timestring_end) + 5
                        else:
                            id_start = bot_message.rfind('`ID: ', 0, timestring_end) + 5
                        id_end = bot_message.find('`', id_start)
                        id = bot_message[id_start:id_end]
                        bot_message_old = bot_message
                        bot_message = bot_message_old[:action_start] + bot_message_old[timestring_start:]
                        found_pets.append([id, timestring.lower()])

                    for pet in found_pets:
                        pet_id = pet[0]
                        pet_timestring = pet[1]
                        time_left = await functions.parse_timestring_to_timedelta(ctx, pet_timestring)
                        bot_answer_time = bot_answer.created_at.replace(microsecond=0)
                        time_elapsed = current_time - bot_answer_time
                        time_left = time_left - time_elapsed
                        pets_message = user.alert_pets.message.replace('$', pet_id)
                        reminder: reminders.Reminder = (
                            await reminders.insert_user_reminder(ctx.author.id, f'pets-{pet_id}', time_left,
                                                                 ctx.channel.id, pets_message)
                        )
                        if not reminder.record_exists:
                            await ctx.send(strings.MSG_ERROR)
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
                # Ignore error that pets are not unlocked yet
                elif bot_message.find('unlocked after second') > 1:
                    if settings.DEBUG_MODE: await bot_answer.add_reaction(emojis.CROSS)
                    return
            except asyncio.TimeoutError as error:
                await ctx.send('Pet detection timeout.')
            except Exception as e:
                logs.logger.error(f'Pet detection error: {e}')
                return

# Initialization
def setup(bot):
    bot.add_cog(PetsCog(bot))