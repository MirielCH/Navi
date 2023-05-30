# work.py

import asyncio
from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, tracking, users
from resources import emojis, exceptions, functions, regex, settings, strings


class WorkCog(commands.Cog):
    """Cog that contains the work detection commands"""
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
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

            # Work cooldown
            search_strings = [
                'you have already got some resources', #English
                'ya conseguiste algunos recursos', #Spanish
                'você já tem alguns recursos', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User name not found in work cooldown message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_WORK,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for work cooldown message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_work.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    last_work_command = interaction.name
                else:
                    for command in strings.WORK_COMMANDS:
                        if command in user_command_message.content.lower():
                            last_work_command = command
                            break
                if last_work_command is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for work cooldown message.', message)
                    return
                user_command = await functions.get_slash_command(user_settings, last_work_command)
                await user_settings.update(last_work_command=last_work_command)
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in work cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Work
            excluded_strings = [
                'hunting together', #English, hunt
                'cazando juntos', #Spanish, hunt
                'caçando juntos', #Portuguese, hunt
                '** found', #English, hunt/adventure
                '** encontr', #Spanish, Portuguese, hunt/adventure
                '** plant', #English, Spanish, Portuguese, farm
                '** throws', #English, world boss
                '** tiró', #Spanish, MISSING, world boss
                '** jogou', #Portuguese, MISSING, world boss
                'new quest', #English, quest
                'nueva misión', #Spanish, quest
                'nova missão', #Portuguese, quest
                'extra life points', #English, overheal
                'puntos extras de vida', #Spanish, overheal
                'pontos de vida extras', #Portuguese, overheal
                ':crossed_swords:', #Ruby dragon event, all languages
                '⚔️', #Ruby dragon event, all languages
                'guildring', #Stuff bought from guild shop, all languages
                'zombie', #Zombie horde hunt event, all languages
                'well done', #English, training
                'bien hecho', #Spanish, training
                'muito bem', #Portuguese, training
                'suspicious broom', #All languages, hal boo
                '**minin\'tboss** event', #English minin'tboss
                '**big arena** event', #English big arena
                'evento **minin\'tboss**', #Spanish, Portuguese minin't boss
                'evento de **big arena**', #Spanish, Portuguese big arena
                'seed in the ground...', #English, farm
                'en el suelo...', #Spanish, farm
                'no solo...', #Portuguese, farm
                'chimney', #English, xmas chimney
                'the next race is in', #English, horse race
                'la siguiente carrera es en', #Spanish, horse race
                'próxima corrida é em', #Portuguese, horse race
                'contribu', #All languages, void contributions
            ]
            search_strings = [
                '** got ', #English
                '** consiguió ', #Spanish
                '** conseguiu ', #Portuguese
            ]
            search_strings_work_items = [
                'wooden log',
                'epic log',
                'super log',
                '**mega** log',
                '**hyper** log',
                'ultimate log',
                'ultra log',
                'normie fish',
                'golden fish',
                'epic fish',
                'super fish',
                'apple',
                'banana',
                'watermelon',
                'ruby',
                'coins',
                'nothing',
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and all(search_string not in message_content.lower() for search_string in excluded_strings)
                and any(search_string in message_content.lower() for search_string in search_strings_work_items)):
                user_name = user_command = last_work_command = user_command_message = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    search_patterns = [
                        r'[!1] \*\*(.+?)\*\* got', #English 1
                        r'\?\?\?\?\? \*\*(.+?)\*\* got', #English 2
                        r'WOOAAAA!! (.+?)\*\* got', #English 3
                        r'WwWOoOOoOAAa!!!1 (.+?)\*\* got', #English 4
                        r'\.\.\. \*\*(.+?)\*\* got', #English 5
                        r'\*\*(.+?)\*\* got', #English 6
                        r'[!1] \*\*(.+?)\*\* consiguió', #Spanish 1, UNCONFIRMED
                        r'\?\?\?\?\? \*\*(.+?)\*\* consiguió', #Spanish 2, UNCONFIRMED
                        r'WOOAAAA!! (.+?)\*\* consiguió', #Spanish 3, UNCONFIRMED
                        r'WwWOoOOoOAAa!!!1 (.+?)\*\* consiguió', #Spanish 4, UNCONFIRMED
                        r'\.\.\. \*\*(.+?)\*\* consiguió', #Spanish 5, UNCONFIRMED
                        r'\*\*(.+?)\*\* consiguió', #Spanish 6
                        r'[!1] \*\*(.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 1, UNCONFIRMED
                        r'\?\?\?\?\? \*\*(.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 2, UNCONFIRMED
                        r'WOOAAAA!! (.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 3, UNCONFIRMED
                        r'WwWOoOOoOAAa!!!1 (.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 4, UNCONFIRMED
                        r'\.\.\. \*\*(.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 5, UNCONFIRMED
                        r'\*\*(.+?)\*\* (?:recebeu|conseguiu)', #Portuguese 6
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User name not found in work message.', message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_WORK,
                                                    user=user, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for work message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                if not user_settings.alert_work.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    if interaction.name not in strings.WORK_COMMANDS: return
                    last_work_command = interaction.name
                else:
                    for command in strings.WORK_COMMANDS:
                        if command in user_command_message.content.lower():
                            last_work_command = command
                            break
                if last_work_command is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for work message.', message)
                    return
                user_command = await functions.get_slash_command(user_settings, last_work_command)
                await user_settings.update(last_work_command=last_work_command)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.reactions_enabled:
                    search_strings_chop_proc = [
                        'quite a large leaf', #English
                        'una bastante grande', #Spanish
                        'uma folha bem grande', #Portuguese
                    ]
                    search_strings_mine_proc = [
                        'mined with too much force', #English
                        'minó con demasiada fuerza', #Spanish
                        'minerado com muita força', #Portugese
                    ]
                    search_strings_fish_proc = [
                        'for some reason, one of the fish was carrying', #English
                        'por alguna razón, uno de los peces llevaba', #Spanish
                        'por algum motivo, um dos peixes estava carregando', #Portuguese
                    ]
                    search_strings_pickup_proc = [
                        'rubies in it', #English
                        'uno de ellos llevaba', #Spanish
                        'um deles tinha', #Portuguese
                    ]
                    if any(search_string in message_content.lower() for search_string in search_strings_chop_proc):
                        await message.add_reaction(emojis.PEPE_WOAH_THERE)
                    if any(search_string in message_content.lower() for search_string in search_strings_mine_proc):
                        await message.add_reaction(emojis.PANDA_SWEATY)
                    if any(search_string in message_content.lower() for search_string in search_strings_fish_proc):
                        await message.add_reaction(emojis.FISHPOGGERS)
                    if any(search_string in message_content.lower() for search_string in search_strings_pickup_proc):
                        await message.add_reaction(emojis.PEEPO_WOW)
                    if 'mega log' in message_content.lower() or '**mega** log' in message_content.lower():
                        await message.add_reaction(emojis.FIRE)
                    elif 'hyper log' in message_content.lower() or '**hyper** log' in message_content.lower():
                        await message.add_reaction(emojis.FIRE)
                    elif 'ultra log' in message_content.lower() or '**ultra** log' in message_content.lower():
                        await message.add_reaction(emojis.PEEPO_WOAH)
                    if 'watermelon' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_MELON)
                    if 'ultimate log' in message_content.lower() or '**ultimate** log' in message_content.lower():
                        await message.add_reaction(emojis.WOAH)
                    if 'super fish' in message_content.lower() or '**super** log' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_FISH)
                    if '<:coolness' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_COOL)

            # Work event non-slash (always English)
            search_strings = [
                'it seems like the dragon just had 1 point of life',
                'the dragon did not move an inch',
                'you slept well and the items respawned',
                '**epic npc** came here to gave you',
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                interaction = await functions.get_interaction(message)
                slash_command = True if interaction is not None else False
                if interaction is None:
                    user_name = user_command = user_command_message = None
                    user_name_match = re.search(r'\s\*\*(.+?)\*\*\s(?:cried|fights|sleeps|ran away)', message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_WORK,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for work event non-slash message.', message)
                        return
                    user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled: return
                    current_time = datetime.utcnow().replace(microsecond=0)
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                    if not user_settings.alert_work.enabled: return
                    for command in strings.WORK_COMMANDS:
                        if command in user_command_message.content.lower():
                            last_work_command = command
                            break
                    if last_work_command is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for work event non-slash message.', message)
                        return
                    await user_settings.update(last_work_command=last_work_command)
                    user_command = await functions.get_slash_command(user_settings, last_work_command)
                    time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                        asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                    await functions.add_reminder_reaction(message, reminder, user_settings)

            # Work event slash (all languages)
            search_strings = [
                ':x:',
                ':crossed_swords:',
                '⚔️',
                ':zzz:',
                '💤',
                ':sweat_drops:',
                '💦',
            ]
            if  any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is not None:
                    if interaction.name not in strings.WORK_COMMANDS: return
                    last_work_command = interaction.name
                    user = interaction.user
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    await user_settings.update(last_work_command=last_work_command)
                    if not user_settings.bot_enabled: return
                    user_command = await functions.get_slash_command(user_settings, interaction.name)
                    current_time = datetime.utcnow().replace(microsecond=0)
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                    if not user_settings.alert_work.enabled: return
                    time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    if user_settings.auto_ready_enabled and user_settings.ready_after_all_commands:
                        asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                    await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(WorkCog(bot))