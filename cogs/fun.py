# fun.py
"""Contains some nonsense"""

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, functions, settings


class FunCog(commands.Cog):
    """Cog with events and help and about commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=('listen',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True, read_message_history=True)
    async def hey(self, ctx: commands.Context) -> None:
        """Hey! Listen!"""
        if ctx.prefix.lower() == 'rpg ':
            return
        await ctx.reply('https://tenor.com/view/navi-hey-listen-gif-4837431')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""

        if not message.embeds and not message.author.bot:
            message_content = message.content
            if message_content.lower() == 'navi lit':
                await message.reply('https://tenor.com/view/betty-white-dab-mood-gif-5044603')

        if not message.embeds and message.author.id == settings.EPIC_RPG_ID:
            message_content = message.content
            laugh_terms = [
                'You just lost your lootbox',
            ]
            if 'died fighting the **mysterious man**' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("^\*\*(.+?)\*\*", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in heal event message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the heal event reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            if 'is now in the jail' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("car \*\*(.+?)\\n", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in epic guard message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the jail reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEEPO_JAIL)

            if 'again, it **exploded**' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("\*\*(.+?)\*\* tries to", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in enchant message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the failed enchant reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            if 'took the seed from the ground and decided to try planting it again later' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("\*\*(.+?)\*\* HITS", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in farm event message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the failed farm event reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            if 'fighting them wasn\'t very clever' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("\*\*(.+?)\*\* fights", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in hunt event message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the failed hunt event reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            if 'you just lost your lootbox' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("\*\*(.+?)\*\* uses a", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in lootbox event message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the failed lootbox event reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.PEPE_LAUGH)

            if 'christmas slime' in message_content.lower() and 'got 100' in message_content.lower():
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name = None
                    try:
                        user_name = re.search("^\*\*(.+?)\*\*", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in christmas slime message for the fun reaction: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a user for the christmas slime reaction.',
                            message
                        )
                        return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                await message.add_reaction(emojis.XMAS_YAY)

        if message.embeds and message.author.id == settings.EPIC_RPG_ID:
            embed: discord.Embed = message.embeds[0]

            if embed.fields:
                field = embed.fields[0]

                # Lost pet reaction
                if '** got bored and left' in field.value.lower():
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        message_history = await message.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if msg.content is not None:
                                if msg.content.lower().replace(' ','').startswith('rpgtr') and not msg.author.bot:
                                    user = msg.author
                                    break
                        if user is None:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                'Couldn\'t find a user for the lost pet reaction.',
                                message
                            )
                            return
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                    await message.add_reaction(emojis.PANDA_SAD)

                # Shitty lootbox reaction
                shitty_lootbox_found = False
                if 'lootbox opened' in field.name.lower():
                    if '+1' in field.value.lower() and field.value.lower().count('<:') == 1:
                        if 'wooden log' in field.value.lower() or 'normie fish' in field.value.lower():
                            shitty_lootbox_found = True
                    elif 'nothing' in field.value.lower():
                        shitty_lootbox_found = True
                if shitty_lootbox_found:
                    user = await functions.get_interaction_user(message)
                    if user is None:
                        message_history = await message.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if msg.content is not None:
                                if msg.content.lower().replace(' ','').startswith('rpgopen') and not msg.author.bot:
                                    user = msg.author
                                    break
                        if user is None:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                'Couldn\'t find a user for the shitty lootbox reaction.',
                                message
                            )
                            return
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.reactions_enabled: return
                    await message.add_reaction(emojis.PEPE_LAUGH)


# Initialization
def setup(bot):
    bot.add_cog(FunCog(bot))