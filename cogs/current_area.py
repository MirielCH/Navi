# current_area.py

import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from resources import exceptions, functions, regex, settings, strings


class CurrentAreaCog(commands.Cog):
    """Cog that contains all commands related to the ruby counter"""
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
            embed_description = embed_field = embed_author = ''
            if embed.description: embed_description = str(embed.description)
            if embed.fields: embed_field = str(embed.fields[0].value)
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Set current area from time traveling
            search_strings = [
                'has traveled in time', #English
                'viajou no tempo', #Spanish
                'tempo de viagem', #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r'\*\*(.+?)\*\* has', #English
                        r'\*\*(.+?)\*\* viajó', #English
                        r'\*\*(.+?)\*\* tempo', #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await errors.log_error('User name not found in current area time travel message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                await user_settings.update(current_area=1)

            # Set current area from profile
            search_strings = [
                "— profile", #All languages
                "— progress", #All languages
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and not 'epic npc' in embed_author.lower()):
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_PROGRESS)
                    )
                    if user_command_message is None: return
                    interaction_user = user_command_message.author
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        return
                if interaction_user not in embed_users: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                area_match = re.search(r'rea\*\*: (.+?) \(', embed_field.lower())
                if not area_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Area not found in current area profile or progress message.', message)
                    return
                current_area = area_match.group(1)
                if current_area == 'top':
                    current_area = 21
                else:
                    current_area = int(current_area)
                if user_settings.current_area != current_area:
                    await user_settings.update(current_area=current_area)

        if not message.embeds:
            message_content = message.content
            # Set current area from hunt and adventure mobs
            search_strings = [
                'found a', #English
                'found the', #English TOP
                'encontr', #Spanish, Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
                and (
                    all(monster.lower() not in message_content.lower() for monster in strings.MONSTERS_HUNT_MISC)
                    and all(monster.lower() not in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_MISC)
                )
            ):
                user = await functions.get_interaction_user(message)
                together = False
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
                if together:
                    search_patterns = [
                        r"\*\*(.+?)\*\* and \*\*", #English
                        r"\*\*(.+?)\*\* y \*\*", #Spanish
                        r"\*\*(.+?)\*\* e \*\*", #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User name not found in current area hunt together message.', message)
                        return
                    user_name = user_name_match.group(1)
                else:
                    search_patterns_user_name = [
                        r"\*\*(.+?)\*\* found a", #English
                        r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns_user_name, message_content)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user name in current area hunt/adventure message.', message)
                        return
                    user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT_ADVENTURE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user in current area hunt/adventure message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                search_patterns_mob_name = [
                    r"found and killed (.+?) \*\*(.+?)\*\*(?: \(but| \(way|\n)", #English
                    r"found (the) \*\*(.+?)\*\*(?:, | \(but| \(way|\n)", #English
                    r"found an? (.+?) \*\*(.+?)\*\*", #English
                    r"encontró un (.+?) \*\*(.+?)\*\*(?:, | \(pero| \(mucho|\n)", #Spanish
                    r"encontró y mató (.+?) \*\*(.+?)\*\*(?:, | \(pero| \(mucho|\n)", #Spanish
                    r"encontrou e matou (.+?) \*\*(.+?)\*\*(?:, | \(só| \(muito|\n)", #Portuguese
                ]
                mob_name_match = await functions.get_match_from_patterns(search_patterns_mob_name, message_content)
                if not mob_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find mob name in current area hunt/adventure message.', message)
                    return
                mob_name = mob_name_match.group(2)
                current_area = await functions.get_area(f'**{mob_name}**')
                if user_settings.current_area != current_area:
                    await user_settings.update(current_area=current_area)

            # Set current area from move command
            search_strings = [
                'has moved to the area #', #English, area change
                'starts to fly and travels to the next area!', #English, candy cane
                'se movio al área #', #Spanish, area change
                'se movio al área #', #Spanish, candy cane, MISSING
                'foi movido para a área #', #Portuguese, area change
                'foi movido para a área #', #Portuguese, candy cane, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for the current area change / candy cane message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_AREA_MOVE_CANDY_CANE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the current area change / candy cane message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                area_match = re.search(r' #(\d+?)(?:$|\s)', message_content)
                if not area_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find the current area in area change / candy cane message.',
                                           message)
                    return
                await user_settings.update(current_area=int(area_match.group(1)))

            # Set current area from hunt event
            if ':zombie' in message_content.lower() and '#2' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = user_command_message = None
                    together = False
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HUNT, user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in current area hunt event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if user_settings.current_area != 2: await user_settings.update(current_area=2)

            # Clear current area from ruby dragon event and warn user
            dragon_names = [
                'the ruby dragon', #English
                'el dragón ruby', #Spanish
                'o dragão ruby', #Portuguese
            ]
            if ':mag:' in message_content.lower() and any(name in message_content.lower() for name in dragon_names):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = user_command_message = None
                    together = False
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HUNT, user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in current area work event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                await user_settings.update(current_area=None)


# Initialization
def setup(bot):
    bot.add_cog(CurrentAreaCog(bot))