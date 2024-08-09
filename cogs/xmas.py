# xmas.py

import asyncio
from datetime import datetime, timedelta
import random
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


CHRISTMAS_AREA_ENABLED = (
    'Christmas area mode enabled. Reminders are reduced by 10%.\n'
)
CHRISTMAS_AREA_DISABLED = (
    'Christmas area mode disabled. Your reminders are back to normal.\n'
)

ACTIVITIES_AFFECTED_BY_A0 = (
    'adventure',
    'arena',
    'clan',
    'chimney',
    'epic',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'training',
    'work',
)

class ChristmasCog(commands.Cog):
    """Cog that contains the horse festival detection commands"""
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
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = message_footer = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: message_title = str(embed.title)
            if embed.footer is not None:
                if embed.footer.text is not None:
                    message_footer = embed.footer.text

            # Chimney cooldown
            search_strings = [
                'you have went through a chimney recently', #English
                'has pasado por una chimenea recientemente', #Spanish
                'você passou por uma chaminé recentemente', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
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
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the xmas chimney cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CHIMNEY,
                                                    user=user, user_name=user_name)
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
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
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
                current_time = utils.utcnow()
                stephans_day = datetime(year=current_time.year, month=12, day=26, hour=0, minute=0, second=0)
                if current_time >= stephans_day: return
                user_id = user_name = None
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
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a user for the advent calendar message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CALENDAR,
                                                    user=user, user_name=user_name)
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
                current_time = utils.utcnow()
                midnight_today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = midnight_today + timedelta(days=1, seconds=random.randint(60, 300))
                time_left = end_time - current_time
                user_command = await functions.get_slash_command(user_settings, 'xmas calendar')
                reminder_message = user_settings.alert_advent.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'advent-calendar', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # Opening eternal presents
            search_strings = [
                'you can open up to 10 presents', #English
                'você pode abrir até 10 presentes', #Spanish & Portuguese
            ]
            if any(search_string in message_footer.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is not None: return
                user_command_message = (
                    await messages.find_message(message.channel.id, regex.COMMAND_XMAS_OPEN_ETERNAL)
                )
                if user_command_message is None: return
                if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_eternal_present.enabled: return
                user_command = await functions.get_slash_command(user_settings, 'xmas open')
                reminder_message = user_settings.alert_eternal_present.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'eternal-presents', timedelta(hours=24),
                                                         message.channel.id, reminder_message)
                )   
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # ETERNAL presents from inventory
            search_strings = [
                "— inventory", #All languages
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                if icon_url is None: return
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_MENU)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        return
                    interaction_user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        return
                if interaction_user not in embed_users: return
                if not user_settings.bot_enabled: return
                field_values = ''
                for field in embed.fields:
                    field_values = f'{field_values}\n{field.value}'
                present_eternal_count = 0
                present_eternal_match = re.search(r"eternal present\*\*: ([0-9,]+)", field_values, re.IGNORECASE)
                
                if present_eternal_match:
                    present_eternal_count = int(present_eternal_match.group(1).replace(',',''))
                if user_settings.inventory.present_eternal != present_eternal_count:
                    await user_settings.update(inventory_present_eternal=present_eternal_count)


        if not message.embeds:
            message_content = message.content

            # Chimney
            search_strings = [
                'went through a chimney', #English
                'se metió por una chimenea', #Spanish
                'passou por uma chaminé', #Portuguese
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
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CHIMNEY,
                                                    user_name=user_name)
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
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'chimney')
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'xmas chimney')
                reminder_message = user_settings.alert_chimney.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'chimney', time_left,
                                                         message.channel.id, reminder_message)
                )
                asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'chimney'))
                await functions.add_reminder_reaction(message, reminder, user_settings)
                search_strings_stuck = [
                    'now stuck in the chimney', #English
                    'atascó en la chimenea', #Spanish
                    'now stuck in the chimney', #TODO: Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_stuck):
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'unstuck', timedelta(minutes=5),
                                                             message.channel.id,
                                                             '{name} Hey! Good news! You got unstuck from that chimney!')
                    )

            # Turn on christmas area mode, gingerbread
            search_strings = [
                'has teleported to the **christmas area**', #English
                'se ha teletransportado al **área de navidad**', #Spanish
                'se teletransportou para a **zona de natal**', #Portuguese
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
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_EAT_GINGERBREAD,
                                                    user_name=user_name)
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
                    await reminders.reduce_reminder_time_percentage(user_settings, 10, ACTIVITIES_AFFECTED_BY_A0)
                    await message.reply(
                        CHRISTMAS_AREA_ENABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )
                if user_settings.current_area != 0: await user_settings.update(current_area=0)

            # Turn off christmas area mode when changing area or using a candy cane
            search_strings = [
                'has moved to the area #', #English, area change
                'starts to fly and travels to the next area!', #English, candy cane
                'se movio al área #', #Spanish, area change
                'se movio al área #', #TODO: Spanish, candy cane
                'foi movido para a área #', #Portuguese, area change
                'foi movido para a área #', #TODO: Portuguese, candy cane
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
                        await errors.log_error('Couldn\'t find a user for the xmas area change / candy cane message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_AREA_MOVE_CANDY_CANE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas area change / candy cane message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if user_settings.christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=False)
                    await reminders.increase_reminder_time_percentage(user_settings, 10, ACTIVITIES_AFFECTED_BY_A0)
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
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
            ):
                event_mobs = [
                   'christmas slime',
                   'bunny slime', 
                   'horslime', 
                ]
                if any(mob in message_content.lower() for mob in event_mobs): return
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
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT_ADVENTURE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for the xmas hunt/adv change message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                monsters_christmas = [
                    '**Elf**',
                    '**Christmas Reindeer**',
                    '**Snowman**',
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
                    await reminders.reduce_reminder_time_percentage(user_settings, 10, ACTIVITIES_AFFECTED_BY_A0)
                    await message.reply(
                        CHRISTMAS_AREA_ENABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )
                if user_settings.christmas_area_enabled and not christmas_area_enabled:
                    await user_settings.update(christmas_area_enabled=False)
                    await reminders.increase_reminder_time_percentage(user_settings, 10, ACTIVITIES_AFFECTED_BY_A0)
                    await message.reply(
                        CHRISTMAS_AREA_DISABLED.format(cd=await functions.get_slash_command(user_settings, 'cd'))
                    )

            # Cookies and milk
            search_strings = [
                '`cookies and milk` successfully crafted!', #English
                '`cookies and milk` crafteado con éxito!', #Spanish
                '`cookies and milk` craftado com sucesso!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CRAFT_COOKIES_AND_MILK)
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
                    r'reset: (.+?)$', #English
                    r'cooldown\(s\): (.+?)$', #Spanish
                    r'resetados: (.+?)$', #Portuguese
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


            # Eternal present cooldown
            search_strings = [
                'you cannot open eternal presents', #English
                'you cannot open eternal presents', #TODO: Spanish
                'you cannot open eternal presents', #TODO: Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = message.mentions[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_eternal_present.enabled: return
                timestring_match = re.search(r"for \*\*(.+?)\*\*", message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1))
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = utils.utcnow() - bot_answer_time
                time_left -= time_elapsed
                if time_left < timedelta(0): return
                user_command = await functions.get_slash_command(user_settings, 'xmas open')
                reminder_message = user_settings.alert_eternal_present.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'eternal-presents', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(ChristmasCog(bot))