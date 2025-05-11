# ascension.py

import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, users
from resources import emojis, exceptions, functions, regex, settings


class AscensionCog(commands.Cog):
    """Cog that contains all commands related to the ruby counter"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_author = embed_footer = embed_field_names = embed_field_values = ''
            if embed.description is not None: embed_description = str(embed.description)
            if embed.fields:
                for field in embed.fields:
                    embed_field_names = f'{embed_field_names}\n{str(field.name)}'
                    embed_field_values = f'{embed_field_values}\n{str(field.value)}'
            if embed.footer is not None: embed_footer = embed.footer.text
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Set ascension from profession overview
            search_strings = [
                "— professions", #All languages
            ]
            search_strings_footer = [
                'level 100', #Not ascended, English
                'nivel 100', #Not ascended, Spanish
                'nível 100', #Not ascended, Portuguese
                'unlocked!', #Ascended, English
                'desbloqueada!', #Ascended, Spanish, Portuguese
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and any(search_string in embed_footer.lower() for search_string in search_strings_footer)):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_MENU,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                ascended = False if '100' in embed_footer.lower() else True
                if user_settings.ascended != ascended:
                    await user_settings.update(ascended=ascended)
                    if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            search_strings = [
                "unlocked the ascended skill", #English
            ]
            if any(search_string in embed_field_names.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\*', embed_field_names)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_PROFESSIONS_ASCEND,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in ascension message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                await user_settings.update(ascended=True)
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            search_strings = [
                "— ready", #All languages, ready
                "— cooldowns", #All languages, cooldowns
            ]
            search_strings_field = [
                ":lock:", #All languages
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and any(search_string in embed_field_names.lower() for search_string in search_strings_field)):
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_MENU)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        return
                    interaction_user = user_command_message.author
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        return
                if interaction_user not in embed_users: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if user_settings.ascended: await user_settings.update(ascended=False)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(AscensionCog(bot))