# ruby_counter.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, functions, settings, strings, views


class RubyCounterCog(commands.Cog):
    """Cog that contains all commands related to the ruby counter"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_description = message_field = message_author = ''
            if embed.description: message_description = str(embed.description)
            if embed.fields: message_field = str(embed.fields[0].value)
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Rubies from trades E and F
            search_strings = [
                'our trade is done then', #English
                'nuestro intercambio está hecho entonces', #Spanish
                'nossa troca é feita então', #Portuguese
            ]
            if (any(search_string in message_description.lower() for search_string in search_strings)
                and '<:ruby' in message_field.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r"\*\*(.+?)\*\*:", message_field)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        if user_name in strings.EPIC_NPC_NAMES: user_name = user_name_match.group(2)
                        user_name = await functions.encode_text(user_name)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in trade message for ruby counter.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in trade message for ruby counter.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                for name in strings.EPIC_NPC_NAMES:
                    epic_npc_pos = message_field.find(name)
                    if epic_npc_pos != -1: break
                ruby_pos = message_field.find('<:ruby')
                trade_type = 'F' if ruby_pos > epic_npc_pos else 'E'
                search_pattern = r"603304907650629653> x(.+?) \n"  if trade_type == 'E' else r"603304907650629653> x(.+?)$"
                ruby_count_match = re.search(search_pattern, message_field)
                if ruby_count_match:
                    ruby_count = int(ruby_count_match.group(1).replace(',',''))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Ruby count not found in trade message for ruby counter.', message)
                    return
                if trade_type == 'E': ruby_count *= -1
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from lootboxes
            search_strings = [
                "— lootbox", #All languages
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings)
                and '<:ruby' in message_field.lower()):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = await functions.encode_text(user_name_match.group(1))
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in lootbox message for ruby counter.', message)
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in lootbox message for ruby counter.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_pos = message_field.find('<:ruby')
                number_start_pos = message_field.rfind('+', 0, ruby_pos)
                ruby_count_match = re.search(r'\+(.+?) <:ruby', message_field[number_start_pos:])
                if ruby_count_match:
                    ruby_count = int(ruby_count_match.group(1).replace(',',''))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Ruby count not found in lootbox message for ruby counter.', message)
                    return
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from inventory
            search_strings = [
                "— inventory", #All languages
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                if icon_url == embed.Empty: return
                user_id = user_name = embed_user = None
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+(?:i\b|inv\b|inventory\b)"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find an interaction user for the inventory message.', message)
                        return
                    interaction_user = user_command_message.author
                user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                else:
                    user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in inventory message for ruby counter.', message)
                        return
                if user_id is not None:
                    embed_user = await message.guild.fetch_member(user_id)
                else:
                    embed_user = await functions.get_guild_member_by_name(message.guild, user_name)
                if embed_user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in inventory message for ruby counter.', message)
                    return
                if embed_user != interaction_user: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                if  '<:ruby' not in message_field.lower():
                    ruby_count = 0
                else:
                    ruby_count_match = re.search(r"ruby\*\*: ([0-9,]+)", message_field)
                    if ruby_count_match:
                        ruby_count = int(ruby_count_match.group(1).replace(',',''))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Ruby count not found in inventory message for ruby counter.', message)
                        return
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

        if not message.embeds:
            message_content = message.content
            # Ruby training helper
            search_strings = [
                '** is training in the mine!', #English
                '** está entrenando en la mina!', #Spanish
                '** está treinando na mina!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True
                if user is None:
                    slash_command = False
                    user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in ruby training message for ruby counter.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in ruby training message for ruby counter.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                search_patterns = [
                    r'more than (.+?) <:ruby', #English
                    r'más de (.+?) <:ruby', #Spanish
                    r'mais de (.+?) <:ruby', #Portuguese
                ]
                ruby_count_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if ruby_count_match:
                    ruby_count = int(ruby_count_match.group(1).replace(',',''))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Ruby count not found in ruby training message for ruby counter.', message)
                    return
                answer = f'You have {user_settings.rubies:,} {emojis.RUBY}'
                if slash_command:
                    buttons = {}
                    correct_button = 'training_yes' if user_settings.rubies > ruby_count else 'training_no'
                    for row, action_row in enumerate(message.components, start=1):
                        buttons[row] = {}
                        for button in action_row.children:
                            if button.custom_id == correct_button:
                                buttons[row][button.custom_id] = (button.label, button.emoji, True)
                            else:
                                buttons[row][button.custom_id] = (button.label, button.emoji, False)
                    view = views.TrainingAnswerView(buttons)
                else:
                    answer = f'`YES` ({answer})' if user_settings.rubies > ruby_count else f'`NO` ({answer})'
                    view = None
                if not user_settings.dnd_mode_enabled:
                    answer = f'{answer} {user.mention}' if user_settings.ping_after_message else f'{user.mention} {answer}'
                await message.reply(content=answer, view=view)

            # Rubies from selling
            search_strings = [
                '`ruby` successfully sold', #English
                '`ruby` vendido(s)', #Spanish, Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+sell\s+ruby.*$"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the ruby sell message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_count_match = re.search(r'^(.+?) <:ruby', message_content, re.IGNORECASE)
                if ruby_count_match:
                    ruby_count = int(ruby_count_match.group(1).replace(',',''))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Ruby count not found in sell message for ruby counter.', message)
                    return
                ruby_count = user_settings.rubies - ruby_count
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from work commands
            search_strings = [
                '** got ', #English
                '** consiguió ', #Spanish
                '** conseguiu ', #Portuguese 1
                '** recebeu ', #Portuguese 2
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and '<:ruby' in message_content.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r'\*\*(.+?)\*\* got', #English
                        r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u)', #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content) #case
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in work message for ruby counter.', message)
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in work message for ruby counter.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                search_patterns = [
                    r'\*\* got (.+?) <:ruby', #English mine commands
                    r' had (.+?) <:ruby', #English proc pickup commands
                    r'\*\* cons(?:e|i)gui(?:ó|u) (.+?) <:ruby', #Spanish, Portuguese mine commands
                    r'llevaba dentro (.+?) <:ruby', #Spanish proc pickup commands
                    r'deles tinha (.+?) <:ruby', #Portuguese proc pickup commands
                ]
                ruby_count_match = await functions.get_match_from_patterns(search_patterns, message_content.lower())
                if ruby_count_match:
                    ruby_count = int(ruby_count_match.group(1).replace(',',''))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Ruby count not found in work message for ruby counter.', message)
                    return
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)

            # Rubies from crafting ruby sword
            search_strings = [
                '`ruby sword` successfully crafted', #English
                '`ruby sword` crafteado(s)', #Spanish
                '`ruby sword` craftado(s)', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+craft\s+ruby\s+sword\s*$"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the ruby sword crafting message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_count = user_settings.rubies - 4
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from crafting ruby armor
            search_strings = [
                '`ruby armor` successfully crafted', #English
                '`ruby armor` crafteado(s)', #Spanish
                '`ruby armor` craftado(s)', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+craft\s+ruby\s+armor\s*$"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the ruby armor crafting message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_count = user_settings.rubies - 7
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from crafting coin sword
            search_strings = [
                '`coin sword` successfully crafted', #English
                '`coin sword` crafteado(s)', #Spanish
                '`coin sword` craftado(s)', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+craft\s+coin\s+sword\s*$"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the coin sword crafting message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_count = user_settings.rubies - 4
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from crafting ultra-edgy armor
            search_strings = [
                '`ultra-edgy armor` successfully forged', #English
                '`ultra-edgy armor` exitosamente forjado', #Spanish
                '`ultra-edgy armor` forjado com sucesso', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+forge\s+ultra-edgy\s+armor\s*$"
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the ultra-edgy armor crafting message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                ruby_count = user_settings.rubies - 400
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(RubyCounterCog(bot))