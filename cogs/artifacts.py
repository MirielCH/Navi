# artifacts.py

import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from resources import emojis, exceptions, functions, regex, settings


class ArtifactsCog(commands.Cog):
    """Cog that contains the artifacts detection commands"""
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
            if embed.author:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: embed_title = str(embed.title)
            if embed.description: embed_description = str(embed.description)
            embed_field0 = ''
            if embed.fields:
                embed_field0 = embed.fields[0].value

            # Artifacts overview
            search_strings = [
                'you can find parts of the artifacts across', #English
                'puedes encontrar partes de los artefactos en muchos', #Spanish
                'você pode encontrar partes dos artefatos em muitos', #Portuguese
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the artifacts message.', message)
                            return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ARTIFACTS, user=user,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the artifacts message.', message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                top_hat_active_match = re.search(r'✅ \| <:tophat', embed_field0.lower())
                top_hat_unlocked = True if top_hat_active_match else False
                await user_settings.update(top_hat_unlocked=top_hat_unlocked)
                pocket_watch_active_match = re.search(r'✅ \| <:pocketwatch', embed_field0.lower())
                if not pocket_watch_active_match: return
                search_patterns = [
                    r'adds a cooldown reduction of ([0-9\.]+)%, ability', #English
                    r'adds a cooldown reduction of ([0-9\.]+)%, ability', #Spanish, MISSING
                    r'adds a cooldown reduction of ([0-9\.]+)%, ability', #Portuguese, MISSING
                ]
                pocket_watch_cooldown_match = await functions.get_match_from_patterns(search_patterns, embed_field0)
                pocket_watch_cooldown = float(pocket_watch_cooldown_match.group(1))
                await user_settings.update(user_pocket_watch_multiplier=(100 - pocket_watch_cooldown) / 100)
                if user_settings.partner_id is not None:
                    try:
                        partner_settings: users.User = await users.get_user(user_settings.partner_id)
                        await partner_settings.update(partner_pocket_watch_multiplier=(100 - pocket_watch_cooldown) / 100)
                    except exceptions.FirstTimeUserError:
                        pass
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(ArtifactsCog(bot))