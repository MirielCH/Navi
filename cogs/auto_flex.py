# auto_flex.py

import re

import discord
from discord.ext import commands

from database import errors, guilds, users
from resources import emojis, exceptions, functions, regex, settings, strings


FLEX_TITLES = {
    'work_ultimatelog': f'{emojis.LOG_ULTIMATE} Wood you log at that!',
    'work_ultralog': f'{emojis.LOG_ULTRA} It\'s not a dream!',
    'work_superfish': f'{emojis.FISH_SUPER} How much is the fish?',
    'work_watermelon': f'{emojis.WATERMELON} One in a melon',
    'forge_cookie': f'{emojis.GODLY_COOKIE} Caution! Hot cookie!',
    'lb_omega_partner': f'{emojis.LB_OMEGA} Oops, wrong recipient, lol',
    'lb_godly': f'{emojis.LB_GODLY} Oh hello, what a nice lootbox',
    'lb_godly_partner': f'{emojis.LB_GODLY} Best gift ever',
    'lb_void': f'{emojis.LB_VOID} Now this is just hacking',
    'lb_void_partner': f'{emojis.LB_VOID} I don\'t even know what to say',
    'lb_edgy_ultra': f'{emojis.LOG_ULTRA} "It\'s only an EDGY lootbox... oh wait what"',
    'lb_godly_tt': f'{emojis.TIME_TRAVEL} There\'s luck, and then there\'s this',
    'pr_ascension': f'{emojis.ASCENSION} Up up and away',
    'event_boss': f'{emojis.MOB_ANCIENT_DRAGON} LEGEN... WAIT FOR IT...',
    'event_lb': f'{emojis.LB_OMEGA} They did what now?',
    'event_enchant': f'{emojis.BOOM} Twice the fun',
    'event_farm': f'{emojis.CROSSED_SWORDS} Totally believable level up story',
    'event_heal': f'{emojis.LIFE_POTION} Very mysterious',
    'cookies': f'{emojis.ARENA_COOKIE} Someone got a bit hungry',
}

FLEX_THUMBNAILS = {
    'work_ultimatelog': 'https://media.tenor.com/4kc5AXWNVvQAAAAC/barney-rubble-chopping-wood.gif',
    'work_ultralog': 'https://c.tenor.com/4ReodhBihBQAAAAC/ruthe-biber.gif',
    'work_superfish': 'https://media.tenor.com/B6dwDGql374AAAAC/mcdonald-chris-mcdonald.gif',
    'work_watermelon': 'https://media.tenor.com/mAxfGDKXrZUAAAAC/bunnies-cute.gif',
    'forge_cookie': 'https://c.tenor.com/CqkklVxeZckAAAAC/cookie-monster.gif',
    'lb_omega_partner': 'https://c.tenor.com/l0wNXZN58S8AAAAC/delivery-kick.gif',
    'lb_godly': 'https://c.tenor.com/zBe7Ew1lzPYAAAAi/tkthao219-bubududu.gif',
    'lb_godly_partner': 'https://media.tenor.com/NvP2dNkQWtEAAAAC/i-got-us-a-box-anthony-mennella.gif',
    'lb_void': 'https://media.tenor.com/f8-9UL5OveIAAAAi/box-cute.gif',
    'lb_void_partner': 'https://media.tenor.com/kumodwVv1bcAAAAC/patrick-the-maniacs-in-mail-box.gif',
    'lb_edgy_ultra': 'https://c.tenor.com/clnoM8TeSxcAAAAC/wait-what-unbelievable.gif',
    'lb_godly_tt': 'https://c.tenor.com/-BVQhBulOmAAAAAC/bruce-almighty-morgan-freeman.gif',
    'pr_ascension': 'https://c.tenor.com/Jpx1xCUOyz8AAAAC/ascend.gif',
    'event_boss': 'https://c.tenor.com/dAMi0gNJQeIAAAAC/peach-cat.gif',
    'event_lb': 'https://c.tenor.com/6WfJrQYFXlYAAAAC/magic-kazaam.gif',
    'event_enchant': 'https://c.tenor.com/gAuPzxRCVw8AAAAC/link-dancing.gif',
    'event_farm': 'https://c.tenor.com/OEIwT0KEyREAAAAC/homer-fist.gif',
    'event_heal': 'https://c.tenor.com/IfAs08au8IYAAAAd/he-died-in-mysterious-circumstances-the-history-guy.gif',
    'cookies': 'https://c.tenor.com/mbs-siKKowoAAAAd/cookie-monster-cookie-for-you.gif',
}


