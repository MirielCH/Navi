# horse_festival.py

from datetime import datetime, timedelta, timezone
import asyncio
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


class HorseFestivalCog(commands.Cog):
    """Cog that contains the horse festival detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_after.embeds:
            embed: discord.Embed = message_after.embeds[0]
            message_author = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Minirace embed
            if '— minirace' in message_author.lower():
                user_name = user_id = None
                user = await functions.get_interaction_user(message_after)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message_after.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user = await functions.get_member_by_name(self.bot, message_after.guild, user_name)
                        else:
                            await functions.add_warning_reaction(message_after)
                            await errors.log_error('User not found in minirace embed.', message_after)
                            return
                        user_command_message = (
                            await messages.find_message(message_after.channel.id, regex.COMMAND_HF_MINIRACE,
                                                        user_name=user_name)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message_after)
                            await errors.log_error('Couldn\'t find a command for minirace embed.', message_after)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_minirace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'minirace')
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = midnight_today + timedelta(days=1, minutes=6, seconds=random.randint(60, 300))
                time_left = end_time - current_time
                reminder_message = user_settings.alert_minirace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'minirace', time_left,
                                                         message_after.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message_after, reminder, user_settings)
        
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""

        if not message.embeds:
            message_content = message.content

            # Lightspeed
            search_strings = [
                'rides at the speed of light', #English
                'viaja a la velocidad de la luz', #Spanish
                'viaja na velocidade', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r'\*\*(.+?)\*\* rides', #English
                        r'\*\*(.+?)\*\* viaja', #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HF_LIGHTSPEED,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in horse lightspeed message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                await reminders.reduce_reminder_time(user_settings, 'half', strings.SLEEPY_POTION_AFFECTED_ACTIVITIES)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'horse')
                if user_settings.alert_horse_breed.enabled:
                    user_command = await functions.get_slash_command(user_settings, 'horse breeding')
                    reminder_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'horse', time_left,
                                                            message.channel.id, reminder_message)
                    )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'horse'))
                if user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)
                    await message.add_reaction(emojis.KIRBY_RUN)

            # Megarace
            search_strings = [
                'you have not reached the end of this stage', #English
                'aún no has llegado al final de esta etapa', #Spanish
                'você ainda não chegou ao fim desta etapa', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace start message.', message)
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'megarace')
                search_patterns = [
                    r'be there in \*\*(.+?)\*\*', #English
                    r'allí en \*\*(.+?)\*\*', #Spanish
                    r'lá em \*\*(.+?)\*\*', #Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_megarace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            
            search_strings = [
                'you are now in the list of pending players for a tournament', #English
                'ahora estás en la lista de jugadores pendientes de un torneo', #Spanish
                'você está agora na lista de jogadores pendentes para um torneio', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the minirace message.', message)
                        return
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in minirace message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_minirace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'minirace')
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = midnight_today + timedelta(days=1, minutes=6)
                time_left = end_time - current_time
                reminder_message = user_settings.alert_minirace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'minirace', time_left,
                                                         message.channel.id, reminder_message)
                )

            search_strings = [
                'started riding!', #English
                'started riding!', #TODO: Spanish
                'started riding!', #TODO: Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in minirace start message.', message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HF_MINIRACE, user=user,
                                                    user_name=user_name_match.group(1))
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the minirace start message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_minirace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'minirace')
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = midnight_today + timedelta(days=1, minutes=6, seconds=random.randint(60, 300))
                time_left = end_time - current_time
                reminder_message = user_settings.alert_minirace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'minirace', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'minirace'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_field0_name = message_field1_name = message_field0_value = message_field1_value = message_author = ''
            message_description = ''
            if embed.description is not None: message_description = str(embed.description)
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                message_field0_name = embed.fields[0].name
                message_field0_value = embed.fields[0].value
            if len(embed.fields) > 1:
                message_field1_name = embed.fields[1].name
                message_field1_value = embed.fields[1].value

            search_strings = [
                'total time', #English
                'tiempo total', #Spanish
                'tempo total', #Portuguese
            ]
            if (any(search_string in message_field1_name.lower() for search_string in search_strings)
                and 'megarace' in message_author.lower()):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if not user_name_match:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User name not found in megarace message.', message)
                            return
                        user_name = user_name_match.group(1)
                        user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HF_MEGARACE, user=user,
                                                    user_name=user_name)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the megarace message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'megarace')
                search_patterns = [
                    r' \*\*(.+?)\*\* ', #English, Spanish, Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field1_value.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                reminder_message = user_settings.alert_megarace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'you can join megarace every week', #English
                'puedes entrar a la megacarrera cada semana', #Spanish
                'você pode entrar na mega corrida toda semana', #Portuguese
            ]
            search_strings_not_started = [
                'megarace not started', #English 2
                'la megacarrera no comenzó', #Spanish 2
                'a megacorrida não começou', #Portuguese 2
            ]
            search_strings_completed = [
                'megarace completed', #English
                'megacarrera completada', #Spanish
                'megacorrida completa', #Portuguese
            ]
            if (any(search_string in message_description.lower() for search_string in search_strings)
                and not any(search_string in message_field0_value.lower() for search_string in search_strings_not_started)):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HF_MEGARACE)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace overview message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'megarace')
                if any(search_string in message_field0_value.lower() for search_string in search_strings_completed):
                    current_time = utils.utcnow()
                    next_monday = current_time.date() + timedelta(days=(0 - current_time.weekday() - 1) % 7 + 1)
                    next_monday_dt = datetime(year=next_monday.year, month=next_monday.month, day=next_monday.day, hour=0, minute=5, second=0, microsecond=0, tzinfo=timezone.utc)
                    time_left = next_monday_dt - utils.utcnow() + timedelta(seconds=random.randint(0, 600))
                else:
                    search_patterns = [
                        r'time remaining\*\*: (.+?)\n', #English
                        r'ti?empo restante\*\*: (.+?)\n', #Spanish, Portuguese
                    ]
                    timestring_match = await functions.get_match_from_patterns(search_patterns, message_field0_value.lower())
                    timestring = timestring_match.group(1)
                    if timestring in ('0d 0h 0m 0s', '0h 0m 0s'): return
                    time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_megarace.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'megarace', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'passes through the boost', #English
                'pasa por el boost', #Spanish
                'passa pelo boost', #Spanish, UNCONFIRMED
            ]
            if any(search_string in message_field0_name.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_field0_name)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in megarace boost done message.', message)
                        return
                    user_name = user_name_match.group(1)
                    guild_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if not guild_users: return
                    if len(guild_users) > 1:
                        await functions.add_warning_reaction(message)
                        await errors.log_error(f'User {user_name} not unique in megarace boost done message. Found {guild_users}.', message)
                        return
                    user = guild_users[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_megarace.enabled: return
                search_patterns = [
                    r'(?:increased|reduced)__: \*\*(.+?)\*\*', #English
                    r'(?:incrementado|aumentado|reducido)__: \*\*(.+?)\*\*', #Spanish, increased one UNCONFIRMED
                    r'(?:incrementado|aumentado|reduzido)__: \*\*(.+?)\*\*', #TODO: Portuguese
                ]
                timestring_match = await functions.get_match_from_patterns(search_patterns, message_field0_value.lower())
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in megarace boost done message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'megarace')
                except exceptions.NoDataFoundError:
                    return
                search_strings_increased = [
                    'stage time increased', #English
                ]
                search_strings_reduced = [
                    'stage time reduced', #English
                    'tiempo de etapa reducido', #Spanish
                    'tempo da etapa reduzido', #Portuguese
                ]
                if any(search_string in message_field0_value.lower() for search_string in search_strings_increased):
                    new_end_time = reminder.end_time + time_left
                elif any(search_string in message_field0_value.lower() for search_string in search_strings_reduced):
                    new_end_time = reminder.end_time - time_left
                await reminder.update(end_time=new_end_time)
                await functions.add_reminder_reaction(message, reminder, user_settings)

            search_strings = [
                'megaraceboost',
            ]
            if any(search_string in message_field0_name.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_field0_name)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in megarace boost message.', message)
                        return
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await messages.find_message(message.channel.id, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace boost message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.megarace_helper_enabled: return
                answer = f'Hey! A **megarace boost** just appeared!'
                answer = f'{answer} {user.mention}' if user_settings.ping_after_message else f'{user.mention} {answer}'
                await message.channel.send(answer)

            search_strings = [
                'did not pass through the boost',
            ]
            if any(search_string in message_field0_name.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_field0_name)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in megarace boost missed message.', message)
                        return
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await messages.find_message(message.channel.id, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user command for the megarace boost missed message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            # Megarace helper
            if '— megarace' in message_author.lower():
                user_name = user_id = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if not user_name_match:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in megarace message for megarace helper.', message)
                            return
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HF_MEGARACE, user=user,
                                                        user_name=user_name)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the megarace helper message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.megarace_helper_enabled: return
                answer = await functions.get_megarace_answer(message)
                if answer is None: return
                if user_settings.dnd_mode_enabled:
                    await message.reply(answer)
                else:
                    answer = f'{answer} {user.mention}' if user_settings.ping_after_message else f'{user.mention} {answer}'
                    await message.reply(answer)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(HorseFestivalCog(bot))