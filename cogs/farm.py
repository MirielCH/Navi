# farm.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings


class FarmCog(commands.Cog):
    """Cog that contains the farm detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Farm cooldown
            if 'you have farmed already' in message_title.lower():
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/farm'
                else:
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
                                f'User not found in farm cooldown message: {message.embeds[0].fields}',
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
                        f'User not found in farm cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_farm.enabled: return
                message_history = await message.channel.history(limit=50).flatten()
                if user_command is None:
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ') and 'farm' in msg.content.lower()
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the farm cooldown message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)

        if not message.embeds:
            message_content = message.content
            # Farm
            if 'have grown from the seed' in message_content.lower():
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\* plants", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in farm message: {message_content}',
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
                        f'User not found in farm message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'farm', current_time)
                if not user_settings.alert_farm.enabled: return
                message_history = await message.channel.history(limit=50).flatten()
                if 'bread seed in the ground' in message_content.lower():
                    user_command = 'rpg farm bread' if not slash_command else '/farm seed: bread'
                elif 'carrot seed in the ground' in message_content.lower():
                    user_command = 'rpg farm carrot' if not slash_command else '/farm seed: carrot'
                elif 'potato seed in the ground' in message_content.lower():
                    user_command = 'rpg farm potato' if not slash_command else '/farm seed: potato'
                else:
                    user_command = 'rpg farm' if not slash_command else '/farm'
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('farm')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[user_donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)
                if 'also got' in message_content.lower():
                    if 'potato seed**' in message_content.lower():
                        await message.add_reaction(emojis.SEED_POTATO)
                    elif 'carrot seed**' in message_content.lower():
                        await message.add_reaction(emojis.SEED_CARROT)
                    elif 'bread seed**' in message_content.lower():
                        await message.add_reaction(emojis.SEED_BREAD)

            # Farm event
            if ('hits the floor with the' in message_content.lower()
                or 'is about to plant another seed' in message_content.lower()):
                user_name = user_command = None
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/farm'
                else:
                    try:
                        user_name = re.search("\*\*(.+?)\*\*", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in farm event message: {message_content}',
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
                        f'User not found in farm event message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'farm', current_time)
                if not user_settings.alert_farm.enabled: return
                message_history = await message.channel.history(limit=50).flatten()
                if user_command is None:
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ') and 'farm' in msg.content.lower()
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the farm event message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('farm')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[user_donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)


# Initialization
def setup(bot):
    bot.add_cog(FarmCog(bot))