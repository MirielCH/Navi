# work.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings


class WorkCog(commands.Cog):
    """Cog that contains the work detection commands"""
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

            # Work cooldown
            search_strings = [
                'you have already got some resources', #English
                'ya conseguiste algunos recursos', #Spanish
                'você já tem alguns recursos', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
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
                            await errors.log_error('User not found in work cooldown message.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in work cooldown message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_work.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    user_command = await functions.get_slash_command(user_settings, interaction.name)
                    last_work_command = interaction.name
                else:
                    regex = r"^rpg\s+(?:"
                    for command in strings.WORK_COMMANDS:
                        regex = fr'{regex}{command}\b|'
                    regex = fr'{regex.strip("|")})'
                    user_command_message, user_command = (
                            await functions.get_message_from_channel_history(message.channel, regex, user)
                        )
                    for command in strings.WORK_COMMANDS:
                        if command in user_command:
                            last_work_command = command
                            break
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the work cooldown message.', message)
                        return
                    user_command = f'`{user_command}`'
                await user_settings.update(last_work_command=last_work_command)
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
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
                ':crossed_sword:', #Ruby dragon event, all languages
                'guildring', #Stuff bought from guild shop, all languages
            ]
            search_strings = [
                '** got ', #English
                '** consiguió ', #Spanish
                '** conseguiu ', #Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and all(search_string not in message_content.lower() for search_string in excluded_strings)):
                user_name = user_command = last_work_command = None
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
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in work message.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(f'User not found for user name {user_name} in work message.', message)
                    return
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
                    user_command = await functions.get_slash_command(user_settings, interaction.name)
                    last_work_command = interaction.name
                else:
                    regex = r"^rpg\s+(?:"
                    for command in strings.WORK_COMMANDS:
                        regex = fr'{regex}{command}\b|'
                    regex = fr'{regex.strip("|")})'
                    user_command_message, user_command = (
                            await functions.get_message_from_channel_history(message.channel, regex, user)
                        )
                    if user_command_message is None:
                        search_strings_chainsaw = [
                            'three chainsaw', #English
                            'tres motosierras', #Spanish
                            'três serras', #Portuguese
                            'ultra log', #All languages
                            'ultimate log', #All languages
                        ]
                        search_strings_bowsaw = [
                            'two bow saw', #English
                            'dos arcos de sierra', #Spanish
                            'dois serra de arcos', #Portuguese
                        ]
                        search_strings_axe = [
                            'axe', #English
                            'hacha', #Spanish
                            'machado', #Portuguese
                        ]
                        search_strings_bigboat = [
                            'three nets', #English
                            'tres redes', #Spanish
                            'três redes', #Portuguese
                        ]
                        search_strings_boat = [
                            'two nets', #English
                            'dos redes', #Spanish
                            'duas redes', #Portuguese
                        ]
                        search_strings_net = [
                            'a **net**', #English
                            'una **red**', #Spanish
                            'uma **rede**', #Portuguese
                        ]
                        search_strings_greenhouse = [
                            'two tractors', #English
                            'dos tractores', #Spanish
                            'dois tratores', #Portuguese
                        ]
                        search_strings_tractor = [
                            'tractor', #English & Spanish
                            'trator', #Portuguese
                        ]
                        search_strings_ladder = [
                            'both hands', #English
                            'ambas manos', #Spanish
                            'ambas as mãos', #Portuguese
                        ]
                        search_strings_dynamite = [
                            'four drills', #English
                            'cuatro taladros', #Spanish
                            'quatro brocas', #Portuguese
                        ]
                        search_strings_drill = [
                            'two drills', #English
                            'dos taladros', #Spanish
                            'duas brocas', #Portuguese
                        ]
                        search_strings_pickaxe = [
                            'pickaxe', #English
                            'un pico', #Spanish
                            'uma picareta', #Portuguese
                        ]
                        if any(search_string in message_content.lower() for search_string in search_strings_chainsaw):
                            action = 'chainsaw'
                        elif any(search_string in message_content.lower() for search_string in search_strings_bowsaw):
                            action = 'bowsaw'
                        elif any(search_string in message_content.lower() for search_string in search_strings_axe):
                            action = 'axe'
                        elif any(search_string in message_content.lower() for search_string in search_strings_bigboat):
                            action = 'bigboat'
                        elif any(search_string in message_content.lower() for search_string in search_strings_boat):
                            action = 'boat'
                        elif any(search_string in message_content.lower() for search_string in search_strings_net):
                            action = 'net'
                        elif any(search_string in message_content.lower() for search_string in search_strings_greenhouse):
                            action = 'greenhouse'
                        elif any(search_string in message_content.lower() for search_string in search_strings_tractor):
                            action = 'tractor'
                        elif any(search_string in message_content.lower() for search_string in search_strings_ladder):
                            action = 'ladder'
                        elif any(search_string in message_content.lower() for search_string in search_strings_dynamite):
                            action = 'dynamite'
                        elif any(search_string in message_content.lower() for search_string in search_strings_drill):
                            action = 'drill'
                        elif any(search_string in message_content.lower() for search_string in search_strings_pickaxe):
                            action = 'pickaxe'
                        elif 'coins' in message_content.lower() or 'ruby' in message_content.lower(): action = 'mine'
                        elif 'log' in message_content.lower(): action = 'chop'
                        elif 'fish' in message_content.lower(): action = 'fish'
                        elif 'apple' in message_content.lower() or 'banana' in message_content.lower():
                            action = 'pickup'
                        else: action = '[work command]'
                        user_command = f'rpg {action}'
                    user_command = f'`{user_command}`'
                    for command in strings.WORK_COMMANDS:
                        if command in user_command:
                            last_work_command = command
                            break
                if last_work_command is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for work message.', message)
                    return
                await user_settings.update(last_work_command=last_work_command)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)
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
                        await message.add_reaction(emojis.WOAH_THERE)
                    if any(search_string in message_content.lower() for search_string in search_strings_mine_proc):
                        await message.add_reaction(emojis.SWEATY)
                    if any(search_string in message_content.lower() for search_string in search_strings_fish_proc):
                        await message.add_reaction(emojis.FISHPOGGERS)
                    if any(search_string in message_content.lower() for search_string in search_strings_pickup_proc):
                        await message.add_reaction(emojis.WOW)
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
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                interaction = await functions.get_interaction(message)
                if interaction is not None: return
                user_name = user_command = None
                user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE, message_content)
                if user_name_match:
                    user_name = await functions.encode_text(user_name_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await('User not found in work event non-slash message.', message)
                    return
                user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in work event non-slash message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                if not user_settings.alert_work.enabled: return
                regex = r"^rpg\s+(?:"
                for command in strings.WORK_COMMANDS:
                    regex = fr'{regex}{command}\b|'
                regex = fr'{regex.strip("|")})'
                user_command_message, user_command = (
                    await functions.get_message_from_channel_history(message.channel, regex, user)
                )
                if user_command_message is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for the work event non-slash message.', message)
                    return
                for command in strings.WORK_COMMANDS:
                    if command in user_command:
                        last_work_command = command
                        break
                user_command = f'`{user_command}`'
                await user_settings.update(last_work_command=last_work_command)
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)

            # Work event slash (all languages)
            if  (':x:' in message_content.lower()
                 or ':crossed_swords:' in message_content.lower()
                 or ':zzz:' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is None: return
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
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)



# Initialization
def setup(bot):
    bot.add_cog(WorkCog(bot))