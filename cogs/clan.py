# clan.py
# Contains clan detection commands

from datetime import timedelta
import re

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from database import clans, errors, cooldowns, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class ClanCog(commands.Cog):
    """Cog that contains the clan detection commands"""
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

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = message_footer = message_field0_name = message_field0_value = ''
            message_field1 = message_description = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)
            if embed.fields:
                message_field0_name = embed.fields[0].name
                message_field0_value = embed.fields[0].value
                if len(embed.fields) > 1:
                    message_field1 = embed.fields[1].value
            if embed.description: message_description = str(embed.description)
            if embed.footer: message_footer = str(embed.footer.text)

            # Clan cooldown
            search_strings = [
                'your guild has already raided or been upgraded', #English
                'tu guild ya hizo un raideo o fue mejorado', #Spanish
                'sua guild já raidou ou foi atualizada', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
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
                            await errors.log_error('User not found in clan cooldown message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in clan cooldown message.', message)
                    return
                clan = user_settings = None
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    pass
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    pass
                user_alert_enabled = getattr(getattr(user_settings, 'alert_guild', None), 'enabled', False)
                clan_channel_id = getattr(clan, 'channel_id', None)
                clan_alert_enabled = getattr(clan, 'alert_enabled', False)
                if clan_channel_id is None: clan_alert_enabled = False
                if not user_alert_enabled and not clan_alert_enabled:
                    return
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in clan cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                if clan_alert_enabled:
                    action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                    if slash_command:
                        alert_message = strings.SLASH_COMMANDS[action]
                    else:
                        alert_message = f'`rpg {action}`'
                    reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                            clan.channel_id, alert_message)
                    )
                    if reminder.record_exists:
                        if user_settings is None:
                            await message.add_reaction(emojis.NAVI)
                        else:
                            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)
                if user_alert_enabled:
                    if clan_alert_enabled:
                        action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                        if slash_command:
                            alert_message = await functions.get_slash_command(user_settings, action)
                        else:
                            alert_message = f'`rpg {action}`'
                    else:
                        if slash_command:
                            command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
                            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                        else:
                            command_upgrade = strings.SLASH_COMMANDS['guild upgrade']
                            command_raid = strings.SLASH_COMMANDS['guild raid']
                        alert_message = f"{command_upgrade} or {command_raid}"
                    alert_message = user_settings.alert_guild.message.replace('{command}', alert_message)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'guild', time_left,
                                                             message.channel.id, alert_message)
                    )
                    if not clan_alert_enabled:
                        await functions.add_reminder_reaction(message, reminder, user_settings)

            # Clan overview
            search_strings = [
                'your guild was raided', #English
                'tu guild fue raideado', #Spanish
                'sua guild foi raidad', #Portuguese
            ]
            if any(search_string in message_footer.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
                if message.mentions: return # Yes that also disables it if you ping yourself but who does that
                try:
                    clan_name = re.search(r"^\*\*(.+?)\*\*", message_description).group(1)
                except Exception as error:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Clan name not found in clan message.', message)
                    return
                clan = user_settings = None
                try:
                    clan: clans.Clan = await clans.get_clan_by_clan_name(clan_name)
                except exceptions.NoDataFoundError:
                    pass
                if user is not None:
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        pass
                user_alert_enabled = getattr(getattr(user_settings, 'alert_guild', None), 'enabled', False)
                clan_channel_id = getattr(clan, 'channel_id', None)
                clan_alert_enabled = getattr(clan, 'alert_enabled', False)
                if clan_channel_id is None: clan_alert_enabled = False
                if not user_alert_enabled and not clan_alert_enabled:
                    return
                search_patterns = [
                    r"STEALTH\*\*: (.+?)\n", #English
                    r"SIGILO\*\*: (.+?)\n", #Spanish
                    r"FURTIVIDADE\*\*: (.+?)\n", #Portuguese
                ]
                stealth_match = await functions.get_match_from_patterns(search_patterns, message_field1)
                if stealth_match:
                    stealth = stealth_match.group(1)
                    stealth = int(stealth)
                    await clan.update(stealth_current=stealth)
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Stealth not found in clan message.', message)
                    return
                timestring_match = re.search(r":clock4: \*\*(.+?)\*\*", message_field1)
                if not timestring_match: return
                timestring = timestring_match.group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
                if time_left < timedelta(0): return
                if clan_alert_enabled:
                    action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                    if slash_command:
                        alert_message = strings.SLASH_COMMANDS[action]
                    else:
                        alert_message = f'`rpg {action}`'
                    reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                            clan.channel_id, alert_message)
                    )
                    if reminder.record_exists:
                        if user_settings is None:
                            await message.add_reaction(emojis.NAVI)
                        else:
                            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)
                if user_alert_enabled:
                    if clan_alert_enabled:
                        action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                        if slash_command:
                            alert_message = await functions.get_slash_command(user_settings, action)
                        else:
                            alert_message = f'`rpg {action}`'
                    else:
                        if slash_command:
                            command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
                            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                        else:
                            command_upgrade = strings.SLASH_COMMANDS['guild upgrade']
                            command_raid = strings.SLASH_COMMANDS['guild raid']
                        alert_message = f"{command_upgrade} or {command_raid}"
                    alert_message = user_settings.alert_guild.message.replace('{command}', alert_message)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'guild', time_left,
                                                             message.channel.id, alert_message)
                    )
                    if not clan_alert_enabled:
                        await functions.add_reminder_reaction(message, reminder, user_settings)

            # Guild upgrade
            search_strings = [
                'upgrade', #English
                'mejora', #Spanish
                'melhoria', #Portuguese
            ]
            if any(search_string == message_field0_name.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(message.channel, r"^rpg\s+guild\s+upgrade\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the clan upgrade message.', message)
                        return
                    user = user_command_message.author
                clan = user_settings = None
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    pass
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    pass
                user_alert_enabled = getattr(getattr(user_settings, 'alert_guild', None), 'enabled', False)
                clan_channel_id = getattr(clan, 'channel_id', None)
                clan_alert_enabled = getattr(clan, 'alert_enabled', False)
                if clan_channel_id is None: clan_alert_enabled = False
                if not user_alert_enabled and not clan_alert_enabled:
                    return
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                if time_left < timedelta(0): return
                if clan_alert_enabled:
                    action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                    if slash_command:
                        alert_message = strings.SLASH_COMMANDS[action]
                    else:
                        alert_message = f'`rpg {action}`'
                    clan_stealth_before = clan.stealth_current
                    stealth_match = re.search(r"--> \*\*(.+?)\*\*", message_field0_value)
                    if stealth_match:
                        stealth = int(stealth_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Stealth not found in clan upgrade message.', message)
                        return
                    await clan.update(stealth_current=stealth)
                    reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                             clan.channel_id, alert_message)
                    )
                    if reminder.record_exists:
                        user_reactions_enabled = getattr(user_settings, 'reactions_enabled', True)
                        if user_reactions_enabled:
                            await message.add_reaction(emojis.NAVI)
                            if clan.stealth_current >= clan.stealth_threshold:
                                await message.add_reaction(emojis.YAY)
                            if clan.stealth_current == clan_stealth_before:
                                await message.add_reaction(emojis.ANGRY)
                            if clan.stealth_current == 69:
                                await message.add_reaction(emojis.NICE)
                    else:
                        if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)
                if user_alert_enabled:
                    if clan_alert_enabled:
                        action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                        if slash_command:
                            alert_message = await functions.get_slash_command(user_settings, action)
                        else:
                            alert_message = f'`rpg {action}`'
                    else:
                        if slash_command:
                            command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
                            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                        else:
                            command_upgrade = strings.SLASH_COMMANDS['guild upgrade']
                            command_raid = strings.SLASH_COMMANDS['guild raid']
                        alert_message = f"{command_upgrade} or {command_raid}"
                    alert_message = user_settings.alert_guild.message.replace('{command}', alert_message)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'guild', time_left,
                                                             message.channel.id, alert_message)
                    )
                    if not clan_alert_enabled:
                        await functions.add_reminder_reaction(message, reminder, user_settings)

            # Guild raid
            search_strings = [
                '** RAIDED **', #English
                '** RAIDEÓ **', #Spanish
                '** RAIDOU **', #Portuguese
            ]
            if (any(search_string in message_description for search_string in search_strings)
                and ':crossed_swords:' in message_description.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
                if user is None:
                    search_patterns = [
                        r"\*\*(.+?)\*\* throws", #English
                        r"\*\*(.+?)\*\* tiró", #Spanish
                        r"\*\*(.+?)\*\* jogou", #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_field0_value)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in clan raid message.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in clan raid message.', message)
                    return
                clan = user_settings = None
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    pass
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    pass
                user_alert_enabled = getattr(getattr(user_settings, 'alert_guild', None), 'enabled', False)
                clan_channel_id = getattr(clan, 'channel_id', None)
                clan_alert_enabled = getattr(clan, 'alert_enabled', False)
                if clan_channel_id is None: clan_alert_enabled = False
                if not user_alert_enabled and not clan_alert_enabled:
                    return
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                if time_left < timedelta(0): return
                if clan_alert_enabled:
                    search_patterns = [
                        r"earned \*\*(.+?)\*\*", #English
                        r"ganó \*\*(.+?)\*\*", #Spanish
                        r"ganhou \*\*(.+?)\*\*", #Portuguese
                    ]
                    energy_match = await functions.get_match_from_patterns(search_patterns, message_field1)
                    if energy_match:
                        energy = int(energy_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Energy not found in clan raid message.', message)
                        return
                    current_time = datetime.utcnow().replace(microsecond=0)
                    clan_raid = await clans.insert_clan_raid(clan.clan_name, user.id, energy, current_time)
                    if not clan_raid.raid_time == current_time:
                        if settings.DEBUG_MODE:
                            await message.channel.send(
                                'There was an error adding the raid to the leaderboard. Please tell Miri he\'s an idiot.'
                            )
                    action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                    if slash_command:
                        alert_message = strings.SLASH_COMMANDS[action]
                    else:
                        alert_message = f'`rpg {action}`'
                    reminder: reminders.Reminder = (
                        await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                            clan.channel_id, alert_message)
                    )
                    if reminder.record_exists:
                        if user_settings is None:
                            await message.add_reaction(emojis.NAVI)
                        else:
                            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                    else:
                        if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)
                if user_alert_enabled:
                    if clan_alert_enabled:
                        action = 'guild raid' if clan.stealth_current >= clan.stealth_threshold else 'guild upgrade'
                        if slash_command:
                            alert_message = await functions.get_slash_command(user_settings, action)
                        else:
                            alert_message = f'`rpg {action}`'
                    else:
                        if slash_command:
                            command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
                            command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                        else:
                            command_upgrade = strings.SLASH_COMMANDS['guild upgrade']
                            command_raid = strings.SLASH_COMMANDS['guild raid']
                        alert_message = f"{command_upgrade} or {command_raid}"
                    alert_message = user_settings.alert_guild.message.replace('{command}', alert_message)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'guild', time_left,
                                                             message.channel.id, alert_message)
                    )
                    if not clan_alert_enabled:
                        await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(ClanCog(bot))