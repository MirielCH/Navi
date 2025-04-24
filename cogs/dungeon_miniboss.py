# dungeon_miniboss.py

import asyncio
from datetime import timedelta
import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings


class DungeonMinibossCog(commands.Cog):
    """Cog that contains the dungeon/miniboss detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
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
            message_author = message_title = icon_url = message_footer = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = str(embed.author.icon_url)
            if embed.title is not None: message_title = str(embed.title)
            if embed.footer is not None: message_footer = embed.footer.text

            # Dungeon / Miniboss cooldown
            search_strings = [
                'been in a fight with a boss recently', #English
                'en una pelea con un boss recientemente', #Spanish
                'em uma briga com um boss recentemente', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command_message = None
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_DUNGEON_MINIBOSS_MININTBOSS)
                    )
                    if user_command_message is None: return
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
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found for dungeon cooldown message.', message)
                        return
                if interaction_user not in embed_users: return
                if not user_settings.bot_enabled or not user_settings.alert_dungeon_miniboss.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                command_dungeon = await functions.get_slash_command(user_settings, 'dungeon')
                command_miniboss = await functions.get_slash_command(user_settings, 'miniboss')
                user_command = f"{command_dungeon} or {command_miniboss}"
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in dungeon cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_dungeon_miniboss.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'dungeon-miniboss', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Dungeons
            search_strings_author = [
               " — dungeon", # All languages
            ]
            search_strings_footer = [
                'eternality', # Eternal dungeon, all languages
                'unlocked commands:', # Dungeons 1-9, 11-14, English
                'comandos desbloqueados:', # Dungeons 1-9, 11-14, Spanish & Portuguese
                'unlocked the next area', # Dungeons 11-15, English
                'unlocked the next area', # TODO: Dungeons 11-15, Spanish
                'unlocked the next area', # TODO: Dungeons 11-15, Portuguese
                'both have unlocked area 11', # Dungeon 10, English
                'both have unlocked area 11', # TODO: Dungeon 10, Spanish
                'both have unlocked area 11', # TODO: Dungeon 10, Portuguese
                'players are still in the same area', # Dungeons 16-20, English
                'players are still in the same area', # TODO: Dungeons 16-20, Spanish
                'players are still in the same area', # TODO: Dungeons 16-20, Portuguese
            ]
            if (any(search_string in message_author.lower() for search_string in search_strings_author) and
                any(search_string in message_footer.lower() for search_string in search_strings_footer)):
                user_id = user_name = user_command_message = None
                solo_dungeon = False
                dungeon_users = []
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                search_strings_solo_dungeons = [
                    'eternality', # Eternal dungeon, all languages
                    'unlocked the next area', # Dungeons 11-15, English
                    'unlocked the next area', # TODO: Dungeons 11-15, Spanish
                    'unlocked the next area', # TODO: Dungeons 11-15, Portuguese
                ]
                if any(search_string in message_footer.lower() for search_string in search_strings_solo_dungeons):
                    solo_dungeon = True
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_DUNGEON,
                                                        user_name=user_name)
                        )
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in dungeon message.', message)
                        return
                    if user is None:
                        user = user_command_message.author
                if solo_dungeon:
                    dungeon_users.append(user)
                else:
                    if slash_command:
                        dungeon_start_message = (
                            await messages.find_message(message.channel.id, r'^dungeon `',
                                                        user=message.author)
                        )
                        if not dungeon_start_message:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Dungeon start message not found for slash dungeon.', message)
                            return
                        player_list = dungeon_start_message.content.split('\n')[0].split('|')[-1].strip()
                        player_names = re.findall(r'(.+?)(?:,|$)', player_list)
                        for player_name in player_names:
                            guild_members = await functions.get_member_by_name(self.bot, message.guild, player_name.strip())
                            if guild_members:
                                dungeon_users.append(guild_members[0])
                    if not slash_command:
                        dungeon_users.append(user)
                        for mentioned_user in user_command_message.mentions:
                            if mentioned_user == message.author: continue
                            dungeon_users.append(mentioned_user)
                for dungeon_user in dungeon_users:
                    try:
                        user_settings: users.User = await users.get_user(dungeon_user.id)
                    except exceptions.FirstTimeUserError:
                        continue
                    if not user_settings.bot_enabled or not user_settings.alert_dungeon_miniboss.enabled: continue
                    user_command = await functions.get_slash_command(user_settings, 'dungeon')
                    time_left = await functions.calculate_time_left_from_cooldown(message, user_settings, 'dungeon-miniboss')
                    if time_left < timedelta(0): continue
                    reminder_message = user_settings.alert_dungeon_miniboss.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                       await reminders.insert_user_reminder(dungeon_user.id, 'dungeon-miniboss', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    if not message.reactions:
                        await functions.add_reminder_reaction(message, reminder, user_settings)
                    if solo_dungeon:                
                        asyncio.ensure_future(functions.call_ready_command(self.bot, message, dungeon_user, user_settings, 'dungeon-miniboss'))


        if not message.embeds:
            message_content = message.content

            # Dungeon reset from returning shop
            search_strings = [
                'dungeon reset` successfully bought', #English
                'dungeon reset` comprado(s)', #Spanish, Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_RETURNING_BUY_DUNGEON_RESET)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for dungeon reset message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(user.id, 'dungeon-miniboss')
                except exceptions.NoDataFoundError:
                    return
                await reminder.delete()
                if reminder.record_exists:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(f'Had an error deleting the dungeon/miniboss reminder in dungeon reset.',
                                           message)
                    return
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(DungeonMinibossCog(bot))