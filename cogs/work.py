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
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
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
                                f'User not found in work cooldown message: {message.embeds[0].fields}',
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
                        f'User not found in work cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_work.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    user_command = f'/{interaction.name}'
                else:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = user_command = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ')
                                and any(command in msg.content.lower() for command in strings.WORK_COMMANDS)
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is not None:
                        user_command = user_command_message.content.lower()
                    else:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the work cooldown message.',
                            message
                        )
                        return
                timestring_match = await functions.get_match_from_patterns(strings.COOLDOWN_TIMESTRING_PATTERNS,
                                                                           message_title)
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
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
                '** found', #English, hunt/adventure
                '** plant', #English, Spanish, Portuguese, farm
                '** throws', #English, world boss
                'new quest', #English, quest
                'stan cazando juntos', #Spanish, hunt
                '** encontr', #Spanish, Portuguese, hunt/adventure
                '** throws', #Spanish, MISSING, world boss
                'nueva misión', #Spanish, quest
                'estão caçando juntos', #Portuguese, hunt
                '** throws', #Portuguese, MISSING, world boss
                'nova missão', #Portuguese, quest
                ':crossed_sword:', #Ruby dragon event, all languages
            ]
            search_strings = [
                '** got ', #English
                '** consiguió ', #Spanish
                '** conseguiu ', #Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and all(search_string not in message_content.lower() for search_string in excluded_strings)):
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    search_patterns = [
                        '[!1] \*\*(.+?)\*\* got', #English 1
                        '\?\?\?\?\? \*\*(.+?)\*\* got', #English 2
                        'WOOAAAA!! (.+?)\*\* got', #English 3
                        'WwWOoOOoOAAa!!!1 (.+?)\*\* got', #English 4
                        '\.\.\. \*\*(.+?)\*\* got', #English 5
                        '\*\*(.+?)\*\* got', #English 6
                        '[!1] \*\*(.+?)\*\* consiguió', #Spanish 1, UNCONFIRMED
                        '\?\?\?\?\? \*\*(.+?)\*\* consiguió', #Spanish 2, UNCONFIRMED
                        'WOOAAAA!! (.+?)\*\* consiguió', #Spanish 3, UNCONFIRMED
                        'WwWOoOOoOAAa!!!1 (.+?)\*\* consiguió', #Spanish 4, UNCONFIRMED
                        '\.\.\. \*\*(.+?)\*\* consiguió', #Spanish 5, UNCONFIRMED
                        '\*\*(.+?)\*\* consiguió', #Spanish 6
                        '[!1] \*\*(.+?)\*\* (recebeu|conseguiu)', #Portuguese 1, UNCONFIRMED
                        '\?\?\?\?\? \*\*(.+?)\*\* (recebeu|conseguiu)', #Portuguese 2, UNCONFIRMED
                        'WOOAAAA!! (.+?)\*\* (recebeu|conseguiu)', #Portuguese 3, UNCONFIRMED
                        'WwWOoOOoOAAa!!!1 (.+?)\*\* (recebeu|conseguiu)', #Portuguese 4, UNCONFIRMED
                        '\.\.\. \*\*(.+?)\*\* (recebeu|conseguiu)', #Portuguese 5, UNCONFIRMED
                        '\*\*(.+?)\*\* (recebeu|conseguiu)', #Portuguese 6
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in work message: {message.content}',
                            message
                        )
                        return
                    user_name = user_name_match.group(1)
                    user_name = await functions.encode_text(user_name)
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found for user name {user_name} in work message: {message.content}',
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
                    await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                if not user_settings.alert_work.enabled: return
                if slash_command:
                    interaction = await functions.get_interaction(message)
                    user_command = f'/{interaction.name}'
                else:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ')
                                and any(command.lower() in msg.content.lower() for command in strings.WORK_COMMANDS)
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is not None:
                        for command in strings.WORK_COMMANDS:
                            if command in user_command_message.content.lower():
                                user_command = f'rpg {command}'
                                break
                    else:
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
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.reactions_enabled:
                    search_strings_chop_proc = [
                        'quite a large leaf', #English
                        'una bastante grande', #Spanish
                        'uma folha bem grande', #Portuguese, RECHECK AT LAUNCH
                    ]
                    search_strings_mine_proc = [
                        'mined with too much force', #English
                        'minó con demasiada fuerza', #Spanish
                        'minó con demasiada fuerza', #Portugese, MISSING
                    ]
                    search_strings_fish_proc = [
                        'for some reason, one of the fish was carrying', #English
                        'por alguna razón, uno de los peces llevaba', #Spanish
                        'por alguna razón, uno de los peces llevaba', #Portuguese, MISSING
                    ]
                    search_strings_pickup_proc = [
                        'rubies in it', #English
                        'uno de ellos llevaba', #Spanish, RECHECK AT LAUNCH
                        'uno de ellos llevaba', #Portuguese, MISSING
                    ]
                    if any(search_string in message_content.lower() for search_string in search_strings_chop_proc):
                        await message.add_reaction(emojis.WOAH_THERE)
                    elif any(search_string in message_content.lower() for search_string in search_strings_mine_proc):
                        await message.add_reaction(emojis.SWEATY)
                    elif any(search_string in message_content.lower() for search_string in search_strings_fish_proc):
                        await message.add_reaction(emojis.FISHPOGGERS)
                    elif any(search_string in message_content.lower() for search_string in search_strings_pickup_proc):
                        await message.add_reaction(emojis.WOW)
                    elif 'mega log' in message_content.lower():
                        await message.add_reaction(emojis.FIRE)
                    elif 'hyper log' in message_content.lower():
                        await message.add_reaction(emojis.FIRE)
                    elif 'ultra log' in message_content.lower():
                        await message.add_reaction(emojis.PEEPO_WOAH)
                    elif 'watermelon' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_MELON)
                    elif 'ultimate log' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_COOL)
                    elif 'super fish' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_FISH)

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
                try:
                    user_name = re.search("\*\*(.+?)\*\*", message_content).group(1)
                    user_name = await functions.encode_text(user_name)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await(
                        f'User not found in work event non-slash message: {message_content}',
                        message
                    )
                    return
                user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in work event non-slash message: {message_content}',
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
                    await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                if not user_settings.alert_work.enabled: return
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        if (msg.content.lower().startswith('rpg ')
                            and any(command.lower() in msg.content.lower() for command in strings.WORK_COMMANDS)
                            and msg.author == user):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a command for the work event non-slash message.',
                        message
                    )
                    return
                for command in strings.WORK_COMMANDS:
                    if command in user_command_message:
                        user_command = f'rpg {command}'
                        break
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Work event slash (all languages)
            if  (':x:' in message_content.lower()
                 or ':crossed_swords:' in message_content.lower()
                 or ':zzz:' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is None: return
                if interaction.name not in strings.WORK_COMMANDS: return
                user_command = f'/{interaction.name}'
                user = interaction.user
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'work', current_time)
                if not user_settings.alert_work.enabled: return
                time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'work')
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)



# Initialization
def setup(bot):
    bot.add_cog(WorkCog(bot))