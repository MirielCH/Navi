# events.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class EventsCog(commands.Cog):
    """Cog that contains the Event detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if not message.embeds: return
        embed: discord.Embed = message.embeds[0]
        message_field_name = message_field_value = ''
        if len(embed.fields) > 1:
            message_field_name = embed.fields[1].name
            message_field_value = embed.fields[1].value

        if not message_field_name.lower() == 'normal events': return

        user = None
        message_history = await message.channel.history(limit=50).flatten()
        user_command_message = None
        for msg in message_history:
            if msg.content is not None:
                if msg.content.lower().startswith('rpg event') and not msg.author.bot:
                    user_command_message = msg
                    break
        if user_command_message is None:
            await message.add_reaction(emojis.WARNING)
            await errors.log_error('Couldn\'t find a command for the events message.')
            return
        user = user_command_message.author
        try:
            user_settings: users.User = await users.get_user(user.id)
        except exceptions.FirstTimeUserError:
            return
        if not user_settings.bot_enabled: return
        cooldowns = []
        if user_settings.alert_big_arena.enabled:
            try:
                big_arena_search = re.search("Big arena\*\*: (.+?)\\n", message_field_value)
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(error)
                return
            if big_arena_search is not None:
                big_arena_timestring = big_arena_search.group(1)
                big_arena_message = user_settings.alert_big_arena.message.format(event='big arena')
                cooldowns.append(['big-arena', big_arena_timestring.lower(), big_arena_message])
        if user_settings.alert_lottery.enabled:
            try:
                lottery_search = re.search("Lottery\*\*: (.+?)\\n", message_field_value)
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(error)
                return
            if lottery_search is not None:
                lottery_timestring = lottery_search.group(1)
                lottery_message = user_settings.alert_lottery.message.replace('%','rpg buy lottery ticket')
                cooldowns.append(['lottery', lottery_timestring.lower(), lottery_message])
        if user_settings.alert_pet_tournament.enabled:
            try:
                pet_search = re.search("tournament\*\*: (.+?)\\n", message_field_value)
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(error)
                return
            if pet_search is not None:
                pet_timestring = pet_search.group(1)
                pet_message = user_settings.alert_pet_tournament.message.format(event='pet tournament')
                cooldowns.append(['pet-tournament', pet_timestring.lower(), pet_message])
        if user_settings.alert_horse_race.enabled:
            try:
                horse_search = re.search("race\*\*: (.+?)\\n", message_field_value)
            except Exception as error:
                await message.add_reaction(emojis.WARNING)
                await errors.log_error(error)
                return
            if horse_search is not None:
                horse_timestring = horse_search.group(1)
                horse_message = user_settings.alert_horse_race.message.format(event='horse race')
                cooldowns.append(['horse-race', horse_timestring.lower(), horse_message])
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
            bot_answer_time = message.created_at.replace(microsecond=0)
            time_elapsed = current_time - bot_answer_time
            time_left = time_left - time_elapsed
            if time_left.total_seconds() > 0:
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, cd_activity, time_left,
                                                         message.channel.id, cd_message, overwrite_message=False)
                )
                if not reminder.record_exists:
                    await message.channel.send(strings.MSG_ERROR)
                    return
        if updated_reminder: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(EventsCog(bot))