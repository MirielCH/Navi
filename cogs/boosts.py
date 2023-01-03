# party_popper.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import exceptions, functions, regex, settings


class BoostsCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
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
            embed_author = embed_title = icon_url = embed_description = ''
            embed_field0_name = embed_field0_value = embed_field1_name = embed_field1_value = ''
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: embed_title = str(embed.title)
            if embed.description: embed_description = str(embed.description)
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
                if len(embed.fields) > 1:
                    embed_field1_name = embed.fields[1].name
                    embed_field1_value = embed.fields[1].value

            # Boosts cooldowns
            search_strings = [
                'these are your active boosts', #English
                'these are your active boosts', #Spanish, MISSING
                'these are your active boosts', #Portuguese, MISSING
            ]
            search_strings_excluded = [
                'none', #English
                'none', #Spanish, MISSING
                'none', #Portuguese, MISSING
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)
                and all(search_string not in embed_field0_value.lower() for search_string in search_strings_excluded)):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the boosts message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_BOOSTS, user=user,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the boosts message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if 'party popper' in embed_field0_value.lower() and user_settings.alert_party_popper.enabled:
                    timestring_match = re.search(r'popper\*\*: (.+?)(?:$|\n)', embed_field0_value.lower())
                    if not timestring_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Timestring not found for party popper in boosts message.', message)
                        return
                    time_left = await functions.calculate_time_left_from_timestring(message, timestring_match.group(1))
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_party_popper.message
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'party-popper', time_left,
                                                             message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Party popper
            search_strings = [
                'uses the <:partypopper', #English
                'uses the <:partypopper', #Spanish, MISSING
                'uses the <:partypopper', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for party popper message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_PARTY_POPPER,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the party popper message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_party_popper.enabled: return
                time_left = timedelta(hours=1)
                reminder_message = user_settings.alert_party_popper.message
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'party-popper', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(BoostsCog(bot))