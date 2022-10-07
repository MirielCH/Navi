# auto_flex.py

import re

import discord
from discord.ext import commands

from database import errors, guilds, users
from resources import emojis, exceptions, functions, regex, settings, strings


FLEX_TITLES = {
    'work_ultimatelog': 'Wood you log at that!',
    'work_ultralog': 'It\'s not a dream!',
    'work_superfish': 'How much is the fish?',
    'work_watermelon': 'One in a melon',
    'forge_cookie': 'Caution! Hot cookie!',
    'lb_omega': 'Ooooh, shiny!',
    'lb_omega_partner': 'Oops, wrong recipient, lol',
    'lb_godly': 'Oh hello, what a nice lootbox',
    'lb_godly_partner': 'Best gift ever',
    'lb_void': 'Now this is just hacking',
    'lb_void_partner': 'I don\'t even know what to say',
    'lb_edgy_ultra': 'What could an EDGY lootbox ever be worth',
    'lb_godly_tt': 'There\'s luck, and then there\'s this',
    'pets_catch_epic': 'EPIC pet incoming',
    'pets_catch_tt': 'K9, is that you?',
    'pr_ascension': 'Up up and away',
    'event_lb': 'They did what now?',
    'event_enchant': 'Twice the fun',
    'event_farm': 'Totally believable level up story',
    'event_heal': 'Very mysterious',
}

FLEX_THUMBNAILS = {
    'work_ultimatelog': 'https://media.tenor.com/4kc5AXWNVvQAAAAC/barney-rubble-chopping-wood.gif',
    'work_ultralog': 'https://c.tenor.com/4ReodhBihBQAAAAC/ruthe-biber.gif',
    'work_superfish': 'https://media.tenor.com/B6dwDGql374AAAAC/mcdonald-chris-mcdonald.gif',
    'work_watermelon': 'https://media.tenor.com/mAxfGDKXrZUAAAAC/bunnies-cute.gif',
    'forge_cookie': 'https://media.tenor.com/YP5Xv8Sa45IAAAAC/cookie-monster-awkward.gif',
    'lb_omega': 'https://c.tenor.com/8yMrP1Cs7ykAAAAC/ninjala-ninjala-season6trailer.gif',
    'lb_omega_partner': 'https://c.tenor.com/l0wNXZN58S8AAAAC/delivery-kick.gif',
    'lb_godly': 'https://c.tenor.com/zBe7Ew1lzPYAAAAi/tkthao219-bubududu.gif',
    'lb_godly_partner': 'https://media.tenor.com/NvP2dNkQWtEAAAAC/i-got-us-a-box-anthony-mennella.gif',
    'lb_void': 'https://media.tenor.com/f8-9UL5OveIAAAAi/box-cute.gif',
    'lb_void_partner': 'https://media.tenor.com/kumodwVv1bcAAAAC/patrick-the-maniacs-in-mail-box.gif',
    'lb_edgy_ultra': 'https://c.tenor.com/clnoM8TeSxcAAAAC/wait-what-unbelievable.gif',
    'lb_godly_tt': 'https://c.tenor.com/-BVQhBulOmAAAAAC/bruce-almighty-morgan-freeman.gif',
    'pets_catch_epic': 'https://media.tenor.com/WnprYvrvNp8AAAAC/cat-kitty.gif',
    'pets_catch_tt': 'https://media.tenor.com/7LMaSfhq9TIAAAAC/flying-omw.gif',
    'pr_ascension': 'https://media.tenor.com/wfma4CqwxCwAAAAC/railgun-misaka-mikoto.gif',
    'event_lb': 'https://media.tenor.com/wn2_Qq6flogAAAAC/magical-magic.gif',
    'event_enchant': 'https://c.tenor.com/gAuPzxRCVw8AAAAC/link-dancing.gif',
    'event_farm': 'https://media.tenor.com/z1ru-IqnJFoAAAAC/earthquake-four-arms.gif',
    'event_heal': 'https://media.tenor.com/lh60y7i9SeQAAAAC/peachmad-peachandgoma.gif',
}


