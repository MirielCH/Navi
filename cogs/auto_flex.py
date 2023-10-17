# auto_flex.py

import random
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, guilds, users
from resources import emojis, exceptions, functions, regex, settings, strings


FLEX_TITLES = {
    'artifacts': strings.FLEX_TITLES_ARTIFACTS,
    'brew_electronical': strings.FLEX_TITLES_BREW_ELECTRONICAL,
    'epic_berry': strings.FLEX_TITLES_EPIC_BERRY,
    'epic_berry_partner': strings.FLEX_TITLES_EPIC_BERRY_PARTNER,
    'event_coinflip': strings.FLEX_TITLES_EVENT_COINFLIP,
    'event_enchant': strings.FLEX_TITLES_EVENT_ENCHANT,
    'event_farm': strings.FLEX_TITLES_EVENT_FARM,
    'event_heal': strings.FLEX_TITLES_EVENT_HEAL,
    'event_lb': strings.FLEX_TITLES_EVENT_LB,
    'event_training': strings.FLEX_TITLES_EVENT_TRAINING,
    'forge_cookie': strings.FLEX_TITLES_FORGE_COOKIE,
    'hal_boo': strings.FLEX_TITLES_HAL_BOO,
    'lb_a18': strings.FLEX_TITLES_LB_A18,
    'lb_a18_partner': strings.FLEX_TITLES_LB_A18_PARTNER,
    'lb_edgy_ultra': strings.FLEX_TITLES_EDGY_ULTRA,
    'lb_godly': strings.FLEX_TITLES_LB_GODLY,
    'lb_godly_partner': strings.FLEX_TITLES_LB_GODLY_PARTNER,
    'lb_godly_tt': strings.FLEX_TITLES_GODLY_TT,
    'lb_omega_multiple': strings.FLEX_TITLES_LB_OMEGA_MULTIPLE,
    'lb_omega_no_hardmode': strings.FLEX_TITLES_LB_OMEGA_NOHARDMODE,
    'lb_omega_partner': strings.FLEX_TITLES_LB_OMEGA_PARTNER,
    'lb_omega_ultra': strings.FLEX_TITLES_OMEGA_ULTRA,
    'lb_party_popper': strings.FLEX_TITLES_PARTY_POPPER,
    'lb_void': strings.FLEX_TITLES_LB_VOID,
    'lb_void_partner': strings.FLEX_TITLES_LB_VOID_PARTNER,
    'pets_catch_epic': strings.FLEX_TITLES_PETS_CATCH_EPIC,
    'pets_catch_tt': strings.FLEX_TITLES_PETS_CATCH_TT,
    'pets_claim_omega': strings.FLEX_TITLES_PETS_CLAIM_OMEGA,
    'pr_ascension': strings.FLEX_TITLES_PR_ASCENSION,
    'time_travel_1': strings.FLEX_TITLES_TIME_TRAVEL_1,
    'time_travel_3': strings.FLEX_TITLES_TIME_TRAVEL_3,
    'time_travel_5': strings.FLEX_TITLES_TIME_TRAVEL_5,
    'time_travel_10': strings.FLEX_TITLES_TIME_TRAVEL_10,
    'time_travel_25': strings.FLEX_TITLES_TIME_TRAVEL_25,
    'time_travel_50': strings.FLEX_TITLES_TIME_TRAVEL_50,
    'time_travel_100': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_150': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_200': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_300': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_400': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_420': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_500': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_600': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_700': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_800': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_900': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_999': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'work_epicberry': strings.FLEX_TITLES_WORK_EPICBERRY,
    'work_hyperlog': strings.FLEX_TITLES_WORK_HYPERLOG,
    'work_ultimatelog': strings.FLEX_TITLES_WORK_ULTIMATELOG,
    'work_ultralog': strings.FLEX_TITLES_WORK_ULTRALOG,
    'work_superfish': strings.FLEX_TITLES_WORK_SUPERFISH,
    'work_watermelon': strings.FLEX_TITLES_WORK_WATERMELON,
    'xmas_chimney': strings.FLEX_TITLES_XMAS_CHIMNEY,
    'xmas_godly': strings.FLEX_TITLES_XMAS_GODLY,
    'xmas_snowball': strings.FLEX_TITLES_XMAS_SNOWBALL,
    'xmas_void': strings.FLEX_TITLES_XMAS_VOID,
}

FLEX_THUMBNAILS = {
    'artifacts': strings.FLEX_THUMBNAILS_ARTIFACTS,
    'brew_electronical': strings.FLEX_THUMBNAILS_BREW_ELECTRONICAL,
    'epic_berry': strings.FLEX_THUMBNAILS_EPIC_BERRY,
    'epic_berry_partner': strings.FLEX_THUMBNAILS_EPIC_BERRY_PARTNER,
    'event_coinflip': strings.FLEX_THUMBNAILS_EVENT_COINFLIP,
    'event_enchant': strings.FLEX_THUMBNAILS_EVENT_ENCHANT,
    'event_farm': strings.FLEX_THUMBNAILS_EVENT_FARM,
    'event_heal': strings.FLEX_THUMBNAILS_EVENT_HEAL,
    'event_lb': strings.FLEX_THUMBNAILS_EVENT_LB,
    'event_training': strings.FLEX_THUMBNAILS_EVENT_TRAINING,
    'forge_cookie': strings.FLEX_THUMBNAILS_FORGE_COOKIE,
    'hal_boo': strings.FLEX_THUMBNAILS_HAL_BOO,
    'lb_a18': strings.FLEX_THUMBNAILS_LB_A18,
    'lb_a18_partner': strings.FLEX_THUMBNAILS_LB_A18_PARTNER,
    'lb_edgy_ultra': strings.FLEX_THUMBNAILS_EDGY_ULTRA,
    'lb_godly': strings.FLEX_THUMBNAILS_LB_GODLY,
    'lb_godly_partner': strings.FLEX_THUMBNAILS_LB_GODLY_PARTNER,
    'lb_godly_tt': strings.FLEX_THUMBNAILS_GODLY_TT,
    'lb_omega_multiple': strings.FLEX_THUMBNAILS_LB_OMEGA_MULTIPLE,
    'lb_omega_no_hardmode': strings.FLEX_THUMBNAILS_LB_OMEGA_NOHARDMODE,
    'lb_omega_partner': strings.FLEX_THUMBNAILS_LB_OMEGA_PARTNER,
    'lb_omega_ultra': strings.FLEX_THUMBNAILS_OMEGA_ULTRA,
    'lb_party_popper': strings.FLEX_THUMBNAILS_PARTY_POPPER,
    'lb_void': strings.FLEX_THUMBNAILS_LB_VOID,
    'lb_void_partner': strings.FLEX_THUMBNAILS_LB_VOID_PARTNER,
    'pets_catch_epic': strings.FLEX_THUMBNAILS_PETS_CATCH_EPIC,
    'pets_catch_tt': strings.FLEX_THUMBNAILS_PETS_CATCH_TT,
    'pets_claim_omega': strings.FLEX_THUMBNAILS_PETS_CLAIM_OMEGA,
    'pr_ascension': strings.FLEX_THUMBNAILS_PR_ASCENSION,
    'time_travel_1': strings.FLEX_THUMBNAILS_TIME_TRAVEL_1,
    'time_travel_3': strings.FLEX_THUMBNAILS_TIME_TRAVEL_3,
    'time_travel_5': strings.FLEX_THUMBNAILS_TIME_TRAVEL_5,
    'time_travel_10': strings.FLEX_THUMBNAILS_TIME_TRAVEL_10,
    'time_travel_25': strings.FLEX_THUMBNAILS_TIME_TRAVEL_25,
    'time_travel_50': strings.FLEX_THUMBNAILS_TIME_TRAVEL_50,
    'time_travel_100': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_150': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_200': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_300': strings.FLEX_THUMBNAILS_TIME_TRAVEL_300,
    'time_travel_400': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_420': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_500': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_600': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_700': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_800': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_900': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_999': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'work_epicberry': strings.FLEX_THUMBNAILS_WORK_EPICBERRY,
    'work_hyperlog': strings.FLEX_THUMBNAILS_WORK_HYPERLOG,
    'work_ultimatelog': strings.FLEX_THUMBNAILS_WORK_ULTIMATELOG,
    'work_ultralog': strings.FLEX_THUMBNAILS_WORK_ULTRALOG,
    'work_superfish': strings.FLEX_THUMBNAILS_WORK_SUPERFISH,
    'work_watermelon': strings.FLEX_THUMBNAILS_WORK_WATERMELON,
    'xmas_chimney': strings.FLEX_THUMBNAILS_XMAS_CHIMNEY,
    'xmas_godly': strings.FLEX_THUMBNAILS_XMAS_GODLY,
    'xmas_snowball': strings.FLEX_THUMBNAILS_XMAS_SNOWBALL,
    'xmas_void': strings.FLEX_THUMBNAILS_XMAS_VOID,
}

