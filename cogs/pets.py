# pets.py

from datetime import datetime, timedelta
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
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if not message.embeds:
            message_content = message.content
            # Single pet adventure
            search_strings = [
                'your pet has started an adventure and will be back', #English 1 pet
                'pets have started an adventure!', #English multiple pets
                'tu mascota empezó una aventura y volverá', #Spanish 1 pet
                'tus mascotas han comenzado una aventura!', #Spanish multiple pets
                'seu pet começou uma aventura e voltará', #Portuguese 1 pet
                'seus pets começaram uma aventura!', #Portuguese multiple pets
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                interaction = await functions.get_interaction(message)
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+pets?\s+(?:adv\b|adventure\b)\s+(?:find\b|learn\b|drill\b)"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for pet adventure message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                if not user_settings.pet_tip_read:
                    command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                    pet_message = (
                        f"**{user.name}**, please use {command_pets_list} "
                        f'or `rpg pets` to create pet reminders.'
                    )
                    pet_message = (
                        f'{pet_message}\n\n'
                        f'Tip: This is done fastest by sorting pets by their status:\n'
                        f"{emojis.BP} {command_pets_list} `sort: status` "
                        f'(click through all pages with active pets)\n'
                        f'{emojis.BP} `rpg pets status`'
                    ) # Message split up like this because I'm unsure if I want to always send the first part
                    await user_settings.update(pet_tip_read=True)
                    await message.reply(pet_message)
                search_strings = [
                    'the following pets are back instantly', #English
                    'las siguientes mascotas están de vuelta instantaneamente', #Spanish
                    'os seguintes pets voltaram instantaneamente', #Portuguese
                ]
                command_pets_claim = await functions.get_slash_command(user_settings, 'pets claim')
                if any(search_string in message_content.lower() for search_string in search_strings):
                    await message.reply(f"➜ {command_pets_claim}")
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.SKILL_TIME_TRAVELER)
                if 'voidog' in message.content.lower():
                    await message.reply(f"➜ {command_pets_claim}")
                    if user_settings.reactions_enabled:
                        await message.add_reaction(emojis.SKILL_TIME_TRAVELER)
                        await message.add_reaction(emojis.VOIDOG)
                if interaction is not None: return
                search_strings = [
                    'pets have started an adventure!', #English
                    'tus mascotas han comenzado una aventura!', #Spanish
                    'seus pets começaram uma aventura!', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings): return
                arguments = user_command_message.content.split()
                pet_id = arguments[-1].upper()
                if pet_id == 'EPIC': return
                current_time = datetime.utcnow().replace(microsecond=0)
                search_patterns = [
                    r'will be back in \*\*(.+?)\*\*', #English
                    r'volverá en \*\*(.+?)\*\*', #Spanish
                    r'voltará em \*\*(.+?)\*\*', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in pet adventure message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}','')
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'pet adventure(s) cancelled', #English
                'mascota(s) cancelada(s)', #Spanish
                'pets cancelada(s)', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is not None:
                    command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                    await message.reply(
                        f"**{user.name}**, please use {command_pets_list}"
                        f' to update your pet reminders.'
                    )
                    return
                user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+pets?\s+(?:adv\b|adventure\b)\s+cancel\b"
                        )
                    )
                if user_command_message is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for pet cancel message.', message)
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
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a pet ID for pet cancel message.', message)
                    return
                for pet_id in pet_ids:
                    activity = f'pets-{pet_id}'
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, activity)
                    except exceptions.NoDataFoundError:
                        continue
                    await reminder.delete()
                    if reminder.record_exists:
                        logs.logger.error(
                            f'{datetime.utcnow()}: Had an error deleting the pet reminder with activity '
                            f'{activity}.'
                        )
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            search_strings = [
                'it came back instantly!!', #English
                'volvio al instante!!', #Spanish
                'voltou instantaneamente!!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+pets?\s+(?:adv\b|adventure\b)\s+(?:find\b|learn\b|drill\b)"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for the pet time travel reaction.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                command_pets_claim = await functions.get_slash_command(user_settings, 'pets claim')
                await message.reply(f"➜ {command_pets_claim}")
                if user_settings.reactions_enabled: await message.add_reaction(emojis.SKILL_TIME_TRAVELER)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_description = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.description: message_description = str(embed.description)

            # Pet list
            search_strings = [
                'pets can collect items and coins, more information', #English
                'las mascotas puedes recoger items y coins, más información', #Spanish
                'pets podem coletar itens e coins, mais informações', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                pet_names_emojis = {
                    'cat': emojis.PET_CAT,
                    'voidog': emojis.VOIDOG,
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
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet list message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(
                        f'User not found in pet list message.',
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
                    pet_id_match = re.search(r'`ID: (.+?)`', field.name)
                    pet_emoji = ''
                    for pet, emoji in pet_names_emojis.items():
                        if pet in field.name.lower():
                            pet_emoji = emoji
                            break
                    pet_action_timestring_match = re.search(r'Status__:\*\* (.+?) \| \*\*(.+?)\*\*', field.value)
                    if not pet_id_match: continue
                    pet_id = pet_id_match.group(1)
                    if not pet_action_timestring_match:
                        try:
                            reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, f'pets-{pet_id}')
                            await reminder.delete()
                        except exceptions.NoDataFoundError:
                            pass
                        continue
                    pet_action = pet_action_timestring_match.group(1)
                    pet_actions = [
                        'finding', #English
                        'learning',
                        'drilling',
                        'buscando', #Spanish
                        'aprendiendo',
                        'perforando',
                        'procurando', #Portuguese
                        'aprendendo',
                        'perfuração',
                    ]
                    if pet_action not in pet_actions: continue
                    pet_timestring = pet_action_timestring_match.group(2)
                    time_left = await functions.parse_timestring_to_timedelta(pet_timestring.lower())
                    time_left = time_left - time_elapsed
                    if time_left < timedelta(0): return # This can happen because the timeout edits pets list one last time
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