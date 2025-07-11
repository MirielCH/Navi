# summer.py

import asyncio
from datetime import datetime, timedelta, timezone
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class SummerCog(commands.Cog):
    """Cog that contains the summer event detection commands"""
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
            embed_author = message_title = message_description = icon_url = ''
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: message_title = str(embed.title)
            if embed.description is not None: message_description = str(embed.description)
            
            # Surf cooldown
            search_strings = [
                'you have surfed recently', #English
                'you have surfed recently', #TODO: Spanish
                'you have surfed recently', #TODO: Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_SMR_SURF,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in surf cooldown message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_surf.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                user_command = await functions.get_slash_command(user_settings, 'smr surf')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in surf cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_surf.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'surf', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Color tournament
            search_strings = [
                'complete a surf course to improve your team score', #English
                'complete a surf course to improve your team score', #TODO: Spanish
                'complete a surf course to improve your team score', #TODO: Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_SMR_COLOR_TOURNAMENT)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in color tournament embed.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_color_tournament.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                current_time = utils.utcnow()
                next_monday = current_time.date() + timedelta(days=(0 - current_time.weekday() - 1) % 7 + 1)
                next_monday_dt = datetime(year=next_monday.year, month=next_monday.month, day=next_monday.day, hour=0, minute=1, second=0, microsecond=0, tzinfo=timezone.utc)
                time_left = next_monday_dt - utils.utcnow() + timedelta(seconds=random.randint(0, 600))
                user_command = await functions.get_slash_command(user_settings, 'smr color tournament')
                reminder_message = user_settings.alert_color_tournament.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'color-tournament', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)      

            # Surf helper
            search_strings = [
                "try not to slip off the surfboard", #English
                "try not to slip off the surfboard", #TODO: Spanish
                "try not to slip off the surfboard", #TODO: Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_SMR_SURF,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in surf message for surf helper.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.surf_helper_enabled: return

                embed_field_names: str = ''
                for field in embed.fields:
                    embed_field_names = f'{embed_field_names} {field.name.lower()}'

                answer: str = ''
                if 'completely normal wave' in embed_field_names:
                    answer = (
                        f'**A**: **Low risk** to slip off, rewards 80 guild rings\n'
                        f'**B**: **Very low risk** to slip off, rewards 1 wishing token\n'
                    )
                elif 'inverted wave' in embed_field_names:
                    answer = (
                        f'**A**: **Very low risk** to slip off, rewards 20 coconuts\n'
                        f'**B**: **High risk** to slip off, rewards 3 EPIC lootboxes\n'
                    )
                elif 'insanely small wave' in embed_field_names:
                    answer = (
                        f'**A**: **Very low risk** to slip off, rewards 30 arena cookies\n'
                        f'**B**: **Very high risk** to slip off, rewards 1 OMEGA horse token\n'
                    )
                elif 'big wave' in embed_field_names:
                    answer = (
                        f'**A**: **Low risk** to slip off, rewards 1 EDGY lootbox\n'
                        f'**B**: **High risk** to slip off, rewards 10 TIME cookies\n'
                    )
                elif 'invisible wave' in embed_field_names:
                    answer = (
                        f'**A**: **Low risk** to slip off, rewards 35 chopped coconuts\n'
                        f'**B**: **Very high risk** to slip off, rewards 4 flasks\n'
                    )
                elif 'angry wave' in embed_field_names:
                    answer = (
                        f'**A**: **High risk** to slip off, rewards 2 flasks\n'
                        f'**B**: **Very high risk** to slip off, rewards 20 TIME cookies\n'
                    )
                else:
                    return
                if not user_settings.dnd_mode_enabled:
                    if user_settings.ping_after_message:
                        await message.channel.send(f'{answer}\n{user.mention}')
                    else:
                        await message.channel.send(f'{user.mention}\n{answer}')
                else:
                    await message.channel.send(answer)

                
        if not message.embeds:
            message_content = message.content

            # Surf
            search_strings = [
                'completed the surf course', #English, success
                'slipped off the surfboard', #English, fail
                'completed the surf course', #TODO: Spanish, success
                'slipped off the surfboard', #TODO: Spanish, fail
                'completed the surf course', #TODO: Portuguese, success
                'slipped off the surfboard', #TODO: Portuguese, fail
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for the surf message.', message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_SMR_SURF,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the surf message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_surf.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'surf')
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'smr surf')
                reminder_message = user_settings.alert_surf.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'surf', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'surf'))
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Joining color tournament from using drinks
            search_strings = [
                'team perk** until the end of this week!', #English
                'team perk** until the end of this week!', #TODO: Spanish
                'team perk** until the end of this week!', #TODO: Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and datetime.today().weekday() < 5):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_SMR_USE_DRINK)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the summer drink message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_color_tournament.enabled: return
                try:
                    reminder = await reminders.get_user_reminder(user_settings.user_id, 'color-tournament')
                except exceptions.NoDataFoundError:
                    current_time = utils.utcnow()
                    next_monday = current_time.date() + timedelta(days=(0 - current_time.weekday() - 1) % 7 + 1)
                    next_monday_dt = datetime(year=next_monday.year, month=next_monday.month, day=next_monday.day, hour=0, minute=1, second=0, microsecond=0, tzinfo=timezone.utc)
                    time_left = next_monday_dt - utils.utcnow() + timedelta(seconds=random.randint(0, 600))
                    user_command = await functions.get_slash_command(user_settings, 'smr color tournament')
                    reminder_message = user_settings.alert_color_tournament.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'color-tournament', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)
                    

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(SummerCog(bot))