class AutoFlexCog(commands.Cog):
    """Cog that contains the auto flex detection"""
    def __init__(self, bot):
        self.bot = bot

    async def send_auto_flex_message(self, message: discord.Message, guild_settings: guilds.Guild,
                                     user_settings: users.User, user: discord.User, event: str,
                                     description: str) -> None:
        """Sends a flex embed to the auto flex channel"""
        description = f'{description}\n\n[Check it out]({message.jump_url})'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = FLEX_TITLES[event],
            description = description,
        )
        embed.set_author(icon_url=user.display_avatar.url, name=f'{user.name} got lucky!')
        embed.set_thumbnail(url=FLEX_THUMBNAILS[event])
        embed.set_footer(text='Use \'/settings user\' to enable or disable auto flex.')
        auto_flex_channel = await functions.get_discord_channel(self.bot, guild_settings.auto_flex_channel_id)
        if auto_flex_channel is None:
            await functions.add_warning_reaction(message)
            await errors.log_error('Couldn\'t find auto flex channel.', message)
            return
        await auto_flex_channel.send(embed=embed)
        if user_settings.reactions_enabled and not message.reactions: await message.add_reaction(emojis.NAVI)

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
            embed_description = embed_title = embed_field0_name = embed_field0_value = embed_autor = icon_url = ''
            if embed.description: embed_description = embed.description
            if embed.title: embed_title = embed.title
            if embed.fields:
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
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
                elif 'godly lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_godly_tt'
                else:
                    return
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = await message.guild.fetch_member(user_id)
                    else:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await functions.get_message_from_channel_history(
                                    message.channel, regex.COMMAND_OPEN,
                                    user_name=user_name
                                )
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
                        await errors.log_error('ULTRA log amount not found in auto flex lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Look at **{user.name}**, opening that {emojis.LB_EDGY} EDGY lootbox like it\'s worth '
                        f'anything, haha.\n'
                        f'See, all they got is {amount} lousy {emojis.LOG_ULTRA} ULTRA log!\n'
                        f'_**Wait...**_'
                    )
                elif event == 'lb_godly_tt':
                    match = re.search(r'\+(.+?) (.+?) time capsule', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time capsule amount not found in auto flex lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'So.\n**{user.name}** opened a {emojis.LB_GODLY} GODLY lootbox. I mean that\'s cool.\n'
                        f'__BUT__. For some reason they found {amount} {emojis.TIME_CAPSULE} **time capsule** in there.\n'
                        f'This hasn\'t happened often yet, so expect to get blacklisted from the game.\n'
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
                            await functions.get_message_from_channel_history(
                                message.channel, regex.COMMAND_PROFESSIONS_ASCEND,
                                user_name=user_name
                            )
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
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'pr_ascend', description)

            # Pets catch
            search_strings = [
                "**dog** is now following", #English, dog
                "**cat** is now following", #English, cat
                "**dragon** is now following", #English, dragon
            ]
            if any(search_string in embed_field0_value.lower() for search_string in search_strings
                and ('epic**' in embed_field0_value.lower() or 'time traveler**' in embed_field0_value.lower())):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r'\*\*(\w+?)\*\* is now following \*\*(\w+?)\*\*', #English
                    ]
                    pet_data_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                    if pet_data_match:
                        pet_type = pet_data_match.group(1)
                        user_name = pet_data_match.group(2)
                        user_command_message = (
                            await functions.get_message_from_channel_history(
                                message.channel, regex.COMMAND_TRAINING,
                                user_name=user_name
                            )
                        )
                    if not pet_data_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Pet type or user name not found in auto flex pets catch message.', message)
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
                        f'**{user.name}** took a stroll when a {pet_type.lower()} popped out of nothingness.\n'
                        f'Turns out it\'s a {emojis.SKILL_TIME_TRAVELER} **time traveler** {pet_type.lower()}!\n'
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



        if not message.embeds:
            message_content = message.content

            # Loot from work commands
            search_strings = [
                'this may be the luckiest moment of your life', #English, ultimate logs
                'is this a **dream**????', #English, ultra logs
                'oooooofff!!', #English, super fish
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                or ('nice!' in message_content.lower() and 'watermelon' in message_content.lower())):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)\*\*', #English
                    r'\*\*(\w+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)\*\*', #Spanish, Portuguese
                ]
                item_events = {
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
                item_name = match.group(4)
                event = item_events[item_name.lower()]
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_WORK,
                            user_name=user_name
                        )
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
                        f'**{user_name}** did some really weird timber magic stuff and found {item_amount:,} '
                        f'{emojis.LOG_ULTIMATE} **ULTIMATE logs**!\n'
                        f'Not sure this is allowed.'
                    )
                elif event == 'work_ultralog':
                    description = (
                        f'**{user_name}** just cut down {item_amount:,} {emojis.LOG_ULTRA} **ULTRA logs** with '
                        f'three chainsaws.\n'
                        f'One of them in their mouth.\n'
                        f'Look, let\'s all just back away slowly, okay...'
                    )
                elif event == 'work_watermelon':
                    description = (
                        f'**{user_name}** got tired of apples and bananas and stole {item_amount:,} {emojis.WATERMELON} '
                        f'**watermelons** instead.\n'
                        f'They should be ashamed. And also make cocktails for everyone.'
                    )
                elif event == 'work_superfish':
                    description = (
                        f'**{user_name}** went fishing and found {item_amount:,} weird purple {emojis.FISH_SUPER} '
                        f'**SUPER fish** in the river.\n'
                        f'Let\'s eat them, imagine wasting those on a VOID armor or something.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Forge godly cookie
            search_strings = [
                'bunch of cookies against the godly sword and then leaves it', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* press', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find use name in auto flex godly cookie message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_FORGE_GODLY_COOKIE,
                            user_name=user_name
                        )
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
                    f'Unless **{user_name}** just crafted a {emojis.GODLY_COOKIE} **GODLY cookie** for fun. You never know.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'forge_cookie', description)

            # Lootboxes from hunt and adventure
            search_strings = [
                'found a', #English
                'encontr', #Spanish, Portuguese
            ]
            search_strings_lootboxes = [
                'omega lootbox',
                'godly lootbox',
                'void lootbox',
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
                and any(search_string in message_content.lower() for search_string in search_strings_lootboxes)
            ):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                together = False
                old_format = True if '__**' not in message_content.lower() else False
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
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_HUNT,
                            user_name=user_name
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex hunt message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                lootboxes_user = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootboxes_partner = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootbox_user_found = []
                lootbox_partner_found = []
                search_patterns_together_new = [
                    fr"\+(.+?) (.+?)", #All languages
                ]
                search_patterns_together_old_user = [
                    fr"{user_name}\*\* got (.+?) (.+?)", #English
                    fr"{user_name}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_together_old_partner = [
                    fr"{partner_name}\*\* got (.+?) (.+?)", #English
                    fr"{partner_name}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_solo = [
                    fr"\*\* got (.+?) (.+?)", #English
                    fr"\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                message_content_user = message_content_partner = ''
                search_patterns_user = []
                search_patterns_partner = []
                if together and not old_format:
                    partner_loot_start = message_content.find(f'**{partner_name}**:')
                    message_content_user = message_content[:partner_loot_start]
                    message_content_partner = message_content[partner_loot_start:]

                if together:
                    if old_format:
                        search_patterns_user = search_patterns_together_old_user
                        search_patterns_partner = search_patterns_together_old_partner
                        message_content_user = message_content_partner = message_content
                    else:
                        search_patterns_user = search_patterns_partner = search_patterns_together_new
                        partner_loot_start = message_content.find(f'**{partner_name}**:')
                        message_content_user = message_content[:partner_loot_start]
                        message_content_partner = message_content[partner_loot_start:]
                else:
                    search_patterns_user = search_patterns_solo
                    message_content_user = message_content

                for lootbox in lootboxes_user.keys():
                    for pattern in search_patterns_user:
                        pattern = rf'{pattern} {re.escape(lootbox)}'
                        lootbox_match = re.search(pattern, message_content_user)
                        if lootbox_match: break
                    if not lootbox_match: continue
                    lootbox_amount = lootbox_match.group(1)
                    lootbox_user_found.append(lootbox)
                    lootbox_user_found.append(lootbox_amount)
                    break

                if together:
                    for lootbox in lootboxes_partner.keys():
                        for pattern in search_patterns_partner:
                            pattern = rf'{pattern} {re.escape(lootbox)}'
                            lootbox_match = re.search(pattern, message_content_partner)
                            if lootbox_match: break
                        if not lootbox_match: continue
                        lootbox_amount = lootbox_match.group(1)
                        lootbox_partner_found.append(lootbox)
                        lootbox_partner_found.append(lootbox_amount)
                        break

                if not lootbox_user_found and not lootbox_partner_found: return

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
                description = ''
                if lootbox_user_found:
                    name, amount = lootbox_user_found
                    event = events_user[name]
                    if event == 'lb_void':
                        description = (
                            f'Everbody rejoice because **{user_name}** did something almost impossible and found '
                            f'{amount} {lootboxes_user[name]} **{name}**!\n'
                            f'We are all so happy for you and not at all jealous!'
                        )
                    else:
                        description = (
                            f'**{user_name}** just found {amount} {lootboxes_user[name]} **{name}**!\n'
                            f'Imagine being this lucky.'
                        )

                if lootbox_partner_found:
                    name, amount = lootbox_partner_found
                    if lootbox_user_found:
                        description = (
                            f'{description}\n\n'
                            f'Ah yes, also... as if that wasn\'t OP enough, they also found their partner '
                            f'**{partner_name}** {amount} {lootboxes_partner[name]} **{name}** ON TOP OF THAT??!!\n'
                            f'I am really not sure why this much luck is even allowed.'
                        )
                    else:
                        event = events_partner[name]
                        if event == 'lb_godly_partner':
                            description = (
                                f'If you ever wanted to see what true love looks like, here\'s an example:\n'
                                f'**{user_name}** just got their partner **{partner_name}** {amount} '
                                f'{lootboxes_partner[name]} **{name}**!\n'
                                f'We\'re all jealous.'
                            )
                        elif event == 'lb_void_partner':
                            description = (
                                f'I am speechless because what we are seeing here is one of the rarest things ever.\n'
                                f'**{user_name}** just found their partner **{partner_name}**... {amount} '
                                f'{lootboxes_partner[name]} **{name}**.\n'
                                f'Yes, you read that right.'
                            )
                        else:
                            description = (
                                f'**{user_name}** ordered {amount} {lootboxes_partner[name]} **{name}** and it just got '
                                f'delivered.\n'
                                f'...to **{partner_name}**\'s address lol.'
                            )
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
                    r'\*\*(\w+?)\*\* uses', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex lootbox event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_OPEN,
                            user_name=user_name
                        )
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
                    f'{emojis.LB_OMEGA} **OMEGA lootbox**!\n'
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
                    r'\*\*(\w+?)\*\* tries', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex enchant event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_ENCHANT,
                            user_name=user_name
                        )
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
                    f'**{user.name}** failed to enchant stuff properly, they enchanted the same thing twice.\n'
                    f'Somehow that actually worked tho and got them an **ULTRA-EDGY enchant**? {emojis.ANIME_SUS}'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_enchant', description)

            # Farm event
            search_strings = [
                'the seed surrendered', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* hits', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex farm event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_FARM,
                            user_name=user_name
                        )
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
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_farm', description)

            # Heal event
            search_strings = [
                'killed the mysterious man', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* killed', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex heal event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, regex.COMMAND_HEAL,
                            user_name=user_name
                        )
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
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_heal', description)


# Initialization
def setup(bot):
    bot.add_cog(AutoFlexCog(bot))