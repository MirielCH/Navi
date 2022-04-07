# work.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, errors, reminders, tracking, users
import database
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
            if 'you have already got some resources' in message_title.lower():
                user_id = user_name = user = None
                if message.interaction is not None:
                    user = message.interaction.user
                else:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        try:
                            user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                            user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        except Exception as error:
                            await message.add_reaction(emojis.WARNING)
                            await errors.log_error(f'User not found in work cooldown message: {message.embeds[0].fields}')
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
                    await errors.log_error(f'User not found in work cooldown message: {message.embeds[0].fields}')
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_work.enabled: return
                if message.interaction is not None:
                    user_command = f'/{message.interaction.name}'
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
                        if ('three chainsaw' in message_content.lower()
                        or 'is this a **dream**??' in message_content.lower()
                        or 'this may be the luckiest moment of your life' in message_content.lower()):
                            action = 'chainsaw'
                        elif 'two bow saw' in message_content.lower(): action = 'bowsaw'
                        elif 'axe' in message_content.lower(): action = 'axe'
                        elif 'log' in message_content.lower(): action = 'chop'
                        elif 'three nets' in message_content.lower(): action = 'bigboat'
                        elif 'a **net**' in message_content.lower(): action = 'net'
                        elif 'fish' in message_content.lower(): action = 'fish'
                        elif 'two tractors' in message_content.lower(): action = 'greenhouse'
                        elif 'tractor' in message_content.lower(): action = 'tractor'
                        elif 'both hands' in message_content.lower(): action = 'ladder'
                        elif 'apple' in message_content.lower() or 'banana' in message_content.lower(): action = 'pickup'
                        elif 'four drills' in message_content.lower(): action = 'dynamite'
                        elif 'two drills' in message_content.lower(): action = 'drill'
                        elif 'pickaxe' in message_content.lower(): action = 'pickaxe'
                        elif 'coins' in message_content.lower() or 'ruby' in message_content.lower(): action = 'mine'
                        else: action = '[work command]'
                        user_command = f'rpg {action}'
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.parse_timestring_to_timedelta(timestring.lower())
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                time_left = time_left - time_elapsed
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.add_reaction(emojis.CROSS)

        if not message.embeds:
            message_content = message.content
            # Work
            excluded_strings = ('hunting together','** found','** plants','** throws', 'new quest')
            if ('** got ' in message_content.lower()
                and not any(string in message_content.lower() for string in excluded_strings)):
                user_name = user = None
                if message.interaction is not None:
                    user = message.interaction.user
                else:
                    search_strings = [
                        '[!1] \*\*(.+?)\*\* got',
                        '[!1] (.+?)\*\* got',
                        '\?\?\?\?\? \*\*(.+?)\*\* got',
                        '\*\*(.+?)\*\* got'
                    ]
                    for search_string in search_strings:
                        user_name_search = re.search(search_string, message_content, re.IGNORECASE)
                        if user_name_search is not None: break
                    if user_name_search is None:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error(f'User not found in work message: {message.content}')
                        return
                    user_name = user_name_search.group(1)
                    user_name = user_name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                    for member in message.guild.members:
                        member_name = member.name.encode('unicode-escape',errors='ignore').decode('ASCII').replace('\\','')
                        if member_name == user_name:
                            user = member
                            break
                if user is None:
                    await message.add_reaction(emojis.WARNING)
                    await errors.log_error(f'User not found for user name {user_name}')
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
                if message.interaction is not None:
                    user_command = f'/{message.interaction.name}'
                else:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ')
                                and any(command in msg.content.lower() for command in strings.WORK_COMMANDS)
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        await message.add_reaction(emojis.WARNING)
                        await errors.log_error('Couldn\'t find a command for the work message.')
                        return
                    user_command = user_command_message.content.lower()
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('work')
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
                reminder_message = user_settings.alert_work.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'work', time_left,
                                                         message.channel.id, reminder_message)
                )
                if reminder.record_exists:
                    await message.add_reaction(emojis.NAVI)
                else:
                    if settings.DEBUG_MODE: await message.channel.send(strings.MSG_ERROR)
                if 'quite a large leaf' in message_content.lower():
                    await message.add_reaction(emojis.WOAH_THERE)
                elif 'mined with too much force' in message_content.lower():
                    await message.add_reaction(emojis.SWEATY)
                elif 'for some reason, one of the fish was carrying' in message_content.lower():
                    await message.add_reaction(emojis.FISHPOGGERS)
                elif 'one of them had' in message_content.lower() and 'rubies in it' in message_content.lower():
                    await message.add_reaction(emojis.WOW)
                elif 'wooaaaa!!' in message_content.lower():
                    await message.add_reaction(emojis.FIRE)
                elif 'wwwooooooaaa!!!1' in message_content.lower():
                    await message.add_reaction(emojis.FIRE)
                elif 'is this a **dream**??' in message_content.lower():
                    await message.add_reaction(emojis.FIRE)
                elif 'nice!' in message_content.lower() and 'watermelon' in message_content.lower():
                    await message.add_reaction(emojis.PANDA_MELON)
                elif 'this may be the luckiest moment of your life' in message_content.lower():
                    await message.add_reaction(emojis.PANDA_COOL)
                elif 'ooofff!!' in message_content.lower():
                    await message.add_reaction(emojis.PANDA_FISH)


# Initialization
def setup(bot):
    bot.add_cog(WorkCog(bot))