class AutoFlexCog(commands.Cog):
    """Cog that contains the auto flex detection"""
    def __init__(self, bot):
        self.bot = bot

    async def send_auto_flex_message(self, message: discord.Message, guild_settings: guilds.Guild, event: str,
                                     description: str) -> None:
        """Sends a flex embed to the auto flex channel"""
        description = f'{description}\n\n[Check it out]({message.jump_url})'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = FLEX_TITLES[event],
            description = description,
        )
        embed.set_thumbnail(url=FLEX_THUMBNAILS[event])
        auto_flex_channel = await functions.get_discord_channel(self.bot, guild_settings.auto_flex_channel_id)
        if auto_flex_channel is None:
            await functions.add_warning_reaction(message)
            await errors.log_error('Couldn\'t find auto flex channel.', message)
            return
        await auto_flex_channel.send(embed=embed)

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

            # Loot in work commands
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
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
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
                        f'{emojis.LOG_ULTIMATE} ULTIMATE logs!\n'
                        f'Not sure this is allowed.'
                    )
                elif event == 'work_ultralog':
                    description = (
                        f'**{user_name}** just cut down {item_amount:,} {emojis.LOG_ULTRA} ULTRA logs with three chainsaws.\n'
                        f'One of them in their mouth.\n'
                        f'Look, let\'s all just back away slowly, okay...'
                    )
                elif event == 'work_watermelon':
                    description = (
                        f'**{user_name}** got tired of apples and bananas and stole {item_amount:,} {emojis.WATERMELON} '
                        f'watermelons instead.\n'
                        f'They should be ashamed. And also make cocktails for everyone.'
                    )
                elif event == 'work_superfish':
                    description = (
                        f'**{user_name}** went fishing and found {item_amount:,} weird purple {emojis.FISH_SUPER} '
                        f'SUPER fish in the river.\n'
                        f'Let\'s eat them, imagine wasting those on a VOID armor or something.'
                    )
                await self.send_auto_flex_message(message, guild_settings, event, description)

            # Forge godly cookie
            search_strings = [
                'bunch of cookies against the godly sword and then leaves it', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* press', #English
                ]
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find auto flex data in godly cookie message.', message)
                    return
                user_name = match.group(1)
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
                    f'Unless **{user_name}** just crafted a {emojis.GODLY_COOKIE} GODLY cookie for fun. You never know.'
                )
                await self.send_auto_flex_message(message, guild_settings, 'forge_cookie', description)

            # Lootboxes
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
                and any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                and any(search_string in message_content.lower() for search_string in search_strings_lootboxes)):
                user = await functions.get_interaction_user(message)
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                together = False
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
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
                    'GODLY present': emojis.PRESENT_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                lootboxes_partner = {
                    'OMEGA present': emojis.PRESENT_OMEGA,
                    'GODLY present': emojis.PRESENT_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                }
                search_patterns_user = [
                    fr'\*\*{re.escape(user_name)}\*\* got (\w+?) ', #English
                    fr'\*\*{re.escape(user_name)}\*\* consiguió ', #Spanish
                    fr'\*\*{re.escape(user_name)}\*\* conseguiu ', #Portuguese
                ]
                search_patterns_partner = [
                    fr'\*\*{re.escape(user_settings.partner_name)}\*\* got ', #English
                    fr'\*\*{re.escape(user_settings.partner_name)}\*\* consiguió ', #Spanish
                    fr'\*\*{re.escape(user_settings.partner_name)}\*\* conseguiu ', #Portuguese
                ]


                description = (
                    f'Oh boy, oh boy, someone is going to try to beat the EPIC NPC today!\n'
                    f'Unless **{user_name}** just crafted a {emojis.GODLY_COOKIE} GODLY cookie for fun. You never know.'
                )
                await self.send_auto_flex_message(message, guild_settings, 'forge_cookie', description)


# Initialization
def setup(bot):
    bot.add_cog(AutoFlexCog(bot))