# Auto flexes that have a column name that differs from the event name
FLEX_COLUMNS = {
    'epic_berry_partner': 'epic_berry',
    'lb_a18_partner': 'lb_a18',
    'lb_godly_partner': 'lb_godly',
    'lb_omega_multiple': 'lb_omega',
    'lb_omega_no_hardmode': 'lb_omega',
    'lb_omega_partner': 'lb_omega',
    'lb_void_partner': 'lb_void',
    'time_travel_1': 'time_travel',
    'time_travel_3': 'time_travel',
    'time_travel_5': 'time_travel',
    'time_travel_10': 'time_travel',
    'time_travel_25': 'time_travel',
    'time_travel_50': 'time_travel',
    'time_travel_100': 'time_travel',
    'time_travel_150': 'time_travel',
    'time_travel_200': 'time_travel',
    'time_travel_300': 'time_travel',
    'time_travel_400': 'time_travel',
    'time_travel_420': 'time_travel',
    'time_travel_500': 'time_travel',
    'time_travel_600': 'time_travel',
    'time_travel_700': 'time_travel',
    'time_travel_800': 'time_travel',
    'time_travel_900': 'time_travel',
    'time_travel_999': 'time_travel',
}

class AutoFlexCog(commands.Cog):
    """Cog that contains the auto flex detection"""
    def __init__(self, bot):
        self.bot = bot

    async def send_auto_flex_message(self, message: discord.Message, guild_settings: guilds.Guild,
                                     user_settings: users.User, user: discord.User, event: str,
                                     description: str) -> None:
        """Sends a flex embed to the auto flex channel"""
        event_column = FLEX_COLUMNS[event] if event in FLEX_COLUMNS else event
        auto_flex_setting = getattr(guild_settings, f'auto_flex_{event_column}_enabled', None)
        if auto_flex_setting is None:
            await functions.add_warning_reaction(message)
            await errors.log_error(f'Couldn\'t find auto flex setting for event "{event}"', message)
            return
        if not auto_flex_setting: return
        description = f'{description}\n\n[Check it out]({message.jump_url})'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = random.choice(FLEX_TITLES[event]),
            description = description,
        )
        if 'ascension' in event:
            author = f'{user.name} is advancing!'
        elif 'chimney' in event:
            author = f'{user.name} got stuck!'
        elif 'time_travel' in event:
            author = f'{user.name} is traveling in time!'
        elif 'a18_partner' in event:
            author = f'{user.name} is being mean!'
        elif 'a18' in event:
            author = f'{user.name} is losing their stuff!'
        elif 'partner' in event:
            author = f'{user.name} got robbed!'
        else:
            author = f'{user.name} got lucky!'
        embed.set_author(icon_url=user.display_avatar.url, name=author)
        embed.set_thumbnail(url=random.choice(FLEX_THUMBNAILS[event]))
        embed.set_footer(text='Use \'/settings user\' to enable or disable auto flex.')
        auto_flex_channel = await functions.get_discord_channel(self.bot, guild_settings.auto_flex_channel_id)
        if auto_flex_channel is None:
            await functions.add_warning_reaction(message)
            await errors.log_error('Couldn\'t find auto flex channel.', message)
            return
        await auto_flex_channel.send(embed=embed)
        if user_settings.reactions_enabled: await message.add_reaction(emojis.PANDA_LUCKY)
        if not user_settings.auto_flex_tip_read:
            await message.reply(
                f'{user.mention} Nice! You just did something flex worthy. Because you have auto flex enabled, '
                f'this was automatically posted to the channel <#{guild_settings.auto_flex_channel_id}>.\n'
                f'If you don\'t like this, you can turn it off in '
                f'{await functions.get_navi_slash_command(self.bot, "settings user")}.'
            )
            await user_settings.update(auto_flex_tip_read=True)

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
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID, settings.OWNER_ID]: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_title = embed_field0_name = embed_field0_value = embed_autor = icon_url = ''
            embed_field1_value = embed_field1_name = embed_fields = ''
            if embed.description: embed_description = embed.description
            if embed.title: embed_title = embed.title
            if embed.fields:
                for field in embed.fields:
                    embed_fields = f'{embed_fields}\n{field.value}'
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
            if len(embed.fields) > 1:
                embed_field1_name = embed.fields[1].name
                embed_field1_value = embed.fields[1].value
            if embed.author:
                embed_autor = embed.author.name
                icon_url = embed.author.icon_url

            # Rare loot from lootboxes
            search_strings = [
                "— lootbox", #All languages
            ]
            if any(search_string in embed_autor.lower() for search_string in search_strings):
                if 'edgy lootbox' in embed_field0_name.lower() and '<:ultralog' in embed_field0_value.lower():
                    event = 'lb_edgy_ultra'
                elif 'omega lootbox' in embed_field0_name.lower() and '<:ultralog' in embed_field0_value.lower():
                    event = 'lb_omega_ultra'
                elif 'godly lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_godly_tt'
                elif '<:partypopper' in embed_field0_value.lower():
                    event = 'lb_party_popper'
                else:
                    return
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_OPEN, user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex lootbox message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if event == 'lb_edgy_ultra':
                    match = re.search(r'\+(.+?) (.+?) ultra log', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('ULTRA log amount not found in auto flex edgy lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Look at **{user.name}**, opening that {emojis.LB_EDGY} EDGY lootbox like it\'s worth '
                        f'anything, haha.\n'
                        f'See, all they got is **{amount}** lousy **{emojis.LOG_ULTRA} ULTRA log**!\n\n'
                        f'_**Wait...**_'
                    )
                elif event == 'lb_omega_ultra':
                    match = re.search(r'\+(.+?) (.+?) ultra log', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('ULTRA log amount not found in auto flex omega lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Never get ULTRAs out of {emojis.LB_OMEGA} **OMEGA lootboxes**?\n'
                        f'**{user.name}** can teach you how it works. They just hacked **{amount}** {emojis.LOG_ULTRA} '
                        f'**ULTRA logs** out of theirs.'
                    )
                elif event == 'lb_godly_tt':
                    match = re.search(r'\+(.+?) (.+?) time capsule', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time capsule amount not found in auto flex godly lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'So.\n**{user.name}** opened a {emojis.LB_GODLY} GODLY lootbox. I mean that\'s cool.\n'
                        f'__BUT__. For some reason they found **{amount}** {emojis.TIME_CAPSULE} **time capsule** in there.\n'
                        f'This hasn\'t happened often yet, so expect to get blacklisted from the game.'
                    )
                elif event == 'lb_party_popper':
                    match = re.search(r'\+(.+?) (.+?) party popper', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Party popper amount not found in auto flex godly lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'**{user.name}** opened a lootbox and found **{amount}**, uh... {emojis.PARTY_POPPER} **party popper**?\n'
                        f'I\'m not exactly sure what this is doing in a lootbox, but I hear it\'s rare, so GG I guess?'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Ascension
            search_strings = [
                "unlocked the ascended skill", #English
            ]
            if any(search_string in embed_field0_name.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\*', embed_field0_name)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_PROFESSIONS_ASCEND,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in auto flex ascension message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** just **ascended**.\n\n'
                    f'Yep, just like that! Congratulations!!\n\n'
                    f'Too bad the `ascended` command is gone, it was so much fun...'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'pr_ascension', description)

            # Pets catch
            search_strings = [
                "**dog** is now following", #English, dog
                "**cat** is now following", #English, cat
                "**dragon** is now following", #English, dragon
            ]
            if (any(search_string in embed_field0_value.lower() for search_string in search_strings)
                and ('epic**' in embed_field0_value.lower() or 'time traveler**' in embed_field0_value.lower())):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* is now following \*\*(.+?)\*\*!', #English
                ]
                pet_data_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not pet_data_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Pet type or user name not found in auto flex pets catch message.',
                                            message)
                    return
                pet_type = pet_data_match.group(1)
                user_name = pet_data_match.group(2)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for auto flex pets catch message.',
                                                message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if 'time traveler' in embed_field0_value.lower():
                    event = 'pets_catch_tt'
                    description = (
                        f'**{user.name}** took a stroll when a {emojis.SKILL_TIME_TRAVELER} **time traveler** '
                        f'{pet_type.lower()} popped out of nothingness.\n'
                        f'Wonder if the doctor will come after it?'
                    )
                else:
                    event = 'pets_catch_epic'
                    description = (
                        f'**{user.name}** caught a {pet_type.lower()}.\n'
                        f'What? Not very exciting? HA, but this was an {emojis.SKILL_EPIC} **EPIC** {pet_type.lower()}!\n'
                        f'What do you say now?'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Pet adventure rewards
            search_strings = [
                'pet adventure rewards', #English 1
                'reward summary', #English 2
                'recompensas de pet adventure', #Spanish, Portuguese 1
                'resumen de recompensas', #Spanish 2
                'resumo de recompensas', #Portuguese 2
            ]
            search_strings_items = [
                'omega lootbox',
            ]
            if (any(search_string in embed_title.lower() for search_string in search_strings)
                and (
                    any(search_string in embed_fields.lower() for search_string in search_strings_items)
                    or any(search_string in embed_description.lower() for search_string in search_strings_items)
                    )
                ):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PETS_CLAIM)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in autoflex pet claim message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** threatened a poor **snowman** pet with a hair dryer and forced him to bring back '
                    f'an {emojis.LB_OMEGA} **OMEGA lootbox**.\n'
                    f'Calvin would be proud.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'pets_claim_omega',
                                                  description)

            # Coinflip event
            search_strings = [
                "where is the coin?", #English
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_COINFLIP,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex coinflip message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if user_settings.current_area == 19: return
                description = (
                    f'**{user.name}** did some coinflipping and **lost the coin**.\n'
                    f'I mean, how hard can it be, seriously? That\'s just embarassing!'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_coinflip',
                                                  description)

            # Update time travel count from profile
            search_strings = [
                "— profile", #All languages
                "— progress", #All languages
            ]
            if (any(search_string in embed_autor.lower() for search_string in search_strings)
                and not 'epic npc' in embed_autor.lower()):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PROFILE_PROGRESS,
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
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if len(embed_field0_value.split('\n')) < 4:
                    time_travel_count = 0
                else:
                    search_patterns = [
                        'time travels\*\*: (.+?)$', #English
                        'el tiempo\*\*: (.+?)$', #Spanish
                        'no tempo\*\*: (.+?)$', #Portuguese
                    ]
                    tt_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                    if not tt_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time travel count not found in profile or progress message.', message)
                        return
                    time_travel_count = int(tt_match.group(1))
                await user_settings.update(time_travel_count=time_travel_count)

            # Update time travel count from time travel message
            search_strings = [
                "— time travel", #All languages
                "— super time travel", #All languages
                "— time jump", #All languages
            ]
            if any(search_string in embed_autor.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
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
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                search_patterns = [
                    'this will be your time travel #(.+?)\n', #English
                    'esta será sua viagem no tempo #(.+?)$', #Spanish, Portuguese
                ]
                tt_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                if tt_match:
                    time_travel_count = int(tt_match.group(1)) - 1
                if not tt_match:
                    search_strings = [
                        'are you sure you want to **time travel**?', #English
                        'estás seguro que quieres **viajar en el tiempo**?', #Spanish
                        'tem certeza de que deseja **viajar no tempo**?', #Portuguese
                    ]
                    if any(search_string in embed_description.lower() for search_string in search_strings):
                        next_tt = True
                    else:
                        next_tt = False
                    search_patterns = [
                        'time travels\*\*: (.+?)\n', #English
                        'extra pet slots\*\*: (.+?)\n', #English
                        'viajes en el tiempo\*\*: (.+?)\n', #Spanish
                        'espacio adicional para mascotas\*\*: (.+?)\n', #Spanish
                        'viagem no tempo\*\*: (.+?)\n', #Portuguese
                        'espaços extras para pets\*\*: (.+?)\n', #Portuguese
                    ]
                    tt_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                    if tt_match:
                        time_travel_count = int(tt_match.group(1))
                        if next_tt: time_travel_count -= 1
                    else:
                        return
                await user_settings.update(time_travel_count=time_travel_count)

            # Time travel
            search_strings = [
                "has traveled in time", #English
                'viajou no tempo', #Spanish
                'tempo de viagem', #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\* has', embed_description)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in auto flex time travel message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.auto_flex_enabled
                    or user_settings.time_travel_count is None): return
                added_tts = 1
                extra_tt_match = re.search(r'\+(\d+?) <', embed_description)
                if extra_tt_match: added_tts += int(extra_tt_match.group(1))
                time_travel_count_old = user_settings.time_travel_count
                time_travel_count_new = time_travel_count_old + added_tts
                await user_settings.update(time_travel_count=time_travel_count_new)
                if time_travel_count_old < 1 and time_travel_count_new >= 1:
                    event = 'time_travel_1'
                    description = (
                        f'**{user.name}** just reached their very **first** {emojis.TIME_TRAVEL} **time travel**!\n'
                        f'Congratulations, we are expecting great things of you!'
                    )
                elif time_travel_count_old < 3 and time_travel_count_new >= 3:
                    event = 'time_travel_3'
                    description = (
                        f'**{user.name}** did it again (and again) and just reached {emojis.TIME_TRAVEL} **TT 3**!\n'
                        f'I think they\'re getting addicted.'
                    )
                elif time_travel_count_old < 5 and time_travel_count_new >= 5:
                    event = 'time_travel_5'
                    description = (
                        f'**{user.name}** got addicted to this game and just reached {emojis.TIME_TRAVEL} **TT 5**!\n'
                        f'The boss in D13 can\'t wait to see you.'
                    )
                elif time_travel_count_old < 10 and time_travel_count_new >= 10:
                    event = 'time_travel_10'
                    description = (
                        f'**{user.name}** is getting serious. {emojis.TIME_TRAVEL} **TT 10** achieved!\n'
                        f'Hope you\'re not colorblind. Also I hope you don\'t expect to survive in A15.'
                    )
                elif time_travel_count_old < 25 and time_travel_count_new >= 25:
                    event = 'time_travel_25'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 25**!\n'
                        f'Good news: You are now in the endgame!\n'
                        f'Bad news: Hope you like dragon scales.'
                    )
                elif time_travel_count_old < 50 and time_travel_count_new >= 50:
                    event = 'time_travel_50'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 50**!\n'
                        f'Sadly they went blind after seeing the profile background they got as a reward.'
                    )
                elif time_travel_count_old < 100 and time_travel_count_new >= 100:
                    event = 'time_travel_100'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 100**!\n'
                        f'Damn, you must really like this game. Enjoy your new high quality background!\n'
                        f'Don\'t forget your sunglasses.'
                    )
                elif time_travel_count_old < 150 and time_travel_count_new >= 150:
                    event = 'time_travel_150'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 150**!\n'
                        f'I\'m starting to question your life choices.\n'
                        f'You can stop playing now btw, there will be no more backgrounds.\n'
                    )
                elif time_travel_count_old < 200 and time_travel_count_new >= 200:
                    event = 'time_travel_200'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 200**!\n'
                        f'What on earth made you do this 200 times? You mad?\n'
                    )
                elif time_travel_count_old < 300 and time_travel_count_new >= 300:
                    event = 'time_travel_300'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **SPARTA**!\n'
                    )
                elif time_travel_count_old < 400 and time_travel_count_new >= 400:
                    event = 'time_travel_400'
                    description = (
                        f'Public Service Alert! **{user.name}** traveled in time **400** times {emojis.TIME_TRAVEL}!\n'
                        f'As to why tho... I couldn\'t say.'
                    )
                elif time_travel_count_old < 420 and time_travel_count_new >= 420:
                    event = 'time_travel_420'
                    description = (
                        f'**4:20 {user.name}**. The usual place.'
                    )
                elif time_travel_count_old < 500 and time_travel_count_new >= 500:
                    event = 'time_travel_500'
                    description = (
                        f'Did you see that? It\'s **{user.name}** plopping through time. For the freaking **500**th time.\n'
                        f'{emojis.TIME_TRAVEL}\n'
                    )
                elif time_travel_count_old < 600 and time_travel_count_new >= 600:
                    event = 'time_travel_600'
                    description = (
                        f'Pretty sury **{user.name}** forgot by now which time they actually belong to after '
                        f'**600** {emojis.TIME_TRAVEL} time travels.\n'
                    )
                elif time_travel_count_old < 700 and time_travel_count_new >= 700:
                    event = 'time_travel_700'
                    description = (
                        f'Did you know that there is such a thing as playing a game too much? **{user.name}** can.\n'
                        f'They just reached **700** {emojis.TIME_TRAVEL} time travels, and it scares me.\n'
                    )
                elif time_travel_count_old < 800 and time_travel_count_new >= 800:
                    event = 'time_travel_800'
                    description = (
                        f'**800** {emojis.TIME_TRAVEL} time travels. It\'s rather crazy. But I get it now - '
                        f'**{user.name}** is probably training for the time olympics on Galifrey.'
                    )
                elif time_travel_count_old < 900 and time_travel_count_new >= 900:
                    event = 'time_travel_900'
                    description = (
                        f'Ted just called **{user.name}** and wanted his phone booth back. After learning it was '
                        f'used for **900** {emojis.TIME_TRAVEL} time travels, he was too scared to take it back tho.'
                    )
                elif time_travel_count_old < 999 and time_travel_count_new >= 999:
                    event = 'time_travel_999'
                    description = (
                        f'**{user.name}** traveled in time for **999** times and thus broke Epic RPG Guide. Good job.\n'
                        f'Hope you\'re proud. Damn it.'
                    )
                else:
                    return
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Christmas loot, quest and duel embeds
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
                'epic snowball', #All languages, epic snowball
            ]
            if (any(search_string in embed_field0_value.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #English
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #Spanish/Portuguese
                ]
                item_events = {
                    'godly present': 'xmas_godly',
                    'void present': 'xmas_void',
                    'epic snowball': 'xmas_snowball',
                }
                match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                guild_users = await functions.get_guild_member_by_name(message.guild, user_name)
                if len(guild_users) > 1:
                    await functions.add_warning_reaction(message)
                    await message.reply(
                        f'Congratulations **{user_name}**, you found something worthy of an auto flex!\n'
                        f'Sadly I am unable to determine who you are as your username is not unique.\n'
                        f'To resolve this, either change your username (not nickname!) or use slash commands next time.'
                    )
                    return
                if not guild_users: return
                user = guild_users[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} '
                        f'{emojis.PRESENT_VOID} **VOID present**, duh.'
                    )
                elif event == 'xmas_snowball':
                    description = (
                        f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                        f'I sense a snowman in their not-so-distant future.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas presents, ultraining embed
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
            ]
            if (any(search_string in embed_field1_value.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b|\bvoid\b) \bpresent\b', #English godly and void present
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (godly\b|void\b) \bpresent', #Spanish/Portuguese godly and void present
                ]
                item_events = {
                    'godly': 'xmas_godly',
                    'void': 'xmas_void',
                }
                match = await functions.get_match_from_patterns(search_patterns, embed_field1_value)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    else:
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_ULTRAINING,
                                                        user_name=user_name)
                        )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex christmas present quest/ultr message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} '
                        f'{emojis.PRESENT_VOID} **VOID present**, duh.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # EPIC snowball from snowball fight
            search_strings = [
                'epic snowball', #All languages
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r' \*\*(.+?)\*\* also got (.+?) (.+?) \*\*EPIC snowball\*\*', #English
                ]
                match = await functions.get_match_from_patterns(search_patterns, embed_description)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, r'(?:\bsummon\b|\bfight\b|\bsleep\b)',
                            user_name=user_name, no_prefix=True
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex epic snowball fight message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                    f'I sense a snowman in their not-so-distant future.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'xmas_snowball', description)

        if not message.embeds:
            message_content = message.content

            # Craft artifacts
            search_strings_1 = [
                '** successfully crafted!', #English
            ]
            search_strings_2 = [
                'see `artifacts`', #English
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings_1)
                and any(search_string in message_content.lower() for search_string in search_strings_2)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_CRAFT_ARTIFACT)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex craft artifact message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                artifact_name_match = re.search(r'\*\*(.+?)\*\* ', message_content.lower())
                artifact_name = artifact_name_match.group(1)
                artifact_emoji = strings.ARTIFACTS_EMOJIS.get(artifact_name, '')

                if artifact_name == 'vampire teeth':
                    description = (
                        f'**{user.name}** found, uh... well. Some {artifact_emoji} **{artifact_name}**.\n'
                        f'In 3 parts.\n'
                        f'And then reassembled them.\n'
                        f'... yes.'
                    )
                else:
                    description = (
                        f'**{user.name}** found some dusty old parts and crafted a {artifact_emoji} **{artifact_name}** '
                        f'with them!\n'
                        f'That thing looks weird, bro.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'artifacts',
                                                  description)

            # Loot from work commands
            search_strings = [
                'this may be the luckiest moment of your life', #English, ultimate logs
                'is this a **dream**????', #English, ultra logs
                'oooooofff!!', #English, super fish
                'wwwooooooaaa!!!1', #English, hyper logs
                '**epic berry**', #English, epic berries
            ]
            search_strings_excluded = [
                'contribu', #All languages, void contributions
                'epic bundle', #All languages, void contributions
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and all(search_string not in message_content.lower() for search_string in search_strings_excluded)
                or ('nice!' in message_content.lower() and 'watermelon' in message_content.lower())):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\?\? \*\*(.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English ULTRA log
                    r'!!1 (.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English HYPER log
                    r' \*\*(.+?)\*\* got (.+?) (.+?) __\*\*(ultimate log)\*\*__', #English ULTIMATE log
                    r'\*\*(.+?)\*\* also got (.+?) (.+?) \*\*(epic berry)\*\*', #English EPIC berry
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English SUPER fish, watermelon
                    r'\?\? \*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese ULTRA log
                    r'!!1 (.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese HYPER log
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese ULTIMATE log, SUPER fish, watermelon
                ]
                item_events = {
                    'epic berry': 'work_epicberry',
                    'hyper log': 'work_hyperlog',
                    'super fish': 'work_superfish',
                    'ultimate log': 'work_ultimatelog',
                    'ultra log': 'work_ultralog',
                    'watermelon': 'work_watermelon',
                }
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find auto flex data in work message.', message)
                    return
                user_name = match.group(1)
                item_amount = int(match.group(2))
                item_name = match.group(4).lower().replace('**','').strip()
                if item_name not in item_events: return
                event = item_events[item_name]
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_WORK,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex work message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'work_ultimatelog':
                    description = (
                        f'**{user_name}** did some really weird timber magic stuff and found **{item_amount:,}** '
                        f'{emojis.LOG_ULTIMATE} **ULTIMATE logs**!\n'
                        f'Not sure this is allowed.'
                    )
                elif event == 'work_ultralog':
                    description = (
                        f'**{user_name}** just cut down **{item_amount:,}** {emojis.LOG_ULTRA} **ULTRA logs** with '
                        f'three chainsaws.\n'
                        f'One of them in their mouth... uh... okay.'
                    )
                elif event == 'work_watermelon':
                    description = (
                        f'**{user_name}** got tired of apples and bananas and stole **{item_amount:,}** '
                        f'{emojis.WATERMELON} **watermelons** instead.\n'
                        f'They should be ashamed (and make cocktails).'
                    )
                elif event == 'work_superfish':
                    description = (
                        f'**{user_name}** went fishing and found **{item_amount:,}** weird purple {emojis.FISH_SUPER} '
                        f'**SUPER fish** in the river.\n'
                        f'Let\'s eat them, imagine wasting those on a VOID armor or something.'
                    )
                elif event == 'work_hyperlog':
                    description = (
                        f'**{user_name}** took a walk in the park when suddenly a tree fell over and split into '
                        f'**{item_amount:,}** {emojis.LOG_HYPER} **HYPER logs**.'
                    )
                elif event == 'work_epicberry':
                    description = (
                        f'**{user_name}** is making fruit salad!\n'
                        f'It will consist of bananas, apples and '
                        f'**{item_amount:,}** {emojis.EPIC_BERRY} **EPIC berries** they just randomly found '
                        f'while gathering the rest.\n'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas loot, non-embed
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
                'epic snowball', #All languages, void present
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #English
                    r'\*\*(.+?)\*\*\ went.+?found (.+?) (.+?) \*\*(\bgodly\b \bpresent\b|\bvoid\b \bpresent\b)\*\*', #English godly and void present, chimney
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #Spanish/Portuguese
                ]
                item_events = {
                    'godly present': 'xmas_godly',
                    'void present': 'xmas_void',
                    'epic snowball': 'xmas_snowball',
                }
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                if user is None:
                    guild_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if len(guild_users) > 1:
                        await functions.add_warning_reaction(message)
                        await message.reply(
                            f'Congratulations, you found something worthy of an auto flex!\n'
                            f'Sadly I am unable to determine who you are as your username is not unique.\n'
                            f'To resolve this, either change your username (not nickname!) or use slash commands next time.'
                        )
                        return
                    if not guild_users: return
                    user = guild_users[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} {emojis.PRESENT_VOID} '
                        f'**VOID present**, duh.'
                    )
                elif event == 'xmas_snowball':
                    description = (
                        f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                        f'I sense a snowman in their not-so-distant future.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas, stuck in chimney
            search_strings = [
                'stuck in the chimney...', #English
                'atascó en la chimenea...', #Spanish
                'atascó en la chimenea...', #Portuguese, MISSING
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\*\ went', #English
                ]
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match: return
                user_name = match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CHIMNEY,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex chimney message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** managed to get themselves stuck in a chimney. Send help!\n'
                    f'After uploading a video of the whole thing on tiktok ofc.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'xmas_chimney', description)

            # Forge godly cookie
            search_strings = [
                'bunch of cookies against the godly sword and then leaves it', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* press', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find use name in auto flex godly cookie message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_FORGE_GODLY_COOKIE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex godly cookie message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'Oh boy, oh boy, someone is going to try to beat the EPIC NPC today!\n'
                    f'Unless **{user_name}** just crafted a {emojis.GODLY_COOKIE} **GODLY cookie** for fun. '
                    f'You never know.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'forge_cookie',
                                                  description)

            # Lootboxes from hunt and adventure
            search_strings = [
                'found a', #English
                'found the', #English
                'encontr', #Spanish, Portuguese
            ]
            search_strings_loot = [
                'omega lootbox',
                'godly lootbox',
                'void lootbox',
                'wolf skin',
                'zombie eye',
                'unicorn horn',
                'mermaid hair',
                'chip',
                'dragon scale',
                'dark energy',
                'epic berry',
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
                and any(search_string in message_content.lower() for search_string in search_strings_loot)
            ):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                hardmode = together = False
                new_format_match = re.search(r'^__\*\*', message_content)
                old_format = False if new_format_match else True
                search_strings_hardmode = [
                    '(but stronger', #English
                    '(pero más fuerte', #Spanish
                    '(só que mais forte', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_hardmode):
                    hardmode = True
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
                partner_name = None
                if together:
                    search_patterns = [
                        r"\*\*(.+?)\*\* and \*\*(.+?)\*\*", #English
                        r"\*\*(.+?)\*\* y \*\*(.+?)\*\*", #Spanish
                        r"\*\*(.+?)\*\* e \*\*(.+?)\*\*", #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        partner_name = user_name_match.group(2)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User names not found in auto flex hunt together message.', message)
                        return
                else:
                    search_patterns_user_name = [
                        r"\*\*(.+?)\*\* found a", #English
                        r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns_user_name, message_content)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user name in auto flex hunt message.', message)
                        return
                    user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT_ADVENTURE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex hunt/adventure message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                # Lootboxes
                lootboxes_user = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootboxes_user_lost = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootboxes_partner = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootboxes_partner_lost = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootbox_user_found = []
                lootbox_user_lost = []
                lootbox_partner_found = []
                lootbox_partner_lost = []
                epic_berry_user_found = []
                epic_berry_partner_found = []
                search_patterns_together_old_user = [
                    fr"{re.escape(user_name)}\*\* got (.+?) (.+?)", #English
                    fr"{re.escape(user_name)}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_together_old_user_lost = [
                    fr"{re.escape(user_name)}\*\* lost (.+?) (.+?)", #English
                ]
                search_patterns_solo = [
                    fr"\*\* got (.+?) (.+?)", #English
                    fr"\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_solo_lost = [
                    fr"\*\* lost (.+?) (.+?)", #English
                ]
                message_content_user = message_content_partner = ''
                search_patterns_user = []
                search_patterns_user_lost = []
                search_patterns_partner = []
                search_patterns_partner_lost = []
                if together and not old_format:
                    partner_loot_start = message_content.find(f'**{partner_name}**:')
                    message_content_user = message_content[:partner_loot_start]
                    message_content_partner = message_content[partner_loot_start:]

                if together:
                    search_patterns_together_new = [
                        fr"\+(.+?) (.+?)", #All languages
                    ]
                    search_patterns_together_new_lost = [
                        fr"\-(.+?) (.+?)", #All languages
                    ]
                    search_patterns_together_old_partner = [
                        fr"{re.escape(partner_name)}\*\* got (.+?) (.+?)", #English
                        fr"{re.escape(partner_name)}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                    ]
                    search_patterns_together_old_partner_lost = [
                        fr"{re.escape(partner_name)}\*\* lost (.+?) (.+?)", #English
                    ]
                    if old_format:
                        search_patterns_user = search_patterns_together_old_user
                        search_patterns_user_lost = search_patterns_together_old_user_lost
                        search_patterns_partner = search_patterns_together_old_partner
                        search_patterns_partner_lost = search_patterns_together_old_partner_lost
                        message_content_user = message_content_partner = message_content
                    else:
                        search_patterns_user = search_patterns_partner = search_patterns_together_new
                        search_patterns_user_lost = search_patterns_together_new_lost
                        partner_loot_start = message_content.find(f'**{partner_name}**:')
                        message_content_user = message_content[:partner_loot_start]
                        message_content_partner = message_content[partner_loot_start:]
                else:
                    search_patterns_user = search_patterns_solo
                    search_patterns_user_lost = search_patterns_solo_lost
                    message_content_user = message_content

                for lootbox in lootboxes_user.keys():
                    for pattern in search_patterns_user:
                        pattern = rf'{pattern} {re.escape(lootbox)}'
                        lootbox_match = re.search(pattern, message_content_user, re.IGNORECASE)
                        if lootbox_match: break
                    if not lootbox_match: continue
                    lootbox_amount = lootbox_match.group(1)
                    lootbox_user_found.append(lootbox)
                    lootbox_user_found.append(lootbox_amount)
                    break
                
                for lootbox in lootboxes_user_lost.keys():
                    for pattern in search_patterns_user_lost:
                        pattern = rf'{pattern} {re.escape(lootbox)}'
                        lootbox_match = re.search(pattern, message_content_user, re.IGNORECASE)
                        if lootbox_match: break
                    if not lootbox_match: continue
                    lootbox_amount = lootbox_match.group(1)
                    lootbox_user_lost.append(lootbox)
                    lootbox_user_lost.append(lootbox_amount)
                    break

                for pattern in search_patterns_user:
                    pattern = rf'{pattern} epic berry'
                    berry_match = re.search(pattern, message_content_user, re.IGNORECASE)
                    if berry_match:
                        drop_amount = int(berry_match.group(1))
                        if (user_settings.current_area == 0
                            or 'pretending' in message_content_user.lower()
                            or 'pretendiendo' in message_content_user.lower()
                            or 'fingindo' in message_content_user.lower()):
                            drop_amount_check = drop_amount / 3
                        else:
                            drop_amount_check = drop_amount
                        if drop_amount_check >= 5:
                            epic_berry_user_found.append('EPIC berry')
                            epic_berry_user_found.append(drop_amount)
                            break

                if together:
                    for lootbox in lootboxes_partner.keys():
                        for pattern in search_patterns_partner:
                            pattern = rf'{pattern} {re.escape(lootbox)}'
                            lootbox_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                            if lootbox_match: break
                        if not lootbox_match: continue
                        lootbox_amount = lootbox_match.group(1)
                        lootbox_partner_found.append(lootbox)
                        lootbox_partner_found.append(lootbox_amount)
                        break
                    
                    for lootbox in lootboxes_partner_lost.keys():
                        for pattern in search_patterns_partner_lost:
                            pattern = rf'{pattern} {re.escape(lootbox)}'
                            lootbox_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                            if lootbox_match: break
                        if not lootbox_match: continue
                        lootbox_amount = lootbox_match.group(1)
                        lootbox_partner_lost.append(lootbox)
                        lootbox_partner_lost.append(lootbox_amount)
                        break

                    for pattern in search_patterns_partner:
                        pattern = rf'{pattern} epic berry'
                        berry_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                        if berry_match:
                            drop_amount = int(berry_match.group(1))
                            if ('pretending' in message_content_partner.lower()
                                or 'pretendiendo' in message_content_partner.lower()
                                or 'fingindo' in message_content_partner.lower()):
                                drop_amount_check = drop_amount / 3
                            else:
                                drop_amount_check = drop_amount
                            if drop_amount_check >= 5:
                                epic_berry_partner_found.append('EPIC berry')
                                epic_berry_partner_found.append(drop_amount)
                                break

                if (not lootbox_user_found and not lootbox_partner_found and not epic_berry_user_found
                    and not epic_berry_partner_found and not lootbox_user_lost and not lootbox_partner_lost):
                    return

                # Lootboxes
                events_user = {
                    'OMEGA lootbox': 'lb_omega',
                    'GODLY lootbox': 'lb_godly',
                    'VOID lootbox': 'lb_void',
                }
                events_partner = {
                    'OMEGA lootbox': 'lb_omega_partner',
                    'GODLY lootbox': 'lb_godly_partner',
                    'VOID lootbox': 'lb_void_partner',
                }
                description = event = ''
                if lootbox_user_found:
                    name, amount = lootbox_user_found
                    event = events_user[name]
                    if event == 'lb_void':
                        description = (
                            f'Everbody rejoice because **{user_name}** did something almost impossible and found '
                            f'**{amount}** {lootboxes_user[name]} **{name}**!\n'
                            f'We are all so happy for you and not at all jealous.'
                        )
                    elif event == 'lb_omega':
                        if not hardmode:
                            event = 'lb_omega_no_hardmode'
                            description = (
                                f'**{user_name}** found an {lootboxes_user[name]} **{name}** just like that.\n'
                                f'And by "just like that" I mean **without hardmoding**!\n'
                                f'See, hardmoders, that\'s how it\'s done!'
                            )
                        elif int(amount) > 2:
                            event = 'lb_omega_multiple'
                            description = (
                                f'While an {lootboxes_user[name]} **{name}** isn\'t very exciting, '
                                f'**{user_name}** just found __**{amount}**__ of them at once!\n'
                                f'(Well, actually, the horse did all the work)'
                            )
                        else:
                            event = ''
                    else:
                        description = (
                            f'**{user_name}** just found **{amount}** {lootboxes_user[name]} **{name}**!\n'
                            f'~~They should be banned!~~ We are so happy for you!'
                        )
                if lootbox_user_lost:
                    name, amount = lootbox_user_lost
                    event = 'lb_a18'
                    description = (
                        f'**{user_name}** just lost **{amount}** {lootboxes_user_lost[name]} **{name}**!\n'
                        f'Damn, they really suck at this game.'
                    )
                if lootbox_partner_found and event == '':
                    name, amount = lootbox_partner_found
                    if lootbox_user_found:
                        description = (
                            f'{description}\n\n'
                            f'Ah yes, also... as if that wasn\'t OP enough, they also found their partner '
                            f'**{partner_name}** **{amount}** {lootboxes_partner[name]} **{name}** ON TOP OF THAT!\n'
                            f'I am really not sure why this much luck is even allowed.'
                        )
                    else:
                        event = events_partner[name]
                        if event == 'lb_godly_partner':
                            description = (
                                f'If you ever wanted to see what true love looks like, here\'s an example:\n'
                                f'**{user_name}** just got their partner **{partner_name}** **{amount}** '
                                f'{lootboxes_partner[name]} **{name}**!\n'
                                f'We\'re all jealous.'
                            )
                        elif event == 'lb_void_partner':
                            description = (
                                f'I am speechless because what we are seeing here is one of the rarest things ever.\n'
                                f'**{user_name}** just found their partner **{partner_name}**... **{amount}** '
                                f'{lootboxes_partner[name]} **{name}**.\n'
                                f'Yes, you read that right.'
                            )
                        else:
                            description = (
                                f'**{user_name}** ordered **{amount}** {lootboxes_partner[name]} **{name}** and it '
                                f'just got delivered.\n'
                                f'...to **{partner_name}**\'s address lol.'
                            )
                if lootbox_partner_lost:
                    name, amount = lootbox_partner_lost
                    event = 'lb_a18_partner'
                    description = (
                        f'**{user_name}** turns out to be the worst partner you can image.\n'
                        f'They just made **{partner_name}** lose  **{amount}** {lootboxes_user_lost[name]} **{name}**!\n'
                        f'You should be ashamed, really.'
                    )
                if description != '':
                    await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

                # EPIC berries
                description = ''
                if epic_berry_user_found:
                    name, amount = epic_berry_user_found
                    event = 'epic_berry'
                    description = (
                        f'**{user_name}** found **{amount}** {emojis.EPIC_BERRY} **EPIC berries**!\n'
                        f'I can see a drooling horse approaching in the distance. Better get out of the way.'
                    )

                if epic_berry_partner_found:
                    name, amount = epic_berry_partner_found
                    if description != '':
                        event = 'epic_berry'
                        description = (
                            f'{description}\n\n'
                            f'Because **{user_name}** is such a nice person and likes to share, '
                            f'their partner **{partner_name}** also got **{amount}**!\n'
                            f'What a lovely marriage.'
                        )
                    else:
                        event = 'epic_berry_partner'
                        description = (
                            f'What do you get when you marry? Love? Happiness? Gifts?\n'
                            f'Your **{amount}** {emojis.EPIC_BERRY} **EPIC berries** stolen, that\'s what.\n'
                            f'If you don\'t believe me, look at what **{partner_name}** just did to **{user_name}**!'
                        )
                if description != '':
                    await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)


            # Lootbox event
            search_strings = [
                'your lootbox has evolved', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* uses', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex lootbox event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_OPEN,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex lootbox event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** used a magic spell on a lootbox for some reason which then evolved into an '
                    f'{emojis.LB_OMEGA} **OMEGA lootbox**! For some reason.\n'
                    f'I wonder what the Ministry of Magic would say to this.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_lb', description)

            # Enchant event
            search_strings = [
                'your sword got an ultra-edgy enchantment', #English sword
                'your armor got an ultra-edgy enchantment', #English armor
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* tries', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex enchant event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ENCHANT,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex enchant event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** failed to enchant stuff properly and enchanted the same thing twice.\n'
                    f'Somehow that actually worked tho and got them an **ULTRA-EDGY enchant**? {emojis.ANIME_SUS}'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_enchant',
                                                  description)

            # Farm event
            search_strings = [
                'the seed surrendered', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* hits', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex farm event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_FARM,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex farm event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** fought a seed (why) by hitting the floor with their fists (what) '
                    f'and **leveled up 20 times** (??).\n'
                    f'Yeah, that totally makes sense.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_farm',
                                                  description)

            # Heal event
            search_strings = [
                'killed the mysterious man', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* killed', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex heal event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HEAL,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex heal event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** encountered a poor and lonely **mysterious man** and... killed him.\n'
                    f'Enjoy your **level up**, I guess. Hope you feel bad.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_heal',
                                                  description)

            # Training event
            search_strings = [
                'wings spawned', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r"in \*\*(.+?)\*\*'s back", #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex training event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex training event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                search_patterns = [
                    r'became \*\*(\d+?) ', #English
                ]
                amount_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not amount_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find dark energy amount in auto flex training event message.', message)
                    return
                amount = amount_match.group(1)
                description = (
                    f'**{user.name}** was tired of an earthly existence and tried to fly away.\n'
                    f'_Somehow_ they not only spawned wings and didn\'t crash miserably, they also found '
                    f'**{amount}** {emojis.DARK_ENERGY} **dark energy** while doing that.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_training',
                                                  description)

            # Time capsule
            search_strings = [
                "a portal was opened", #English
                "se abrió un portal", #Spanish
                "um portal foi aberto", #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\* breaks', message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TIME_CAPSULE,
                                                    user_name=user_name)
                        )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex time capsule message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.auto_flex_enabled
                    or user_settings.time_travel_count is None): return
                time_travel_count_new = user_settings.time_travel_count + 1
                await user_settings.update(time_travel_count=time_travel_count_new)
                if time_travel_count_new == 1:
                    event = 'time_travel_1'
                    description = (
                        f'**{user.name}** just reached their very **first** {emojis.TIME_TRAVEL} **time travel**!\n'
                        f'Congratulations, we are expecting great things of you!'
                    )
                elif time_travel_count_new == 3:
                    event = 'time_travel_3'
                    description = (
                        f'**{user.name}** did it again (and again) and just reached {emojis.TIME_TRAVEL} **TT 3**!\n'
                        f'I think they\'re getting addicted.'
                    )
                elif time_travel_count_new == 5:
                    event = 'time_travel_5'
                    description = (
                        f'**{user.name}** is busy moving on in the world and just reached {emojis.TIME_TRAVEL} **TT 5**!\n'
                        f'The boss in D13 can\'t wait to see you.'
                    )
                elif time_travel_count_new == 10:
                    event = 'time_travel_10'
                    description = (
                        f'**{user.name}** is getting serious. {emojis.TIME_TRAVEL} **TT 10** achieved!\n'
                        f'Hope you\'re not colorblind. Also I hope you don\'t expect to survive in A15.'
                    )
                elif time_travel_count_new == 25:
                    event = 'time_travel_25'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 25**!\n'
                        f'Good news: Welcome to the endgame!\n'
                        f'Bad news: Hope you like dragon scale farming.'
                    )
                elif time_travel_count_new == 50:
                    event = 'time_travel_50'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 50**!\n'
                        f'Sadly they went blind after seeing the profile background they got as a reward.'
                    )
                elif time_travel_count_new == 100:
                    event = 'time_travel_100'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 100**!\n'
                        f'Damn, you must really like this game. I just hope you still remember your family.\n'
                        f'Nothing more I can teach you anyway. Wdym I never taught you anything? Ungrateful brat.'
                    )
                elif time_travel_count_new == 150:
                    event = 'time_travel_150'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 150**!\n'
                        f'I\'m starting to question your life choices.\n'
                        f'You can stop playing now btw, there will be no more backgrounds.\n'
                    )
                elif time_travel_count_new == 200:
                    event = 'time_travel_200'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **TT 200**!\n'
                        f'What on earth made you do this 200 times? You mad?\n'
                    )
                elif time_travel_count_new == 300:
                    event = 'time_travel_300'
                    description = (
                        f'**{user.name}** reached {emojis.TIME_TRAVEL} **SPARTA**!\n'
                    )
                elif time_travel_count_new == 400:
                    event = 'time_travel_400'
                    description = (
                        f'Public Service Alert! **{user.name}** traveled in time **400** times {emojis.TIME_TRAVEL}!\n'
                        f'As to why tho... I couldn\'t say.'
                    )
                elif time_travel_count_new == 420:
                    event = 'time_travel_420'
                    description = (
                        f'**4:20 {user.name}**. The usual place.'
                    )
                elif time_travel_count_new == 500:
                    event = 'time_travel_500'
                    description = (
                        f'Did you see that? It\'s **{user.name}** plopping through time. For the freaking **500**th time.\n'
                        f'{emojis.TIME_TRAVEL}\n'
                    )
                elif time_travel_count_new == 600:
                    event = 'time_travel_600'
                    description = (
                        f'Pretty sury **{user.name}** forgot by now which time they actually belong to after '
                        f'**600** {emojis.TIME_TRAVEL} time travels.\n'
                    )
                elif time_travel_count_new == 700:
                    event = 'time_travel_700'
                    description = (
                        f'Did you know that there is such a thing as playing a game too much? **{user.name}** can.\n'
                        f'They just reached **700** {emojis.TIME_TRAVEL} time travels, and it scares me.\n'
                    )
                elif time_travel_count_new == 800:
                    event = 'time_travel_800'
                    description = (
                        f'**800** {emojis.TIME_TRAVEL} time travels. It\'s rather crazy. But I get it now - '
                        f'**{user.name}** is probably training for the time olympics on Galifrey.'
                    )
                elif time_travel_count_new == 900:
                    event = 'time_travel_900'
                    description = (
                        f'Ted just called **{user.name}** and wanted his phone booth back. After learning it was '
                        f'used for **900** {emojis.TIME_TRAVEL} time travels, he was too scared to take it back tho.'
                    )
                elif time_travel_count_new == 999:
                    event = 'time_travel_999'
                    description = (
                        f'**{user.name}** traveled in time for **999** times and thus broke Epic RPG Guide. Good job.\n'
                        f'Hope you\'re proud. Damn it.'
                    )
                else:
                    return
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Rare halloween loot
            search_strings = [
                'sleepy potion', #English potion
                'suspicious broom', #English broom
            ]
            search_strings_scare = [
                '** scared **', #English potion
                'got so much scared', #English broom
                'got so hella scared', #English broom
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and any(search_string in message_content.lower() for search_string in search_strings_scare)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r" \*\*(.+?)\*\* scared", #English
                    r"scared by \*\*(.+?)\*\*", #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex hal boo message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HAL_BOO,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex hal boo message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if 'sleepy potion' in message_content.lower():
                    emoji = emojis.SLEEPY_POTION
                    item_name = 'sleepy potion'
                else:
                    emoji = emojis.SUSPICIOUS_BROOM
                    item_name = 'suspicious broom'
                description = (
                    f'**{user.name}** scared a friend to death and got a {emoji} **{item_name}** as a reward for that.\n'
                    f'So we\'re getting rewarded for being a bad friend now? Hope you feel bad, okay?'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'hal_boo',
                                                  description)

            # Brew electronical potion
            search_strings = [
                '**electronical potion**, you\'ve received the following boosts', #English
                '**electronical potion**, you\'ve received the following boosts', #Spanish, MISSING
                '**electronical potion**, you\'ve received the following boosts', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ALCHEMY)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the dragon breath potion auto flex.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** is thirsty, but unlike, you know, _normal_ people, it has to be the rather exclusive '
                    f'{emojis.POTION_ELECTRONICAL} **Electronical potion** for them.\n'
                    f'The snob.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'brew_electronical',
                                                  description)

# Initialization
def setup(bot):
    bot.add_cog(AutoFlexCog(bot))