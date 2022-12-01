# xmas.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


CHRISTMAS_AREA_ENABLED = (
    'Christmas area mode enabled. This reduces your reminders by 10%.\n'
    'Note that this does not affect running reminders. Use {cd} to update them.'
)
CHRISTMAS_AREA_DISABLED = (
    'Christmas area mode disabled. Your reminders are back to normal.\n'
    'Note that this does not affect running reminders. Use {cd} to update them.'
)

class ChristmasCog(commands.Cog):
    """Cog that contains the horse festival detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
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
            message_author = message_title = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Chimney cooldown
            search_strings = [
                'you have went through a chimney recently', #English
                'you have went through a chimney recently', #Spanish, MISSING
                'you have went through a chimney recently', #Portuguese, MISSING
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the xmas chimney cooldown message.', message)
                            return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_XMAS_CHIMNEY,
                            user=user, user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas chimney cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_chimney.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'xmas chimney')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in xmas chimney message.', message)
                    return
                time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_chimney.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'chimney', time_left,
                                                        message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Advent calendar
            search_strings = [
                '— advent calendar', #All languages
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a user for the advent calendar message.', message)
                            return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_XMAS_CALENDAR,
                            user=user, user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas calendar message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_advent.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                midnight_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = midnight_today + timedelta(days=1, minutes=5)
                time_left = end_time - current_time
                user_command = await functions.get_slash_command(user_settings, 'xmas calendar')
                reminder_message = user_settings.alert_advent.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'advent-calendar', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content

            # Chimney
            search_strings = [
                'went through a chimney', #English
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
                        await errors.log_error('Couldn\'t find a user for the xmas chimney message.', message)
                        return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_XMAS_CHIMNEY,
                            user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas chimney message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_chimney.enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'chimney')
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'xmas chimney')
                reminder_message = user_settings.alert_chimney.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'chimney', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                search_strings_stuck = [
                    'now stuck on the chimney', #English
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_stuck):
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'unstuck', timedelta(minutes=5),
                                                             message.channel.id,
                                                             '{name} Hey! Good news! You got unstuck from that chimney!')
                    )
                if user_settings.auto_ready_enabled:
                    await functions.call_ready_command(self.bot, message, user)

            # Turn on christmas area mode, gingerbread
            search_strings = [
                'has teleported to the **christmas area**', #English
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
                        await errors.log_error('Couldn\'t find a user for the xmas gingerbread message.', message)
                        return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_XMAS_EAT_GINGERBREAD,
                            user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas gingerbread message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if not user_settings.christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=True)
                    await message.reply(
                        CHRISTMAS_AREA_ENABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )

            # Turn off christmas area mode, changing area
            search_strings = [
                'has moved to the area #', #English
                'se movio al área #', #Spanish
                'foi movido para a área #', #Portuguese
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
                        await errors.log_error('Couldn\'t find a user for the xmas area change message.', message)
                        return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_AREA_MOVE,
                            user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas area change message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if user_settings.christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=False)
                    await message.reply(
                        CHRISTMAS_AREA_DISABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )

            # Toggle christmas area mode, hunt and adventure
            search_strings = [
                'found a', #English
                'found the', #English
                'encontr', #Spanish, Portuguese
                'hunting together', #English
                'cazando juntos', #Spanish
                'caçando juntos', #Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(f'{monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'{monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(f'{monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
            ):
                if 'christmas slime' in message_content.lower(): return
                user_id = user_name = partner_name = None
                together = False
                user = await functions.get_interaction_user(message)
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
                if user is None:
                    if together:
                        search_patterns = [
                           r"\*\*(.+?)\*\* and \*\*(.+?)\*\*", #English
                            r"\*\*(.+?)\*\* y \*\*(.+?)\*\*", #Spanish
                            r"\*\*(.+?)\*\* e \*\*(.+?)\*\*", #Portuguese
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            partner_name = user_name_match.group(2)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User names not found in xmas hunt together message.', message)
                            return
                    else:
                        search_patterns = [
                            r"\*\*(.+?)\*\* found a", #English
                            r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a user name for the xmas hunt/adv message.', message)
                            return
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_HUNT_ADVENTURE,
                            user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for the xmas hunt/adv change message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                monsters_christmas = [
                    '**Elf**',
                    '**Christmas Reindeer**',
                    '**Snowman**',
                    'Krampus',
                    '**Krampus**',
                    '**Yeti**',
                    '**Hyper Giant Ice Block**',
                ]
                if together:
                    partner_start_pos = message_content.find(f'**{partner_name}**:')
                    if partner_start_pos == -1:
                        partner_start_pos = message_content.find(f'while **{partner_name}**')
                    message_content = message_content[:partner_start_pos]
                christmas_area_enabled = False
                for monster in monsters_christmas:
                    if monster.lower() in message_content.lower():
                        christmas_area_enabled = True
                        break
                if not user_settings.christmas_area_enabled and christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=True)
                    await message.reply(
                        CHRISTMAS_AREA_ENABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )
                if user_settings.christmas_area_enabled and not christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=False)
                    await message.reply(
                        CHRISTMAS_AREA_DISABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )

            # Cookies and milk
            search_strings = [
                '`cookies and milk` successfully crafted!', #English
                '`cookies and milk` successfully crafted!', #Spanish, MISSING
                '`cookies and milk` successfully crafted!', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = await functions.get_message_from_channel_history(
                        message.channel, regex.COMMAND_XMAS_CRAFT_COOKIES_AND_MILK
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas cookies and milk message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                search_patterns = [
                    f'reset: (.+?)$', #English
                ]
                activites_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not activites_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t read reset activites from xmas cookies and milk message.', message)
                    return
                activites = activites_match.group(1).split(', ')
                for activity in activites:
                    if activity in strings.ACTIVITIES_ALIASES:
                        activity = strings.ACTIVITIES_ALIASES[activity]
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, activity)
                    except exceptions.NoDataFoundError:
                        continue
                    await reminder.delete()
                    if reminder.record_exists:
                        await functions.add_warning_reaction(message)
                        await errors.log_error(f'Had an error deleting the reminder with activity "{activity}".', message)
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                if user_settings.auto_ready_enabled:
                    await functions.call_ready_command(self.bot, message, user)


# Initialization
def setup(bot):
    bot.add_cog(ChristmasCog(bot))