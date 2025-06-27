# quest.py

import asyncio
from datetime import timedelta
from math import floor
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import cooldowns, clans, errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings


class QuestCog(commands.Cog):
    """Cog that contains the quest detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        if message_before.edited_at == message_after.edited_at: return
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
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = message_description = icon_url = field_value = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                field_name = embed.fields[0].name
                field_value = embed.fields[0].value
            if embed.title is not None: message_title = str(embed.title)
            if embed.description is not None: message_description = embed.description

            # Guild quest check
            search_strings_quest = [
                'are you looking for a quest', #English
                'buscando una misión', #Spanish
                'procurando uma missão', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings_quest):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_QUEST,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in guild quest message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                user_global_name = user.global_name if user.global_name is not None else user.name
                search_strings_miniboss = [
                    'summon and kill a miniboss', #English
                    'invoca y mata un miniboss', #Spanish
                    'invocar e matar um miniboss', #Portuguese
                ]
                if any(search_string in field_value.lower() for search_string in search_strings_miniboss): 
                    if user_settings.alert_dungeon_miniboss.enabled:
                        try:
                            miniboss_reminder = await reminders.get_user_reminder(user.id, 'dungeon-miniboss')
                            if miniboss_reminder.triggered: miniboss_reminder = None
                        except:
                            miniboss_reminder = None
                        command_miniboss = await functions.get_slash_command(user_settings, 'miniboss')
                        if miniboss_reminder is not None:
                            current_time = utils.utcnow()
                            time_left = miniboss_reminder.end_time - current_time
                            timestring = await functions.parse_timedelta_to_timestring(time_left)
                            answer = f'🕓 {command_miniboss} is ready in **{timestring}**.'
                        else:
                            answer = f'{emojis.ENABLED} {command_miniboss} is ready!'
                        if user_settings.dnd_mode_enabled:
                            answer = f'**{user_global_name}**, {answer}'
                        else:
                            if user_settings.ping_after_message:
                                answer = f'{answer} {user.mention}'
                            else:
                                answer = f'{user.mention} {answer}'
                        await message.channel.send(answer)
                    
                search_strings_guild_raid = [
                    'do a guild raid', #English
                    'has un guild raid', #Spanish
                    'faça uma guild raid', #Portuguese
                ]
                if any(search_string in field_value.lower() for search_string in search_strings_guild_raid): 
                    clan: clans.Clan | None
                    try:
                        clan = await clans.get_clan_by_user_id(user_settings.user_id)
                    except exceptions.NoDataFoundError:
                        clan = None
                    if clan:
                        clan_reminder: reminders.Reminder | None
                        try:
                            clan_reminder = await reminders.get_clan_reminder(clan.clan_name)
                        except exceptions.NoDataFoundError:
                            clan_reminder = None

                        if clan.alert_enabled:
                            if user_settings.dnd_mode_enabled:
                                user_name = f'**{user_global_name}**,'
                            else:
                                user_name = user.mention
                            await user_settings.update(last_quest_command='quest')
                            if clan.stealth_current < clan.stealth_threshold and not clan.upgrade_quests_enabled:
                                await message.channel.send(
                                    f'{user_name}\n'
                                    f'{emojis.DISABLED} Guild quest slot not available.\n'
                                    f'Your guild doesn\'t allow doing guild quests below the '
                                    f'stealth threshold ({clan.stealth_threshold}).'
                                )
                                return
                            if clan.quest_user_id is not None:
                                await message.channel.send(
                                    f'{user_name}\n'
                                    f'{emojis.DISABLED} Guild quest slot not available.\n'
                                    f'Another guild member is already doing a guild quest.'
                                )
                                return
                            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                            if clan_reminder:
                                current_time = utils.utcnow()
                                time_left = clan_reminder.end_time - current_time
                                timestring = await functions.parse_timedelta_to_timestring(time_left)
                                raid_ready = f'🕓 {command_raid} is ready in **{timestring}**.'
                                await user_settings.update(guild_quest_prompt_active=True)
                            else:
                                raid_ready = f'{emojis.ENABLED} {command_raid} is ready!'
                            await message.channel.send(
                                f'{user_name}\n'
                                f'{emojis.ENABLED} Guild quest slot available!\n{raid_ready}\n\n'
                                f'_If you accept this quest, the next guild reminder will ping you solo first. '
                                f'You will have 5 minutes to raid before the other members are pinged._\n'
                                f'_Note that you will lose your slot if you don\'t answer in time._'
                            )
                            return
                    if user_settings.alert_guild.enabled:
                        try:
                            clan_user_reminder = await reminders.get_user_reminder(user.id, 'guild')
                            if clan_user_reminder.triggered: clan_user_reminder = None
                        except:
                            clan_user_reminder = None
                        command_guild_raid = await functions.get_slash_command(user_settings, 'guild raid')
                        if clan_user_reminder is not None:
                            current_time = utils.utcnow()
                            time_left = clan_user_reminder.end_time - current_time
                            timestring = await functions.parse_timedelta_to_timestring(time_left)
                            answer = f'🕓 {command_guild_raid} is ready in **{timestring}**.'
                        else:
                            answer = f'{emojis.ENABLED} {command_guild_raid} is ready!'
                        if user_settings.dnd_mode_enabled:
                            answer = f'**{user_global_name}**, {answer}'
                        else:
                            answer = f'{user.mention} {answer}'
                        await message.channel.send(answer)

            # Quest cooldown
            search_strings = [
                'you have already claimed a quest', #English
                'ya reclamaste una misión', #Spanish
                'você já reivindicou uma missão', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User name not found in quest cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_QUEST_EPIC_QUEST,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for quest cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    last_quest_command = 'epic quest' if interaction.name.startswith('epic') else 'quest'
                else:
                    user_command_message_content = re.sub(rf'\b<@!?{settings.EPIC_RPG_ID}>\b', '',
                                                          user_command_message.content.lower())
                    last_quest_command = 'epic quest' if 'epic quest' in user_command_message_content else 'quest'
                user_command = await functions.get_slash_command(user_settings, last_quest_command)
                await user_settings.update(last_quest_command=last_quest_command)
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in quest cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                activity: str = 'quest'
                if user_settings.multiplier_management_enabled:
                    await user_settings.update_multiplier(activity, time_left)
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, activity, time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Quest in void areas and TOP
            search_strings = [
                'i don\'t think i can give you any quest here', #English
                'misión aquí', #Spanish
                'missão aqui', #Portuguese, UNCONFIRMED
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_QUEST_EPIC_QUEST,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in void quest message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'quest')
                await user_settings.update(last_quest_command='quest')
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'quest')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'quest'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Epic Quest
            search_strings = [
                '__wave #1__', #English
                '__oleada #1__', #Spanish
                '__onda #1__', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_EPIC_QUEST,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in epic quest message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'epic quest')
                await user_settings.update(last_quest_command='epic quest')
                current_time = utils.utcnow()
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = current_time - bot_answer_time
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest')
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                if cooldown.donor_affected:
                    time_left_seconds = (actual_cooldown
                                        * settings.DONOR_COOLDOWNS[user_donor_tier]
                                        - floor(time_elapsed.total_seconds()))
                else:
                    time_left_seconds = actual_cooldown - floor(time_elapsed.total_seconds())
                if user_settings.christmas_area_enabled: time_left_seconds *= settings.CHRISTMAS_AREA_MULTIPLIER
                if user_settings.round_card_active: time_left_seconds *= settings.ROUND_CARD_MULTIPLIER
                if user_settings.potion_flask_active: time_left_seconds *= settings.POTION_FLASK_MULTIPLIER
                time_left = timedelta(seconds=time_left_seconds)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'quest'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Guild quest in progress
            search_strings = [
                'if you don\'t want this quest anymore', #English
                'si ya no quieres esta misión', #Spanish
                'se você não quiser mais esta missão', #Portuguese
            ]
            if (any(search_string in message_description.lower() for search_string in search_strings)
                and 'guild' in field_name.lower()):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_QUEST,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in guild quest progress message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user_settings.user_id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                user_global_name = user.global_name if user.global_name is not None else user.name
                if user_settings.dnd_mode_enabled:
                    user_name = f'**{user_global_name}**,'
                else:
                    user_name = user.mention
                if clan.stealth_current < clan.stealth_threshold and not clan.upgrade_quests_enabled:
                    await message.channel.send(
                        f'{user_name}\n'
                        f'{emojis.DISABLED} Guild quest slot not available.\n'
                        f'Your guild doesn\'t allow doing guild quests below the '
                        f'stealth threshold ({clan.stealth_threshold}).'
                    )
                    return
                if clan.quest_user_id is not None:
                    if clan.quest_user_id == user.id:
                        await message.channel.send(
                            f'{user_name} You are already registered for the guild quest. Patience, young Padawan.'
                        )
                    else:
                        await message.channel.send(
                            f'{user_name}\n'
                            f'{emojis.DISABLED} Guild quest slot not available.\n'
                            f'Another guild member is already doing a guild quest.'
                        )
                    return
                await user_settings.update(guild_quest_prompt_active=True)
                await message.channel.send(
                    f'{user_name}\n'
                    f'{emojis.ENABLED} You are now registered for the guild quest.\n'
                    f'You will have 5 minutes to raid before the other members are pinged.\n'
                    f'Note that you will lose your slot if you don\'t answer in time.'
                )
                await clan.update(quest_user_id=user.id)
                try:
                    clan_reminder: reminders.Reminder = (
                        await reminders.get_clan_reminder(clan.clan_name)
                    )
                except exceptions.NoDataFoundError:
                    clan_reminder = None
                current_time = utils.utcnow()
                clan_member: clans.ClanMember
                for clan_member in clan.members:
                    if clan_member.user_id == user.id: continue
                    try:
                        user_clan_reminder: reminders.Reminder = (
                            await reminders.get_user_reminder(clan_member.user_id, 'guild')
                        )
                    except exceptions.NoDataFoundError:
                        continue
                    user_reminder_time_left = user_clan_reminder.end_time - current_time
                    new_end_time = current_time + (user_reminder_time_left + timedelta(minutes=5))
                    await user_clan_reminder.update(end_time=new_end_time)


        if not message.embeds:
            message_content = message.content
            # Quest
            search_strings = [
                'got a **new quest**!', #English accepted
                'you did not accept the quest', #English declined
                'consiguió una **nueva misión**', #Spanish accepted
                'no aceptaste la misión', #Spanish declined
                'conseguiu uma **nova missão**', #Portuguese accepted
                'você não aceitou a missão', #Portuguese declined
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_QUEST,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found for quest message.', message)
                            return
                        user = user_command_message.author
                quest_declined = True if message.mentions else False
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'quest')
                await user_settings.update(last_quest_command='quest')
                current_time = utils.utcnow()
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = current_time - bot_answer_time
                if quest_declined:
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest-decline')
                else:
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest')
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                if cooldown.donor_affected:
                    time_left_seconds = (actual_cooldown
                                        * settings.DONOR_COOLDOWNS[user_donor_tier]
                                        - floor(time_elapsed.total_seconds()))
                else:
                    time_left_seconds = actual_cooldown - floor(time_elapsed.total_seconds())
                if user_settings.christmas_area_enabled: time_left_seconds *= settings.CHRISTMAS_AREA_MULTIPLIER
                if user_settings.round_card_active: time_left_seconds *= settings.ROUND_CARD_MULTIPLIER
                if user_settings.potion_flask_active: time_left_seconds *= settings.POTION_FLASK_MULTIPLIER
                time_left = timedelta(seconds=time_left_seconds * user_settings.alert_quest.multiplier
                                      * (1 - (1.535 * (1 - user_settings.user_pocket_watch_multiplier))))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.guild_quest_prompt_active:
                    if not quest_declined:
                        try:
                            clan: clans.Clan = await clans.get_clan_by_clan_name(user_settings.clan_name)
                            await clan.update(quest_user_id=user.id)
                            if clan.alert_enabled:
                                try:
                                    clan_reminder: reminders.Reminder = (
                                        await reminders.get_clan_reminder(clan.clan_name)
                                    )
                                except exceptions.NoDataFoundError:
                                    clan_reminder = None
                            clan_member: clans.ClanMember
                            for clan_member in clan.members:
                                if clan_member.user_id == user.id: continue
                                try:
                                    user_clan_reminder: reminders.Reminder = (
                                        await reminders.get_user_reminder(clan_member.user_id, 'guild')
                                    )
                                except exceptions.NoDataFoundError:
                                    continue
                                new_end_time = user_clan_reminder.end_time + timedelta(minutes=5)
                                await user_clan_reminder.update(end_time=new_end_time)
                        except exceptions.NoDataFoundError:
                            pass

                    await user_settings.update(guild_quest_prompt_active=False)
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'quest'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Aborted guild quest
            search_strings = [
                'you don\'t have a quest anymore', #English
                'ya no tienes una misión', #Spanish
                'você não tem mais uma missão', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings) and message.mentions:
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if clan.quest_user_id == user.id:
                    await clan.update(quest_user_id=None)
                    clan_member: clans.ClanMember
                    for clan_member in clan.members:
                        if clan_member.user_id == user.id: continue
                        try:
                            user_clan_reminder: reminders.Reminder = (
                                await reminders.get_user_reminder(clan_member.user_id, 'guild')
                            )
                        except exceptions.NoDataFoundError:
                            continue
                        await user_clan_reminder.update(end_time=(user_clan_reminder.end_time - timedelta(minutes=5)))
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(QuestCog(bot))