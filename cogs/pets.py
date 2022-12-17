# pets.py

import asyncio
from datetime import datetime, timedelta
from math import ceil
import re
import roman

import discord
from discord.ext import commands

from database import errors, pets, reminders, users
from resources import emojis, exceptions, functions, logs, regex, settings, strings


# User ID: (Message ID of epic pets list, message ID of corresponding Navi message showing pages)
pets_list_update_messages_ids = {}


class PetsCog(commands.Cog):
    """Cog that contains the pets detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

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
                user = await functions.get_interaction_user(message)
                user_command_message = None
                returned_pet_ids = []
                slash_command = True if user is not None else False
                if not slash_command:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_PETS_ADVENTURE_START
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
                if slash_command:
                    pet_message = (
                        f"**{user.name}**, please use {command_pets_list} `sort: status` "
                        f'or `rpg pets status` to create pet reminders when using slash commands.'
                    )
                    if not user_settings.pet_tip_read:
                        command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                        pet_message = (
                            f"{pet_message}\n\n"
                            f'If you don\'t want to do this, please flip through all pet pages to register your '
                            f'pets and then use **only** `rpg` commands in the future for sending and fusing pets.'
                        )
                        await user_settings.update(pet_tip_read=True)
                    await message.reply(pet_message)

                search_strings = [
                    'the following pets are back instantly', #English
                    'las siguientes mascotas están de vuelta instantaneamente', #Spanish
                    'os seguintes pets voltaram instantaneamente', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings):
                    if user_settings.reactions_enabled:
                        asyncio.ensure_future(message.add_reaction(emojis.SKILL_TIME_TRAVELER))
                        returned_pet_ids_match = re.search(r'instantly: (.+?)$')
                        if not returned_pet_ids_match:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find pet ids if returned pets in pet adv message.', message)
                            return
                        returned_pet_ids = returned_pet_ids_match.group(1).replace('`', '').split(', ')
                    await message.reply(f"➜ {strings.SLASH_COMMANDS['pets claim']}")
                if 'voidog' in message.content.lower():
                    await message.reply(f"➜ {strings.SLASH_COMMANDS['pets claim']}")
                    if user_settings.reactions_enabled:
                        asyncio.ensure_future(message.add_reaction(emojis.SKILL_TIME_TRAVELER))
                        asyncio.ensure_future(message.add_reaction(emojis.PET_VOIDOG))

                if not slash_command:
                    if -1 in user_settings.outdated_pet_pages:
                        await functions.send_outdated_pet_pages_message(user_settings, message)
                        return
                    sent_pet_ids_match = re.search(
                        r'\bpets?\s+(?:\badv\b|\badventure\b)\s+(?:\bfind\b|\blearn\b|\bdrill\b)\s+(.+?)$',
                        user_command_message.content.lower()
                    )
                    if not sent_pet_ids_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find sent pet ids in the pet adv user command message.', message)
                        return
                    sent_pet_ids = re.split(r'\s+', sent_pet_ids_match.group(1))
                    for pet_id in returned_pet_ids:
                        if pet_id in sent_pet_ids: sent_pet_ids.remove(pet_id)
                    if sent_pet_ids[0] == 'epic':
                        epic_pets = await pets.get_pets(user.id, skills=['epic',])
                        for pet in epic_pets:
                            page = ceil(pet.pet_id / 6)
                            if page in user_settings.outdated_pet_pages:
                                await functions.send_outdated_pet_pages_message(user_settings, message)
                                return
                        for pet in epic_pets:
                            if pet.pet_id_str not in returned_pet_ids:
                                try:
                                    reminder: reminders.Reminder = await reminders.get_user_reminder(
                                        user.id, f'pets-{pet.pet_id_str}'
                                    )
                                except exceptions.NoDataFoundError:
                                    reminder: reminders.Reminder = (
                                        await reminders.insert_user_reminder(user.id, f'pets-{pet.pet_id_str}',
                                                                            pet.get_reminder_time(), message.channel.id,
                                                                            reminder_message)
                                    )
                    else:
                        for pet_id in sent_pet_ids:
                            pet_id = await functions.convert_pet_id_to_int(pet_id)
                            page = ceil(pet_id / 6)
                            if page in user_settings.outdated_pet_pages:
                                await functions.send_outdated_pet_pages_message(user_settings, message)
                                return
                        for pet_id in sent_pet_ids:
                            try:
                                pet: pets.Pet = await pets.get_pet(user.id, await functions.convert_pet_id_to_int(pet_id))
                            except exceptions.NoDataFoundError:
                                await user_settings.update(outdated_pet_pages=[-1,])
                                await functions.send_outdated_pet_pages_message(user_settings, message)
                                return
                            reminder: reminders.Reminder = (
                                await reminders.insert_user_reminder(user.id, f'pets-{pet.pet_id}',
                                                                     pet.get_reminder_time(), message.channel.id,
                                                                     reminder_message)
                            )

            search_strings = [
                'pet adventure(s) cancelled', #English
                'mascota(s) cancelada(s)', #Spanish
                'pets cancelada(s)', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is not None:
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                    await message.reply(
                        f"**{user.name}**, please use {command_pets_list}"
                        f' to update your pet reminders.'
                    )
                    return
                user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_PETS_ADVENTURE_CANCEL
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
                pet_ids_match = re.search(
                        r'\bpets?\s+(?:\badv\b|\badventure\b)\s+\bcancel\b\s+(.+?)$',
                        user_command_message.content.lower()
                    )
                if not pet_ids_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find pet ids in the pet adv cancel user command message.', message)
                    return
                pet_ids = re.split(r'\s+', sent_pet_ids_match.group(1))
                for pet_id in pet_ids:
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, f'pets-{pet_id}')
                    except exceptions.NoDataFoundError:
                        continue
                    await reminder.delete()
                    if reminder.record_exists:
                        logs.logger.error(
                            f'{datetime.utcnow()}: Had an error deleting the pet reminder with activity '
                            f'pets-{pet_id}.'
                        )
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            # Pets claim when no pets are on adventures, for ready list
            search_strings = [
                'there are no pet adventure rewards to claim', #English
                'no hay recompensas de pet adventure para reclamar', #Spanish
                'não há recompensas de pet adventure para coletar', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for pet claim without active pets message.', message)
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                if user_settings.ready_pets_claim_active:
                    await user_settings.update(ready_pets_claim_active=False)

            search_strings = [
                'it came back instantly!!', #English
                'volvio al instante!!', #Spanish
                'voltou instantaneamente!!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_PETS_ADVENTURE_START
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
                if user_settings.reactions_enabled: await message.add_reaction(emojis.SKILL_TIME_TRAVELER)
                await message.reply(f"➜ {strings.SLASH_COMMANDS['pets claim']}")

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_description = icon_url = message_title = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.description: message_description = str(embed.description)
            if embed.title: message_title = embed.title

            # Pets list, updates pets and pet reminders
            search_strings = [
                'pets can collect items and coins, more information', #English
                'las mascotas puedes recoger items y coins, más información', #Spanish
                'pets podem coletar itens e coins, mais informações', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                pet_names_emojis = {
                    'cat': emojis.PET_CAT,
                    'voidog': emojis.PET_VOIDOG,
                    'dog': emojis.PET_DOG,
                    'dragon': emojis.PET_DRAGON,
                    'golden bunny': emojis.PET_GOLDEN_BUNNY,
                    'hamster': emojis.PET_HAMSTER,
                    'pumpkin bat': emojis.PET_PUMPKIN_BAT,
                    'pink fish': emojis.PET_PINK_FISH,
                    'snowball': emojis.PET_SNOWBALL,
                    'pony': emojis.PET_PONY,
                    'panda': emojis.PET_PANDA,
                    'snowman': emojis.PET_SNOWBALL,
                    'penguin': emojis.PET_PENGUIN,
                }
                user_id = user_name = user_command_message = pet_type = None
                unexpected_changes_found = False
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await functions.get_message_from_channel_history(
                                    message.channel, regex.COMMAND_PETS,
                                    user_name=user_name
                                )
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet list message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                pet_amount_match = re.search(f'pets__\*\*: \d+/(\d+?)\n', message_description.lower())
                pages_match = re.search(f'page__\*\*: (\d+?)/(\d+?)$', message_description.lower())
                if not pages_match or not pet_amount_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(
                        f'Couldn\'t find pages or pet amount in the pet list message.\n'
                        f'Pages match: {pages_match}\n',
                        f'Pet amount match: {pet_amount_match}\n',
                        message
                    )
                    return
                current_page = int(pages_match.group(1))
                max_page = int(pages_match.group(2))
                max_pets = int(pet_amount_match.group(1))
                try:
                    user_pets = await pets.get_pets(user.id)
                except exceptions.NoDataFoundError:
                    user_pets = []
                if len(user_pets) != max_pets or ceil(len(max_pets) / 6) != max_page:
                    outdated_pet_pages = list(range(1, max_page + 1))
                    await user_settings.update(outdated_pet_pages=outdated_pet_pages)
                for field in embed.fields:
                    if 'pets commands' in field.name.lower(): continue
                    pet_id_match = re.search(r'`id: (.+?)`', field.name.lower())
                    pet_tier_match = re.search(r'tier (.+?)$', field.name.lower())
                    if not pet_id_match or not pet_tier_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error(
                            f'Couldn\'t find pet ID or tier in field "{field.name}" in the pets list message.\n'
                            f'Pet ID match: {pet_id_match}'
                            f'Pet tier match: {pet_tier_match}',
                            message
                        )
                        return
                    for pet_name in pet_names_emojis.keys():
                        if pet_name in field.name.lower():
                            pet_type = pet_name
                            break
                    if pet_type is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error(
                            f'Couldn\'t find pet type in field "{field.name}" in the pets list message.\n',
                            message
                        )
                        return
                    pet_id = pet_id_match.group(1)
                    pet_tier = roman.fromRoman(pet_tier_match.group(1).upper())
                    normal_pet_skills = [
                        'clever',
                        'digger',
                        'epic',
                        'fast',
                        'happy',
                        'lucky',
                        'traveler',
                    ]
                    special_pet_skills = [
                        'faster',
                    ]
                    pet_skills_found = {}
                    for pet_skill in normal_pet_skills:
                        if pet_skill in field.value.lower():
                            pet_skill_match = re.search(rf'{pet_skill}\*\* \[(.+?)\]', field.value.lower())
                            if not pet_skill_match:
                                await functions.add_warning_reaction(message)
                                await errors.log_error(
                                    f'Couldn\'t find skill rank for skill {pet_skill} in the pets list message.',
                                    message
                                )
                                return
                            pet_skill_rank = strings.PET_SKILL_RANKS.index(pet_skill_match.group(1).lower()) + 1
                            pet_skills_found[pet_skill] = pet_skill_rank
                    for pet_skill in special_pet_skills:
                        if pet_skill in field.value.lower(): pet_skills_found[pet_skill] = 1
                    pet_id_int = await functions.convert_pet_id_to_int(pet_id)
                    try:
                        existing_pet: pets.Pet = await pets.get_pet(user.id, pet_id_int)
                    except exceptions.NoDataFoundError:
                        existing_pet = None
                    updated_pet = await pets.insert_pet(user.id, pet_id_int, pet_tier, pet_type, pet_skills_found)
                    if existing_pet is not None and updated_pet != existing_pet:
                        unexpected_changes_found = True
                        outdated_pet_pages = list(range(1, max_page + 1))
                        await user_settings.update(outdated_pet_pages=outdated_pet_pages)
                    pet_emoji = ''
                    for pet, emoji in pet_names_emojis.items():
                        if pet in field.name.lower():
                            pet_emoji = emoji
                            break
                    pet_action_timestring_match = re.search(r'Status__:\*\* (.+?) \| \*\*(.+?)\*\*', field.value)
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
                    if pet_action in pet_actions:
                        pet_timestring = pet_action_timestring_match.group(2)
                        time_left = await functions.parse_timestring_to_timedelta(pet_timestring.lower())
                        if time_left < timedelta(0): return # This can happen because the timeout edits pets list one last time
                        reminder_message = user_settings.alert_pets.message.replace('{id}', pet_id).replace('{emoji}',pet_emoji)
                        reminder: reminders.Reminder = (
                            await reminders.insert_user_reminder(user.id, f'pets-{pet_id}', time_left,
                                                                message.channel.id, reminder_message)
                        )
                if user_settings.outdated_pet_pages:
                    if current_page in user_settings.outdated_pet_pages:
                        outdated_pet_pages = user_settings.outdated_pet_pages
                        outdated_pet_pages.remove(current_page)
                        if not outdated_pet_pages: outdated_pet_pages = [0,]
                        await user_settings.update(outdated_pet_pages=outdated_pet_pages)
                    pages = await functions.convert_outdated_pet_pages_to_string(user_settings.outdated_pet_pages)
                    answer = (
                        f'Pets page `{current_page}` updated.\n'
                        f'Remaining pet pages:\n'
                        f'{emojis.BP} {pages}'
                    )
                    if unexpected_changes_found:
                        answer = (
                            f'{emojis.WARNING} Unexpected pet discrepancy found. Please show all pet pages.\n\n'
                            f'{answer}'
                        )
                    pets_list_update_message_ids = pets_list_update_messages_ids.get(user.id, None)
                    if pets_list_update_message_ids is None:
                        update_message = await message.reply(content=answer)
                        pets_list_update_messages_ids[user.id] = (message.id, update_message.id)
                    else:
                        pets_list_message_id , pets_list_update_message_id = pets_list_update_message_ids
                        if pets_list_message_id == message.id:
                            pets_list_update_message = message.channel.get_partial_message(pets_list_update_message_id)
                            await pets_list_update_message.edit(content=answer)
                        else:
                            update_message = await message.reply(content=answer)
                            pets_list_update_messages_ids[user.id] = (message.id, update_message.id)
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            # Pets claim
            search_strings = [
                'pet adventure rewards', #English
                'recompensas de pet adventure', #Spanish, Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await functions.get_message_from_channel_history(
                                    message.channel, regex.COMMAND_PETS_CLAIM,
                                    user_name=user_name
                                )
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet claim message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_pets.enabled: return
                if user_settings.ready_pets_claim_active:
                    await user_settings.update(ready_pets_claim_active=False)


# Initialization
def setup(bot):
    bot.add_cog(PetsCog(bot))