# nsmb-bigarena.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class NotSoMiniBossBigArenaCog(commands.Cog):
    """Cog that contains the not so mini boss and big arena detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds: return
        message_content = message.content
        search_strings = [
            'successfully registered for the next **big arena** event!', #English 1
            'successfully registered for the next **minin\'tboss** event!', #English 2
            'you are already registered!', #English 3
            'en registro', #Spanish, thanks lume
        ]
        if any(search_string in message_content.lower() for search_string in search_strings):
            user_name = None
            user = await functions.get_interaction_user(message)
            slash_command = True if user is not None else False
            if user is None:
                if message.mentions:
                    user = message.mentions[0]
                else:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\*,", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in big-arena or minin\'tboss message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
            if user is None:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'User not found in big-arena or minin\'tboss message: {message_content}',
                    message

                )
                return
            try:
                user_settings: users.User = await users.get_user(user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled: return
            if slash_command:
                interaction = await functions.get_interaction(message)
                if interaction.name == 'big':
                    user_command = '/big arena'
                elif interaction.name == 'minintboss':
                    user_command = '/minintboss'
                else:
                    return
                user_command = f'{user_command} join: true'
            else:
                message_history = await message.channel.history(limit=50).flatten()
                user_command_message = None
                for msg in message_history:
                    if msg.content is not None:
                        msg_content = msg.content.lower().replace(' ','')
                        if ((msg_content.startswith('rpg')
                            and 'bigarenajoin' in msg_content or 'minintbossjoin' in msg_content)
                            and msg.author == user):
                            user_command_message = msg
                            break
                if user_command_message is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        'Couldn\'t find a command for the big-arena or minin\'tboss message.',
                        message
                    )
                    return
                user_command = user_command_message.content.lower()
            today = datetime.utcnow().replace(hour=18, minute=0, second=0, microsecond=0)
            current_time = datetime.utcnow().replace(microsecond=0)
            if 'minint' in user_command:
                if not user_settings.alert_not_so_mini_boss.enabled: return
                next_tuesday = today + timedelta((1-today.weekday()) % 7)
                next_thursday = today + timedelta((3-today.weekday()) % 7)
                next_saturday = today + timedelta((5-today.weekday()) % 7)
                time_left_tuesday = next_tuesday - current_time
                time_left_thursday = next_thursday - current_time
                time_left_saturday = next_saturday - current_time
                time_left = min(time_left_tuesday, time_left_thursday, time_left_saturday)
                event = 'minin\'tboss'
                reminder_message = user_settings.alert_not_so_mini_boss.message.replace('{event}', event.replace('-',' '))
            else:
                if not user_settings.alert_big_arena.enabled: return
                next_monday = today + timedelta((0-today.weekday()) % 7)
                next_wednesday = today + timedelta((2-today.weekday()) % 7)
                next_friday = today + timedelta((4-today.weekday()) % 7)
                time_left_monday = next_monday - current_time
                time_left_wednesday = next_wednesday - current_time
                time_left_friday = next_friday - current_time
                time_left = min(time_left_monday, time_left_wednesday, time_left_friday)
                event = 'big-arena'
                reminder_message = user_settings.alert_big_arena.message.replace('{event}', event.replace('-',' '))
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(user.id, event, time_left,
                                                     message.channel.id, reminder_message)
            )
            await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(NotSoMiniBossBigArenaCog(bot))