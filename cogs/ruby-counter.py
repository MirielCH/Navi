# ruby_counter.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, functions, settings, strings


class RubyCounterCog(commands.Cog):
    """Cog that contains all commands related to the ruby counter"""
    def __init__(self, bot):
        self.bot = bot

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
            ]
            if (any(search_string in message_description.lower() for search_string in search_strings)
                and '<:ruby' in message_field.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        search_string = "\*\*(.+?)\*\*"
                        user_name = re.search(search_string, message_field).group(1)
                        if user_name in strings.EPIC_NPC_NAMES: user_name = re.search(search_string, message_field).group(2)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in trade message for ruby counter: {message.embeds[0].fields}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in trade message for ruby counter: {message.embeds[0].fields}',
                        message
                    )
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
                search_string = "603304907650629653> x(.+?) \\n"  if trade_type == 'E' else "603304907650629653> x(.+?)$"
                try:
                    ruby_count = re.search(search_string, message_field).group(1)
                    ruby_count = int(ruby_count.replace(',',''))
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Ruby count not found in trade message for ruby counter: {message.embeds[0].fields}',
                        message
                    )
                    return
                if trade_type == 'E': ruby_count *= -1
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from lootboxes
            search_strings = [
                "'s lootbox", #English
                "— lootbox", #Spanish
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings)
                and '<:ruby' in message_field.lower()):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        search_patterns = [
                            "^(.+?)'s lootbox", #English
                            "^(.+?) — lootbox", #Spanish
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_author)
                        try:
                            user_name = user_name_match.group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in lootbox message for ruby counter: {message.embeds[0].fields}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in lootbox message for ruby counter: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                try:
                    ruby_pos = message_field.find('<:ruby')
                    number_start_pos = message_field.rfind('+', 0, ruby_pos)
                    ruby_count = re.search('\+(.+?) <:ruby', message_field[number_start_pos:]).group(1)
                    ruby_count = int(ruby_count.replace(',',''))
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Ruby count not found in lootbox message for ruby counter: {message.embeds[0].fields}',
                        message
                    )
                    return
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)
                if user_settings.rubies == ruby_count and user_settings.reactions_enabled:
                    await message.add_reaction(emojis.NAVI)

            # Rubies from inventory
            search_strings = [
                "'s inventory", #English
                "— inventory", #Spanish
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                user_id = user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                    except:
                        search_patterns = [
                            "^(.+?)'s inventory", #English
                            "^(.+?) — inventory", #Spanish
                        ]
                        user_name_match = await functions.get_match_from_patterns(search_patterns, message_author)
                        try:
                            user_name = user_name_match.group(1)
                            user_name = await functions.encode_text(user_name)
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'User not found in inventory message for ruby counter: {message.embeds[0].fields}',
                                message
                            )
                            return
                    if user_id is not None:
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in inventory message for ruby counter: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                if  '<:ruby' not in message_field.lower():
                    ruby_count = 0
                else:
                    try:
                        ruby_count = re.search("ruby\*\*: (.+?)\\n", message_field).group(1)
                        ruby_count = int(ruby_count.replace(',',''))
                    except:
                        try:
                            ruby_count = re.search("ruby\*\*: (.+?)$", message_field).group(1)
                            ruby_count = int(ruby_count.replace(',',''))
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'Ruby count not found in inventory message for ruby counter: {message.embeds[0].fields}',
                                message
                            )
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
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in ruby training message for ruby counter: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in ruby training message for ruby counter: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                search_patterns = [
                    'more than (.+?) <:ruby', #English
                    'más de (.+?) <:ruby', #Spanish
                ]
                ruby_count_match = await functions.get_match_from_patterns(search_patterns, message_content)
                try:
                    ruby_count = ruby_count_match.group(1)
                    ruby_count = int(ruby_count.replace(',',''))
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Ruby count not found in ruby training message for ruby counter: {message_content}',
                        message
                    )
                    return
                answer = '`YES`' if user_settings.rubies > ruby_count else '`NO`'
                if not user_settings.dnd_mode_enabled:
                    answer = f'{answer} {user.mention}' if user_settings.ping_after_message else f'{user.mention} {answer}'
                await message.reply(f'{answer} (you have {user_settings.rubies:,} {emojis.RUBY})')

            # Rubies from selling
            search_strings = [
                '`ruby` successfully sold', #English
                '`ruby` vendido(s) exitosamente', #Spanish
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgsellruby') and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the ruby sell message.',
                            message
                        )
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                try:
                    ruby_count = re.search('^(.+?) <:ruby', message_content, re.IGNORECASE).group(1)
                    ruby_count = int(ruby_count.replace(',',''))
                except:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Ruby count not found in sell message for ruby counter: {message_content}',
                        message
                    )
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
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and '<:ruby' in message_content.lower()):
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        '\*\*(.+?)\*\* got', #English
                        '\*\*(.+?)\*\* consiguió', #Spanish
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content) #case
                    try:
                        user_name = user_name_match.group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in work message for ruby counter: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in work message for ruby counter: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                search_patterns = [
                    '\*\* got (.+?) <:ruby', #English mine commands
                    ' had (.+?) <:ruby', #English proc pickup commands
                    '\*\* consiguió (.+?) <:ruby', #Spanish mine commands
                    'llevaba dentro (.+?) <:ruby', #Spanish proc pickup commands, RECHECK
                ]
                ruby_count_match = await functions.get_match_from_patterns(search_patterns, message_content) #case
                try:
                    ruby_count = ruby_count_match.group(1)
                    ruby_count = int(ruby_count.replace(',',''))
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Ruby count not found in work message for ruby counter: {message_content}',
                        message
                    )
                    return
                ruby_count += user_settings.rubies
                if ruby_count < 0: ruby_count == 0
                await user_settings.update(rubies=ruby_count)

            # Rubies from crafting ruby sword
            search_strings = [
                '`ruby sword` successfully crafted', #English
                '`ruby sword` crafteado(s) exitosamente', #Spanish
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgcraftrubysword') and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the ruby sword crafting message.',
                            message
                        )
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
                '`ruby armor` crafteado(s) exitosamente', #Spanish
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgcraftrubyarmor') and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the ruby armor crafting message.',
                            message
                        )
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
                '`coin sword` crafteado(s) exitosamente', #Spanish
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgcraftcoinsword') and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the coin sword crafting message.',
                            message
                        )
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
                '`ultra-edgy armor` successfully crafted', #English
                '`ultra-edgy armor` crafteado(s) exitosamente', #Spanish
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpgforgeultra-edgyarmor') and not msg.author.bot:
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the ultra-edgy armor crafting message.',
                            message
                        )
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