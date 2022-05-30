# quest.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, clans, errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class QuestCog(commands.Cog):
    """Cog that contains the quest detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = message_description = icon_url = field_value = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                field_value = embed.fields[0].value
            if embed.title: message_title = str(embed.title)
            if embed.description: message_description = embed.description

            # Guild quest check
            if 'do a guild raid' in field_value.lower() and 'are you looking for a quest' in message_description.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s quest", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in guild quest message: {message.embeds[0].fields}',
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
                        f'User not found in guild quest message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_clan_name(user_settings.clan_name)
                except exceptions.NoDataFoundError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                if not clan.alert_enabled: return
                if clan.stealth_current < clan.stealth_threshold and not clan.upgrade_quests_enabled:
                    await message.reply(
                        f'{emojis.ERROR} Guild quest spot not available.\n'
                        f'Your guild doesn\'t allow doing guild quests below the '
                        f'stealth threshold ({clan.stealth_threshold}).'
                    )
                    return
                if clan.quest_user_id is not None:
                    await message.reply(
                        f'{emojis.ERROR} Guild quest spot not available.\n'
                        f'Another guild member is already doing a guild quest.'
                    )
                    return
                await user_settings.update(guild_quest_prompt_active=True)
                await message.reply(
                    f'{emojis.CHECK} Guild quest spot available.\n'
                    f'If you accept this quest, the next guild reminder will ping you solo first. '
                    f'You will have 5 minutes to raid before the other members are pinged.\n'
                    f'Note that you will lose your spot if you don\'t answer in time.'
                )

            # Quest cooldown
            if 'you have already claimed a quest' in message_title.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in quest cooldown message: {message.embeds[0].fields}',
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
                        f'User not found in quest cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    user_command = '/quest start' if interaction.name == 'quest' else '/epic quest'
                else:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            msg_content = msg.content.lower()
                            if ((msg_content.replace(' ','').startswith('rpgquest')
                                 or msg_content.replace(' ','').startswith('rpgepicquest'))
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the quest cooldown message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Quest in void areas
            if 'i don\'t think i can give you any quest here' in message_description.lower():
                user = await functions.get_interaction_user(message)
                user_command = 'rpg quest' if user is None else '/quest start'
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s quest", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in void quest message: {message.embeds[0].fields}',
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
                        f'User not found in void quest message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'quest')
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Epic Quest
            if '__wave #1__' in message_description.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                user_command = 'rpg epic quest' if user is None else '/epic quest'
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s epic quest", message_author).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in epic quest message: {message.embeds[0].fields}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        for member in message.guild.members:
                            member_name = await functions.encode_text(member.name)
                            if member_name == user_name:
                                user = member
                                break
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in epic quest message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest')
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[user_donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                reminder_message = user_settings.alert_quest.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'quest', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

        if not message.embeds:
            message_content = message.content
            # Quest
            if ('you did not accept the quest' in message_content.lower()
                or 'got a **new quest**!' in message_content.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                user_command = '/quest start' if user is not None else 'rpg quest'
                if user is None:
                    if message.mentions:
                        user = message.mentions[0]
                    else:
                        try:
                            user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in quest message: {message_content}',
                                message
                            )
                            return
                        for member in message.guild.members:
                            member_name = await functions.encode_text(member.name)
                            if member_name == user_name:
                                user = member
                                break
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in quest message: {message_content}',
                        message
                    )
                    return
                quest_declined = True if message.mentions else False
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_quest.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                if quest_declined:
                    time_left = timedelta(hours=1)
                else:
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('quest')
                    user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                    if cooldown.donor_affected:
                        time_left_seconds = (cooldown.actual_cooldown()
                                            * settings.DONOR_COOLDOWNS[user_donor_tier]
                                            - time_elapsed.total_seconds())
                    else:
                        time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                    time_left = timedelta(seconds=time_left_seconds)
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
                        except exceptions.NoDataFoundError:
                            pass
                    await user_settings.update(guild_quest_prompt_active=False)
                if reminder.record_exists:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

            # Aborted guild quest
            if 'you don\'t have a quest anymore' in message_content.lower() and message.mentions:
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if clan.quest_user_id is not None:
                    if clan.quest_user_id == user.id:
                        await clan.update(quest_user_id=None)
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(QuestCog(bot))