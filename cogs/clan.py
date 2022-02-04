# clan.py
# Contains clan detection commands

import re

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from database import clans, errors, cooldowns, reminders
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
                user_id = user_name = user = None
                try:
                    user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                except:
                    try:
                        user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                        user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    except Exception as error:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error(error)
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
                    await errors.log_error(f'User not found in clan cooldown message: {message}')
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
                bot_answer_time = message.created_at.replace(microsecond=0)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                alert_message = 'rpg guild raid' if clan.stealth_current >= clan.stealth_threshold else 'rpg guild upgrade'
                reminder: reminders.Reminder = (
                    await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                         clan.channel_id, alert_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)

            # Clan overview
            if 'your guild was raided' in message_footer.lower():
                if message.mentions: return # Yes that also disables it if you ping yourself but who does that
                try:
                    clan_name = re.search("^\*\*(.+?)\*\*", message_description).group(1)
                except Exception as error:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(error)
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_clan_name(clan_name)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled or clan.channel_id is None: return
                try:
                    stealth = re.search("STEALTH\*\*: (.+?)\\n", message_field1).group(1)
                    stealth = int(stealth)
                    await clan.update(stealth_current=stealth)
                except Exception as error:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(error)
                    return
                alert_message = 'rpg guild raid' if clan.stealth_current >= clan.stealth_threshold else 'rpg guild upgrade'
                if '`raid` | `upgrade`' in message_field1:
                    timestring = '0m 1s'
                else:
                    timestring = re.search(":clock4: \*\*(.+?)\*\*", message_field1).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring)
                reminder: reminders.Reminder = (
                    await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                         clan.channel_id, alert_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

            # Guild upgrade
            if ('guild successfully upgraded!' in message_description.lower()
                or 'guild upgrade failed!' in message_description.lower()):
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if msg.content.lower() == 'rpg guild upgrade' and not msg.author.bot:
                            user_command_message = msg
                            break
                if user_command_message is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error('Couldn\'t find a command for the clan upgrade message.')
                    return
                user = user_command_message.author
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                clan_stealth_before = clan.stealth_current
                try:
                    stealth = re.search("--> \*\*(.+?)\*\*", message_field0).group(1)
                    stealth = int(stealth)
                except Exception as error:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(error)
                    return
                await clan.update(stealth_current=stealth)
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                alert_message = 'rpg guild raid' if clan.stealth_current >= clan.stealth_threshold else 'rpg guild upgrade'
                reminder: reminders.Reminder = (
                    await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                         clan.channel_id, alert_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                    if clan.stealth_current >= clan.stealth_threshold: await message.add_reaction(emojis.YAY)
                    if clan.stealth_current == clan_stealth_before: await message.add_reaction(emojis.ANGRY)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)

            # Guild raid
            if ('** RAIDED **' in message_description and ':crossed_swords:' in message_description.lower()):
                user_name = user = None
                try:
                    user_name = re.search("\*\*(.+?)\*\* throws", message_field0).group(1)
                    user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                except Exception as error:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(error)
                    return
                for member in message.guild.members:
                    member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    if member_name == user_name:
                        user = member
                        break
                if user is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(f'User not found in clan raid message: {message}')
                    return
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(user.id)
                except exceptions.NoDataFoundError:
                    return
                if not clan.alert_enabled: return
                try:
                    energy = re.search("earned \*\*(.+?)\*\*", message_field1).group(1)
                    energy = int(energy)
                except Exception as error:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(error)
                    return
                current_time = datetime.utcnow().replace(microsecond=0)
                clan_raid = await clans.insert_clan_raid(clan.clan_name, user.id, energy, current_time)
                if not clan_raid.raid_time == current_time:
                    if settings.DEBUG_MODE:
                        await message.channel.send(
                            'There was an error adding the raid to the leaderboard. Please tell Miri he\'s an idiot.'
                        )
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('clan')
                bot_answer_time = message.created_at.replace(microsecond=0)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = timedelta(seconds=cooldown.actual_cooldown()) - time_elapsed
                alert_message = 'rpg guild raid' if clan.stealth_current >= clan.stealth_threshold else 'rpg guild upgrade'
                reminder: reminders.Reminder = (
                    await reminders.insert_clan_reminder(clan.clan_name, time_left,
                                                         clan.channel_id, alert_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)


# Initialization
def setup(bot):
    bot.add_cog(ClanCog(bot))