# patreon.py

import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, users
from resources import emojis, exceptions, functions, regex, settings, strings


class PatreonCog(commands.Cog):
    """Cog that contains the patreon detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before: dict[str, str] = await functions.parse_embed(message_before)
        embed_data_after: dict[str, str] = await functions.parse_embed(message_after)
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
            embed_description = str(embed.description) if embed.description else ''

            # Patreon
            search_strings: list[str] = [
               "if you want to support", #English
               "si quieres apoyar", #Spanish
               "se você quiser apoiar", #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                user_command_message: discord.Message | None = None
                user: discord.User | discord.Member = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_PATREON)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User command not found for patreon message.', message)
                        return
                    user: discord.User | discord.Member = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if not embed.fields:
                    donor_tier: int = 0
                else:
                    donor_tiers: list[str] = [tier.lower() for tier in strings.DONOR_TIERS]
                    donor_tier_match: re.Match[str] = re.search(r'\| (.+?)$', embed.fields[0].name.lower())
                    donor_tier: int = donor_tiers.index(donor_tier_match.group(1))
                if user_settings.user_donor_tier != donor_tier:
                    await user_settings.update(user_donor_tier=donor_tier)
                if user_settings.partner_id is not None:
                    partner_settings: users.User = await users.get_user(user_settings.partner_id)
                    if partner_settings.partner_donor_tier != donor_tier:
                        await partner_settings.update(partner_donor_tier=donor_tier)
                if user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(PatreonCog(bot))