# pets.py

from datetime import datetime
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, logs, settings, strings


class PetsCog(commands.Cog):
    """Cog that contains the pets detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if not message.embeds:
            message_content = message.content
            # Single pet adventure
            if ('your pet has started an adventure and will be back' in message_content.lower()
                or 'pets have started an adventure!' in message_content.lower()):
                interaction = await functions.get_interaction(message)
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().replace(' ','').startswith('rpgpet') and ' adv' in msg.content.lower()
                                and not msg.author.bot):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for pet adventure message.',
                            message
                        )
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                if not user_settings.pet_tip_read:
                    pet_message = f'**{user.name}**, please use `/pets list` or `rpg pets` to create pet reminders.'
                    pet_message = (
                        f'{pet_message}\n\n'
                        f'Tip: This is done fastest by sorting pets by their status:\n'
                        f'{emojis.BP} `/pets list sort: status` (click through all pages with active pets)\n'
                        f'{emojis.BP} `rpg pets status`'
                    ) # Message split up like this because I'm unsure if I want to always send the first part
                    await user_settings.update(pet_tip_read=True)
                    await message.reply(pet_message)
                if 'for some completely unknown reason, the following pets are back instantly' in message_content.lower():
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.SKILL_TIME_TRAVELER)
                if interaction is not None or 'pets have started an adventure!' in message_content.lower(): return
                arguments = user_command_message.content.split()
                pet_id = arguments[-1].upper()
                if pet_id == 'EPIC': return
                current_time = datetime.utcnow().replace(microsecond=0)
                timestring = re.search("will be back in \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}','')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            if 'pet adventure(s) cancelled' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is not None:
                    await message.reply(
                        f'**{user.name}**, please use `/pets list` to update your pet reminders.'
                    )
                    return
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if (msg.content.lower().replace(' ','').startswith('rpgpet') and ' cancel ' in msg.content.lower()
                            and not msg.author.bot):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a command for pet cancel message.',
                        message
                    )
                    return
                user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                arguments = user_command_message.content.split()
                pet_ids = []
                for arg in arguments:
                    if arg not in ('rpg','pets','pet','adventure','adv','cancel'): pet_ids.append(arg.upper())
                if not pet_ids:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a pet ID for pet cancel message.',
                        message
                    )
                    return
                for pet_id in pet_ids:
                    activity = f'pets-{pet_id}'
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, activity)
                    except:
                        continue
                    await reminder.delete()
                    if reminder.record_exists:
                        logs.logger.error(
                            f'{datetime.now()}: Had an error deleting the pet reminder with activity '
                            f'{activity}.'
                        )
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            if 'it came back instantly!!' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().replace(' ','').startswith('rpgpet') and ' adv' in msg.content.lower()
                                and not msg.author.bot):
                                user = msg.author
                                break
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the pet time travel reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.alert_pets.enabled
                    or not user_settings.reactions_enabled):
                    return
                await message.add_reaction(emojis.SKILL_TIME_TRAVELER)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_description = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.description: message_description = str(embed.description)

            # Pet list
            if 'pets can collect items and coins, more information' in message_description.lower():
                pet_names_emojis = {
                    'cat': emojis.PET_CAT,
                    'dog': emojis.PET_DOG,
                    'dragon': emojis.PET_DRAGON,
                    'golden bunny': emojis.PET_GOLDEN_BUNNY,
                    'hamster': emojis.PET_HAMSTER,
                    'pumpkin bat': emojis.PET_PUMPKIN_BAT,
                    'pink fish': emojis.PET_PINK_FISH,
                    'snowball': emojis.PET_SNOWBALL,
                    'pony': emojis.PET_PONY,
                    'panda': emojis.PET_PANDA,
                }
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s pets", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in pet list message: {message_author}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in pet list message: {message_author}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                reminder_created = False
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                for field in embed.fields:
                    try:
                        pet_id_search = re.search('`ID: (.+?)`', field.name)
                        pet_emoji = ''
                        for pet, emoji in pet_names_emojis.items():
                            if pet in field.name.lower():
                                pet_emoji = emoji
                                break
                        pet_action_timestring_search = re.search('Status__:\*\* (.+?) \| \*\*(.+?)\*\*', field.value)
                        if pet_id_search is None: continue
                        pet_id = pet_id_search.group(1)
                        if pet_action_timestring_search is None:
                            try:
                                reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, f'pets-{pet_id}')
                                await reminder.delete()
                            except exceptions.NoDataFoundError:
                                pass
                            continue
                        pet_action = pet_action_timestring_search.group(1)
                        if pet_action not in ('learning','finding','drilling'): continue
                        pet_timestring = pet_action_timestring_search.group(2)
                        time_left = await functions.parse_timestring_to_timedelta(pet_timestring.lower())
                        time_left = time_left - time_elapsed
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'Pet id, action or timestring not found in pet list message: {message.embeds[0].fields}',
                            message
                        )
                        return

                    reminder_created = True
                    reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}',pet_emoji)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                             message.channel.id, reminder_message)
                    )
                if reminder_created and user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

# Initialization
def setup(bot):
    bot.add_cog(PetsCog(bot))