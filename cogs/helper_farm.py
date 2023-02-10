# helper_farm.py

import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from resources import exceptions, functions, regex, settings


class HelperFarmCog(commands.Cog):
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
            message_description = message_author = message_title = ''
            if embed.title: message_title = embed.title
            if embed.description: message_description = str(embed.description)
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Seeds and crops from inventory
            search_strings = [
                "— inventory", #All languages
            ]
            if any(search_string in message_author.lower() for search_string in search_strings):
                if icon_url == embed.Empty: return
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
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        return
                if interaction_user not in embed_users: return
                if not user_settings.bot_enabled or not user_settings.ruby_counter_enabled: return
                field_values = ''
                for field in embed.fields:
                    field_values = f'{field_values}\n{field.value}'
                bread_count = carrot_count = potato_count = seed_bread_count = seed_carrot_count = seed_potato_count = 0
                bread_match = re.search(r"bread\*\*: ([0-9,]+)", field_values)
                carrot_match = re.search(r"carrot\*\*: ([0-9,]+)", field_values)
                potato_match = re.search(r"potato\*\*: ([0-9,]+)", field_values)
                seed_bread_match = re.search(r"bread seed\*\*: ([0-9,]+)", field_values)
                seed_carrot_match = re.search(r"carrot seed\*\*: ([0-9,]+)", field_values)
                seed_potato_match = re.search(r"potato seed\*\*: ([0-9,]+)", field_values)
                if bread_match: bread_count = int(bread_match.group(1).replace(',',''))
                if carrot_match: carrot_count = int(carrot_match.group(1).replace(',',''))
                if potato_match: potato_count = int(potato_match.group(1).replace(',',''))
                if seed_bread_match: seed_bread_count = int(seed_bread_match.group(1).replace(',',''))
                if seed_carrot_match: seed_carrot_count = int(seed_carrot_match.group(1).replace(',',''))
                if seed_potato_match: seed_potato_count = int(seed_potato_match.group(1).replace(',',''))
                await user_settings.update(inventory_bread=bread_count, inventory_carrot=carrot_count,
                                           inventory_potato=potato_count, inventory_seed_bread=seed_bread_count,
                                           inventory_seed_carrot=seed_carrot_count,
                                           inventory_seed_potato=seed_potato_count)

            # Pets claim
            search_strings = [
                'pet adventure rewards', #English 1
                'reward summary', #English 2
                'recompensas de pet adventure', #Spanish, Portuguese 1
                'resumen de recompensas', #Spanish 2
                'resumo de recompensas', #Portuguese 2
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PETS_CLAIM)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet claim message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                kwargs = {}
                if message_description != '':
                    seed_match = re.search(r'^\+([0-9,]+) (?:.+?) \*\*(.+?)seed', message_description.lower(), re.MULTILINE)
                    if not seed_match: return
                    seed_count = int(seed_match.group(1))
                    seed_type = seed_match.group(2)
                    seed_type = seed_type.strip()
                    if seed_type == '': return
                    seed_count = getattr(user_settings.inventory, f'seed_{seed_type}') + seed_count
                    kwargs[f'inventory_seed_{seed_type}'] = seed_count
                else:
                    seeds_found = {
                        'bread': 0,
                        'carrot': 0,
                        'potato': 0,
                    }
                    for field in embed.fields:
                        if not 'pony' in field.name.lower(): continue
                        seed_match = re.search(r'>(.+?)seed', field.value.lower())
                        if not seed_match: continue
                        seed_found = seed_match.group(1).strip()
                        if seed_found != '':
                            seeds_found[seed_found] += 1
                    for seed_type, seed_amount in seeds_found.items():
                        if seed_amount > 0:
                            seed_count = getattr(user_settings.inventory, f'seed_{seed_type}') + seed_amount
                            kwargs[f'inventory_seed_{seed_type}'] = seed_count
                if kwargs: await user_settings.update(**kwargs)


        if not message.embeds:
            message_content = message.content

            # Special seed from guild shop
            if '`special seed`' in message_content.lower() and 'guild rings' in message_content.lower():
                message_content = message_content.split('\n')[1]
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r"^\*\*(.+?)\*\* got (\d+) (?:.+?) \*\*(.+?) seed", #English
                        r"^\*\*(.+?)\*\* cons[ie]gui[óu] (\d+) (?:.+?) \*\*(.+?) seed", #Spanish & Portuguese
                    ]
                    data_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if data_match:
                        user_name = data_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_CLAN_BUY_SPECIAL_SEED,
                                                        user_name=user_name)
                        )
                    if not data_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for guild buy special seed message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                kwargs = {}
                seed_type = data_match.group(3)
                seed_count = getattr(user_settings.inventory, f'seed_{seed_type}')
                seed_count += int(data_match.group(2))
                kwargs[f'inventory_seed_{seed_type}'] = seed_count
                await user_settings.update(**kwargs)


# Initialization
def setup(bot):
    bot.add_cog(HelperFarmCog(bot))