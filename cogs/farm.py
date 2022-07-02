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
            search_strings = [
                'you have farmed already', #English
                'ya cultivaste recientemente', #Spanish
                'você plantou recentemente', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/farm'
                else:
                    user_command = 'rpg farm'
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        user_name_match = await functions.get_match_from_patterns(strings.COOLDOWN_USERNAME_PATTERNS,
                                                                                  message_author)
                        try:
                            user_name = user_name_match.group(1)
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
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
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
                            if msg.content.lower().replace(' ','').startswith('rpgfarm') and msg.author == user:
                                if user_command_message.content.lower().startswith('rpgfarmcarrot'):
                                    user_command = f'{user_command} carrot'
                                elif user_command_message.content.lower().startswith('rpgfarmpotato'):
                                    user_command = f'{user_command} potato'
                                elif user_command_message.content.lower().startswith('rpgfarmbread'):
                                    user_command = f'{user_command} bread'
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
                timestring_match = await functions.get_match_from_patterns(strings.COOLDOWN_TIMESTRING_PATTERNS,
                                                                           message_title)
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
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
               'have grown from the seed', #English
               'crecieron de la semilla', #Spanish
               'partir da semente', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    search_patterns = [
                        "^\*\*(.+?)\*\* plant", #English, Spanish, Portuguese
                    ]
                    try:
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                        user_name = user_name_match.group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in farm message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
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
                search_strings = [
                    '{} in the ground', #English
                    '{} en el suelo', #Spanish
                    '{} no solo', #Portuguese
                ]
                if any(search_string.format('bread seed') in message_content.lower() for search_string in search_strings):
                    user_command = 'rpg farm bread' if not slash_command else '/farm seed: bread'
                elif any(search_string.format('carrot seed') in message_content.lower() for search_string in search_strings):
                    user_command = 'rpg farm carrot' if not slash_command else '/farm seed: carrot'
                elif any(search_string.format('potato seed') in message_content.lower() for search_string in search_strings):
                    user_command = 'rpg farm potato' if not slash_command else '/farm seed: potato'
                else:
                    user_command = 'rpg farm' if not slash_command else '/farm'
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'farm')
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
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
                try:
                    user_name = re.search("\*\*(.+?)\*\*", message_content).group(1)
                    user_name = await functions.encode_text(user_name)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in farm event non-slash message: {message_content}',
                        message
                    )
                    return
                user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in farm event non-slash message: {message_content}',
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
                user_command = 'rpg farm'
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'farm')
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Farm event slash (all languages)
            if  (('<:seed' in message_content.lower() and '!!' in message_content.lower())
                 or ':crossed_swords:' in message_content.lower()
                 or ':sweat_drops:' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is None: return
                if interaction.name != 'farm': return
                user_command = '/farm'
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
                reminder_message = user_settings.alert_farm.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'farm', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(FarmCog(bot))