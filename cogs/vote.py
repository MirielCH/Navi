# vote.py

import re

import discord
from discord.ext import commands

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings


class VoteCog(commands.Cog):
    """Cog that contains the dungeon/miniboss detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            if message.embeds[0].fields:
                field = message.embeds[0].fields[0]

                # Vote cooldown
                if field.name.lower() == 'next vote rewards':
                    timestring_search = re.search("Cooldown: \*\*(.+?)\*\*", field.value)
                    if timestring_search is None: return
                    timestring = timestring_search.group(1)
                    user = await functions.get_interaction_user(message)
                    user_command = 'rpg vote' if user is None else '/vote'
                    if user is None:
                        message_history = await message.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if msg.content is not None:
                                if msg.content.lower().replace(' ','').startswith('rpgvote') and not msg.author.bot:
                                    user = msg.author
                                    break
                        if user is None:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                'Couldn\'t find a user for the vote embed.',
                                message
                            )
                            return
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.alert_vote.enabled: return
                    time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                    reminder_message = user_settings.alert_vote.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'vote', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(VoteCog(bot))