# halloween.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import exceptions, functions, regex, settings


class HalloweenCog(commands.Cog):
    """Cog that contains the halloween detection"""
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
        if message.author.id not in [settings.EPIC_RPG_ID, settings.OWNER_ID]: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_title = embed_field0_name = embed_field0_value = embed_autor = icon_url = ''
            if embed.description: embed_description = embed.description
            if embed.title: embed_title = embed.title
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
            if embed.author:
                embed_autor = embed.author.name
                icon_url = embed.author.icon_url

            # Scroll boss helper
            search_strings = [
                "**pumpkin bat** is attacking you", #English
            ]
            if any(search_string in embed_field0_value.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\* HITS', embed_field0_value)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await functions.get_message_from_channel_history(
                                message.channel, regex.COMMAND_HAL_CRAFT_SPOOKY_SCROLL,
                                user_name=user_name
                            )
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        user = None # Helper will still work if no user is found.
                    else:
                        user = user_command_message.author
                if user is not None:
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.halloween_helper_enabled: return
                search_patterns = [
                    r'(?:attacking you) (?:from )?(?:the )?(\w.+)!', #English
                ]
                attack_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not attack_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('No attack found in scroll boss helper', message)
                    return
                attack = attack_match.group(1)
                attacks_answers = {
                    'left': 'pumpkin',
                    'right': 'attack',
                    'ahead': 'bazooka',
                    'behind': 'dodge',
                }
                await message.reply(f'`{attacks_answers[attack].upper()}`')

# Initialization
def setup(bot):
    bot.add_cog(HalloweenCog(bot))