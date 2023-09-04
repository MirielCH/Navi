# events.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


class EventsCog(commands.Cog):
    """Cog that contains the Event detection commands"""
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
            message_field1_name = message_field1_value = ''
            if len(embed.fields) > 1:
                message_field1_name = embed.fields[1].name
                message_field1_value = embed.fields[1].value

            search_strings = [
                'normal events', #English
                'eventos normales', #Spanish
                'eventos normais', #Portuguese
            ]
            if any(search_string in message_field1_name.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_EVENTS)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the events message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                cooldowns = []
                if user_settings.alert_big_arena.enabled:
                    big_arena_match = re.search(r"big arena\*\*: (.+?)\n", message_field1_value.lower())
                    if big_arena_match:
                        big_arena_timestring = big_arena_match.group(1)
                        big_arena_message = user_settings.alert_big_arena.message.replace('{event}', 'big arena')
                        cooldowns.append(['big-arena', big_arena_timestring.lower(), big_arena_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Big arena cooldown not found in event message.', message)
                        return
                if user_settings.alert_lottery.enabled:
                    lottery_match = re.search(r"lottery\*\*: (.+?)\n", message_field1_value.lower())
                    if lottery_match:
                        lottery_timestring = lottery_match.group(1)
                        user_command = await functions.get_slash_command(user_settings, 'lottery')
                        user_command = f"{user_command} `amount: [1-200]`"
                        lottery_message = user_settings.alert_lottery.message.replace('{command}', user_command)
                        cooldowns.append(['lottery', lottery_timestring.lower(), lottery_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Lottery cooldown not found in event message.', message)
                        return
                if user_settings.alert_pet_tournament.enabled:
                    pet_match = re.search(r"tournament\*\*: (.+?)\n", message_field1_value.lower())
                    if pet_match:
                        pet_timestring = pet_match.group(1)
                        pet_message = user_settings.alert_pet_tournament.message.replace('{event}', 'pet tournament')
                        cooldowns.append(['pet-tournament', pet_timestring.lower(), pet_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Pet tournament cooldown not found in event message.', message)
                        return
                if user_settings.alert_horse_race.enabled:
                    horse_match = re.search(r"race\*\*: (.+?)\n", message_field1_value.lower())
                    if horse_match:
                        horse_timestring = horse_match.group(1)
                        horse_message = user_settings.alert_horse_race.message.replace('{event}', 'horse race')
                        cooldowns.append(['horse-race', horse_timestring.lower(), horse_message])
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Horse race cooldown not found in event message.', message)
                        return
                current_time = datetime.utcnow().replace(microsecond=0)
                updated_reminder = False
                for cooldown in cooldowns:
                    cd_activity = cooldown[0]
                    cd_timestring = cooldown[1]
                    cd_message = cooldown[2]
                    try:
                        reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, cd_activity)
                    except exceptions.NoDataFoundError:
                        continue
                    updated_reminder = True
                    time_left = await functions.parse_timestring_to_timedelta(cd_timestring)
                    if cd_activity == 'pet-tournament': time_left += timedelta(minutes=1)
                    bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                    time_elapsed = current_time - bot_answer_time
                    time_left = time_left - time_elapsed
                    if time_left < timedelta(0): continue
                    if time_left.total_seconds() > 0:
                        reminder: reminders.Reminder = (
                            await reminders.insert_user_reminder(user.id, cd_activity, time_left,
                                                                message.channel.id, cd_message, overwrite_message=False)
                        )
                        if not reminder.record_exists:
                            await message.channel.send(strings.MSG_ERROR)
                            return
                if updated_reminder and user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(EventsCog(bot))