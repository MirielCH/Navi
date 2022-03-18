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
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if not message.embeds:
            message_content = message.content
            # Single pet adventure
            if 'your pet has started an adventure and will be back' in message_content.lower():
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if (msg.content.lower().startswith('rpg pet') and ' adv' in msg.content.lower()
                            and not msg.author.bot):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error('Couldn\'t find a command for pet adventure message.')
                    return
                user = user_command_message.author
                arguments = user_command_message.content.split()
                pet_id = arguments[-1].upper()
                if pet_id == 'EPIC': return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                timestring = re.search("will be back in \*\*(.+?)\*\*", message_content).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
                bot_answer_time = message.created_at.replace(microsecond=0)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}','')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

            if 'pet adventure(s) cancelled' in message_content.lower():
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if (msg.content.lower().startswith('rpg pet') and ' cancel ' in msg.content.lower()
                            and not msg.author.bot):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error('Couldn\'t find a command for pet cancel message.')
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
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error('Couldn\'t find a pet ID for pet cancel message.')
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
                await message.add_reaction(emojis.NAVI)

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
                user_id = user_name = user = None
                try:
                    user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                except:
                    try:
                        user_name = re.search("^(.+?)'s pets", message_author).group(1)
                        user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    except Exception as error:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error(f'User not found in pet list message: {message.embeds[0].fields}')
                        return
                if user_id is not None:
                    user = await message.guild.fetch_member(user_id)
                else:
                    for member in message.guild.members:
                        member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        if member_name == user_name:
                            user = member
                            break
                if user is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(f'User not found in pet list message: {message.embeds[0].fields}')
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                reminder_created = False
                bot_answer_time = message.created_at.replace(microsecond=0)
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
                        if pet_id_search is None or pet_action_timestring_search is None: continue
                        pet_id = pet_id_search.group(1)
                        pet_action = pet_action_timestring_search.group(1)
                        if pet_action not in ('learning','finding','drilling'): continue
                        pet_timestring = pet_action_timestring_search.group(2)
                        time_left = await functions.parse_timestring_to_timedelta(pet_timestring.lower())
                        time_left = time_left - time_elapsed
                    except Exception as error:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error(f'Pet id, action or timestring not found in pet list message: {message.embeds[0].fields}')
                        return

                    reminder_created = True
                    reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}',pet_emoji)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                             message.channel.id, reminder_message)
                    )
                if reminder_created: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(PetsCog(bot))