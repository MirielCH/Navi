# clan.py
# Contains clan detection commands

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
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = message_footer = message_field0 = ''
            message_field1 = message_description = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)
            if embed.fields:
                message_field0 = embed.fields[0].value
                if len(embed.fields) > 1:
                    message_field1 = embed.fields[1].value
            if embed.description: message_description = str(embed.description)
            if embed.footer: message_footer = str(embed.footer.text)

            # Clan cooldown
            if 'your guild has already raided or been upgraded' in message_title.lower():
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                alert_message_prefix = '/' if user is not None else 'rpg '
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
                                f'User not found in clan cooldown message: {message.embeds[0].fields}',
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
                        f'User not found in clan cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    user_settings = None
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if clan.stealth_current >= clan.stealth_threshold:
                    alert_message = f'{alert_message_prefix}guild raid'
                else:
                    alert_message = f'{alert_message_prefix}guild upgrade'
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

            # Clan overview
            if 'your guild was raided' in message_footer.lower():
                user = await functions.get_interaction_user(message)
                alert_message_prefix = '/' if user is not None else 'rpg '
                if message.mentions: return # Yes that also disables it if you ping yourself but who does that
                try:
                    clan_name = re.search("^\*\*(.+?)\*\*", message_description).group(1)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Clan name not found in clan message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_clan_name(clan_name)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled or clan.channel_id is None: return
                user_settings = None
                if user is not None:
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        pass
                try:
                    stealth = re.search("STEALTH\*\*: (.+?)\\n", message_field1).group(1)
                    stealth = int(stealth)
                    await clan.update(stealth_current=stealth)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Stealth not found in clan message: {message.embeds[0].fields}',
                        message
                    )
                    return
                if clan.stealth_current >= clan.stealth_threshold:
                    alert_message = f'{alert_message_prefix}guild raid'
                else:
                    alert_message = f'{alert_message_prefix}guild upgrade'
                timestring_search = re.search(":clock4: \*\*(.+?)\*\*", message_field1)
                if timestring_search is None: return
                timestring = timestring_search.group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
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

            # Guild upgrade
            if ('guild successfully upgraded!' in message_description.lower()
                or 'guild upgrade failed!' in message_description.lower()):
                user = await functions.get_interaction_user(message)
                alert_message_prefix = '/' if user is not None else 'rpg '
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower() == 'rpg guild upgrade' and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the clan upgrade message.',
                            message
                        )
                        return
                    user = user_command_message.author
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    user_settings = None
                clan_stealth_before = clan.stealth_current
                try:
                    stealth = re.search("--> \*\*(.+?)\*\*", message_field0).group(1)
                    stealth = int(stealth)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Stealth not found in clan upgrade message: {message.embeds[0].fields}',
                        message
                    )
                    return
                await clan.update(stealth_current=stealth)
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                if clan.stealth_current >= clan.stealth_threshold:
                    alert_message = f'{alert_message_prefix}guild raid'
                else:
                    alert_message = f'{alert_message_prefix}guild upgrade'
                reminder: reminders.Reminder = (
                    await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                         clan.channel_id, alert_message)
                )
                if reminder.record_exists:
                    if user_settings is None:
                        await message.add_reaction(emojis.NAVI)
                    else:
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                    if clan.stealth_current >= clan.stealth_threshold:
                        if user_settings is None:
                            await message.add_reaction(emojis.YAY)
                        else:
                            if user_settings.reactions_enabled: await message.add_reaction(emojis.YAY)
                    if clan.stealth_current == clan_stealth_before:
                        if user_settings is None:
                            await message.add_reaction(emojis.ANGRY)
                        else:
                            if user_settings.reactions_enabled: await message.add_reaction(emojis.ANGRY)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

            # Guild raid
            if ('** RAIDED **' in message_description and ':crossed_swords:' in message_description.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                alert_message_prefix = '/' if user is not None else 'rpg '
                if user is None:
                    try:
                        user_name = re.search("\*\*(.+?)\*\* throws", message_field0).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in clan raid message: {message.embeds[0].fields}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in clan raid message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    user_settings = None
                try:
                    energy = re.search("earned \*\*(.+?)\*\*", message_field1).group(1)
                    energy = int(energy)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Energy not found in clan raid message: {message.embeds[0].fields}',
                        message
                    )
                    return
                current_time = datetime.utcnow().replace(microsecond=0)
                clan_raid = await clans.insert_clan_raid(clan.clan_name, user.id, energy, current_time)
                if not clan_raid.raid_time == current_time:
                    if settings.DEBUG_MODE:
                        await message.channel.send(
                            'There was an error adding the raid to the leaderboard. Please tell Miri he\'s an idiot.'
                        )
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                if clan.stealth_current >= clan.stealth_threshold:
                    alert_message = f'{alert_message_prefix}guild raid'
                else:
                    alert_message = f'{alert_message_prefix}guild upgrade'
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


# Initialization
def setup(bot):
    bot.add_cog(ClanCog(bot))