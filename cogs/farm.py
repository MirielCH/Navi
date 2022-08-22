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
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Farm cooldown
            search_strings = [
                'you have farmed already', #English
                'ya cultivaste recientemente', #Spanish
                'você plantou recentemente', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                slash_command = True
                if user is None:
                    slash_command = False
                    user_command = 'rpg farm'
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in farm cooldown message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                    user_command_message, user_command = (
                        await functions.get_message_from_channel_history(
                            message.channel,
                            r"^rpg\s+farm\b\s*(?:carrot\b|potato\b|bread\b)?",
                            user
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error(
                            'Couldn\'t find a command for the farm cooldown message.',
                            message
                        )
                        return
                    user_command = f'`{user_command.strip()}`'
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in farm cooldown message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_farm.enabled: return
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'farm')
                else:
                    last_farm_seed = None
                    if 'carrot' in user_command:
                        last_farm_seed = 'carrot'
                    elif 'bread' in user_command:
                        last_farm_seed = 'bread'
                    elif 'potato' in user_command:
                        last_farm_seed = 'potato'
                    await user_settings.update(last_farm_seed=last_farm_seed)
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in farm cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Farm
            search_strings = [
               'seed in the ground...', #English
               'en el suelo...', #Spanish
               'no solo...', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = last_farm_seed = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    search_patterns = [
                        r"^\*\*(.+?)\*\* plant", #English, Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in farm message.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in farm message.', message)
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
                search_strings = [
                    '{} in the ground', #English
                    '{} en el suelo', #Spanish
                    '{} no solo', #Portuguese
                ]
                if any(search_string.format('bread seed') in message_content.lower() for search_string in search_strings):
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'farm')
                        user_command = f'{user_command} `seed: bread`'
                    else:
                        user_command = '`rpg farm bread`'
                    last_farm_seed = 'bread'
                elif any(search_string.format('carrot seed') in message_content.lower() for search_string in search_strings):
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'farm')
                        user_command = f'{user_command} `seed: carrot`'
                    else:
                        user_command = '`rpg farm carrot`'
                    last_farm_seed = 'carrot'
                elif any(search_string.format('potato seed') in message_content.lower() for search_string in search_strings):
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'farm')
                        user_command = f'{user_command} `seed: potato`'
                    else:
                        user_command = '`rpg farm potato`'
                    last_farm_seed = 'potato'
                else:
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'farm')
                    else:
                        user_command = '`rpg farm`'
                await user_settings.update(last_farm_seed=last_farm_seed)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'farm')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)
                search_strings = [
                    'also got', #English
                    'también consiguió', #Spanish
                    'também conseguiu', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings):
                    if 'potato seed**' in message_content.lower():
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.SEED_POTATO)
                    elif 'carrot seed**' in message_content.lower():
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.SEED_CARROT)
                    elif 'bread seed**' in message_content.lower():
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.SEED_BREAD)

            # Farm event non-slash (always English)
            if ('hits the floor with the' in message_content.lower()
                or 'is about to plant another seed' in message_content.lower()):
                interaction = await functions.get_interaction(message)
                if interaction is not None: return
                user_name = user_command = user_command_message = None
                user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE, message_content)
                if user_name_match:
                    user_name = await functions.encode_text(user_name_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in farm event non-slash message.', message)
                    return
                user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in farm event non-slash message.', message)
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
                user_command = '`rpg farm`'
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'farm')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)

            # Farm event slash (all languages)
            if  (('<:seed' in message_content.lower() and '!!' in message_content.lower())
                 or ':crossed_swords:' in message_content.lower()
                 or ':sweat_drops:' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is None: return
                if interaction.name != 'farm': return
                user_command = await functions.get_slash_command(user_settings, 'farm')
                user = interaction.user
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'farm', current_time)
                if not user_settings.alert_farm.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'farm')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)


# Initialization
def setup(bot):
    bot.add_cog(FarmCog(bot))