# helper_context.py

import discord
from discord.ext import commands

from database import users
from resources import exceptions, functions, settings


class HelperContextCog(commands.Cog):
    """Cog that contains the training helper detection"""
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
            embed_description = embed_title = embed_field0_name = embed_field0_value = ''
            if embed.description: embed_description = embed.description
            if embed.title: embed_title = embed.title
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value

            # Pets fusion
            search_strings = [
                'you have got a new pet', #English
                'conseguiste una nueva mascota', #Spanish
                'você tem um novo pet', #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_pets_fusion = await functions.get_slash_command(user_settings, 'pets fusion')
                command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                answer = (
                    f"➜ {command_pets_fusion}\n"
                    f"➜ {command_pets_list}\n"
                )
                await message.reply(answer)

            # Caught new pet
            search_strings = [
                '** is now following **', #English
                '** ahora sigue a **', #Spanish
                '** agora segue **', #Portuguese
            ]
            if any(search_string in embed_field0_value.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                answer = (
                    f"➜ {command_pets_list}\n"
                )
                await message.reply(answer)

            # Pets claim
            search_strings = [
                'pet adventure rewards', #English
                'recompensas de pet adventure', #Spanish & Portuguese
            ]
            if any(search_string in embed_title.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_pets_adv = await functions.get_slash_command(user_settings, 'pets adventure')
                command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                answer = (
                    f"➜ {command_pets_adv}\n"
                    f"➜ {command_pets_list}\n"
                )
                await message.reply(answer)

            # Vote embed
            search_strings = [
                'next vote rewards', #English
                'recompensas del siguiente voto', #Spanish
                'recompensas do próximo voto', #Portuguese
            ]
            if (any(search_string in embed_field0_name.lower() for search_string in search_strings)
                and not 'cooldown:' in embed_field0_value.lower()):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_adventure = await functions.get_slash_command(user_settings, 'adventure')
                if user_settings.last_adventure_mode != '':
                    command_adventure = f'{command_adventure} `mode: {user_settings.last_adventure_mode}`'
                answer = (
                    f"➜ {command_adventure}\n"
                )
                await message.reply(answer)


        if not message.embeds:
            message_content = message.content

            # Pets adventure
            search_strings = [
                'your pet has started an adventure and will be back', #English 1 pet
                'pets have started an adventure!', #English multiple pets
                'tu mascota empezó una aventura y volverá', #Spanish 1 pet
                'tus mascotas han comenzado una aventura!', #Spanish multiple pets
                'seu pet começou uma aventura e voltará', #Portuguese 1 pet
                'seus pets começaram uma aventura!', #Portuguese multiple pets
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                search_strings_tt = [
                    'the following pets are back instantly', #English
                    'voidog pet made all pets travel', #English VOIDog
                    'las siguientes mascotas están de vuelta instantaneamente', #Spanish
                    'mascota voidog hizo que todas tus mascotas', #Spanish VOIDog
                    'os seguintes pets voltaram instantaneamente', #Portuguese
                    'voidog fez todos os bichinhos', #Portuguese VOIDog
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_tt):
                    command_pets_claim = await functions.get_slash_command(user_settings, 'pets claim')
                    answer = f"➜ {command_pets_claim}"
                else:
                    command_pets_adv = await functions.get_slash_command(user_settings, 'pets adventure')
                    command_pets_list = await functions.get_slash_command(user_settings, 'pets list')
                    answer = (
                        f"➜ {command_pets_adv}\n"
                        f"➜ {command_pets_list}\n"
                    )
                await message.reply(answer)

            # Single pet TT trigger
            search_strings = [
                'it came back instantly!!', #English
                'volvio al instante!!', #Spanish
                'voltou instantaneamente!!', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_pets_claim = await functions.get_slash_command(user_settings, 'pets claim')
                await message.reply(f"➜ {command_pets_claim}")

            # Quest - Only works with slash
            search_strings = [
                'got a **new quest**!', #English accepted
                'consiguió una **nueva misión**', #Spanish accepted
                'conseguiu uma **nova missão**', #Portuguese accepted
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                if message.reference.cached_message is not None:
                    quest_message = message.reference.cached_message
                else:
                    quest_message = await message.channel.fetch_message(message.reference.message_id)
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                search_strings_gambling = [
                    'gambling quest', #English
                    'misión de apuestas', #Spanish
                    'missão de aposta', #Portuguese
                ]
                search_strings_guild = [
                    'guild quest', #English
                    'misión de guild', #Spanish
                    'missão de guild', #Portuguese
                ]
                search_strings_crafting = [
                    'crafting quest', #English
                    'misión de crafteo', #Spanish
                    'missão de craft', #Portuguese
                ]
                search_strings_cooking = [
                    'cooking quest', #English
                    'misión de cocina', #Spanish
                    'missão de cozinha', #Portuguese
                ]
                search_strings_trading = [
                    'trading quest', #English
                    'misión de intercambio', #Spanish
                    'missão de troca', #Portuguese
                ]
                quest_field = quest_message.embeds[0].fields[0].value.lower()
                if any(search_string in quest_field for search_string in search_strings_gambling):
                    command_big_dice = await functions.get_slash_command(user_settings, 'big dice')
                    command_blackjack = await functions.get_slash_command(user_settings, 'blackjack')
                    command_coinflip = await functions.get_slash_command(user_settings, 'coinflip')
                    command_cups = await functions.get_slash_command(user_settings, 'cups')
                    command_dice = await functions.get_slash_command(user_settings, 'dice')
                    command_multidice = await functions.get_slash_command(user_settings, 'multidice')
                    command_slots = await functions.get_slash_command(user_settings, 'slots')
                    command_wheel = await functions.get_slash_command(user_settings, 'wheel')
                    answer = (
                        f"➜ {command_big_dice}\n"
                        f"➜ {command_blackjack}\n"
                        f"➜ {command_coinflip}\n"
                        f"➜ {command_cups}\n"
                        f"➜ {command_dice}\n"
                        f"➜ {command_multidice}\n"
                        f"➜ {command_slots}\n"
                        f"➜ {command_wheel}\n"
                    )
                elif any(search_string in quest_field for search_string in search_strings_guild):
                    command_raid = await functions.get_slash_command(user_settings, 'guild raid')
                    command_upgrade = await functions.get_slash_command(user_settings, 'guild upgrade')
                    answer = (
                        f"➜ {command_raid}\n"
                        f"➜ {command_upgrade}\n"
                    )
                elif any(search_string in quest_field for search_string in search_strings_crafting):
                    command_craft = await functions.get_slash_command(user_settings, 'craft')
                    command_dismantle = await functions.get_slash_command(user_settings, 'dismantle')
                    answer = (
                        f"➜ {command_craft}\n"
                        f"➜ {command_dismantle}\n"
                    )
                elif any(search_string in quest_field for search_string in search_strings_cooking):
                    command_cook = await functions.get_slash_command(user_settings, 'cook')
                    answer = (
                        f"➜ {command_cook}\n"
                    )
                elif any(search_string in quest_field for search_string in search_strings_trading):
                    command_trade = await functions.get_slash_command(user_settings, 'trade items')
                    answer = (
                        f"➜ {command_trade}\n"
                    )
                else:
                    return
                await message.reply(answer)

            search_strings = [
                'is now in the jail', #English
                'is now in the jail', #Spanish, MISSING
                'is now in the jail', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                if user is None: return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.context_helper_enabled: return
                command_jail = await functions.get_slash_command(user_settings, 'jail')
                await message.reply(f"➜ {command_jail}")


# Initialization
def setup(bot):
    bot.add_cog(HelperContextCog(bot))