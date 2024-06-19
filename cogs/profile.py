# profile.py

from math import floor
import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, guilds, users
from resources import exceptions, functions, regex, settings


class ProfileCog(commands.Cog):
    """Cog that contains the adventure detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
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
            embed_author = embed_field0_value = embed_footer = icon_url = ''
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.fields:
                embed_field0_value = str(embed.fields[0].value)
            if embed.footer:
                embed_footer = embed.footer.text

            # Update settings from profile
            search_strings = [
                "— profile", #All languages
                "— progress", #All languages
            ]
            if (any(search_string in embed_author.lower() for search_string in search_strings)
                and not 'epic npc' in embed_author.lower()):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
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
                if not user_settings.bot_enabled: return

                kwargs = {}
                
                # Update time travel count
                if len(embed_field0_value.split('\n')) < 4:
                    time_travel_count = 0
                else:
                    search_patterns = [
                        r'time travels\*\*: (.+?)(?:$|\n)', #English
                        r'el tiempo\*\*: (.+?)(?:$|\n)', #Spanish
                        r'no tempo\*\*: (.+?)(?:$|\n)', #Portuguese
                    ]
                    tt_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                    if not tt_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time travel count not found in profile or progress message.', message)
                        return
                    time_travel_count = int(tt_match.group(1))
                if time_travel_count != user_settings.time_travel_count:
                    kwargs['time_travel_count'] = time_travel_count
                trade_daily_total = floor(100 * (time_travel_count + 1) ** 1.35)
                if trade_daily_total != user_settings.trade_daily_total:
                    kwargs['trade_daily_total'] = trade_daily_total

                # Update current area
                area_match = re.search(r'rea\*\*: (.+?) \(', embed_field0_value.lower())
                if not area_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Area not found in current area profile or progress message.', message)
                    return
                new_area = area_match.group(1)
                if new_area == 'top':
                    new_area = 21
                else:
                    new_area = int(new_area)
                if user_settings.current_area != new_area:
                    kwargs['current_area'] = new_area

                # Remove partner name if not married
                partner_match = re.search(r'married to (.+?)$', embed_footer.lower())
                partner_name = partner_match.group(1) if partner_match else None
                if partner_name != user_settings.partner_name:
                    kwargs['partner_name'] = partner_name

                if kwargs:
                    await user_settings.update(**kwargs)
                    

# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(ProfileCog(bot))