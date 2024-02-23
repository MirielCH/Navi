# boosts.py

from datetime import timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, reminders, users
from resources import emojis, exceptions, functions, regex, settings, strings


class BoostsCog(commands.Cog):
    """Cog that contains the boost detection commands"""
    def __init__(self, bot):
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
            embed_author = embed_title = icon_url = embed_description = ''
            if embed.author is not None:
                embed_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title is not None: embed_title = str(embed.title)
            if embed.description is not None: embed_description = str(embed.description)
            embed_potion_fields = ''
            if embed.fields:
                embed_potion_fields = embed.fields[0].value
                if len(embed.fields) > 1:
                    if embed.fields[1].name == '':
                        embed_potion_fields = f'{embed_potion_fields}\n{embed.fields[1].value}'

            # Boosts cooldowns
            search_strings = [
                'these are your active boosts', #English
                'estos son tus boosts activos', #Spanish
                'estes são seus boosts ativos', #Portuguese
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)):
                user_id = user_name = user_command_message = None
                potion_dragon_breath_active = round_card_active = potion_flask_active = False
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_BOOSTS)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        return
                    interaction_user = user_command_message.author
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    embed_users.append(message.guild.get_member(user_id))
                if not embed_users:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if not user_name_match or not embed_users:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find embed user for the boosts message.', message)
                        return
                if interaction_user not in embed_users: return
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                all_boosts = list(strings.ACTIVITIES_BOOSTS[:])
                for line in embed_potion_fields.lower().split('\n'):
                    search_strings = [
                        'none', #English
                        'ninguno', #Spanish
                        'nenhum', #Portuguese
                    ]
                    if any(search_string == embed_potion_fields.lower() for search_string in search_strings):
                        try:
                            active_reminders = await reminders.get_active_user_reminders(interaction_user.id)
                            for active_reminder in active_reminders:
                                if (active_reminder.activity in strings.ACTIVITIES_BOOSTS
                                    or active_reminder.activity in strings.BOOSTS_ALIASES):
                                    await active_reminder.delete()
                        except exceptions.NoDataFoundError:
                            pass
                        break
                    active_item_match = re.search(r' \*\*(.+?)\*\*: (.+?)$', line)
                    if not active_item_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Active item not found in boosts message.', message)
                        return
                    active_item_activity = active_item_match.group(1).replace(' ','-')
                    active_item_activity = strings.BOOSTS_ALIASES.get(active_item_activity, active_item_activity)
                    if active_item_activity in all_boosts: all_boosts.remove(active_item_activity)
                    if active_item_activity == 'dragon-breath-potion':
                        potion_dragon_breath_active = True
                        if not user_settings.potion_dragon_breath_active:
                            await user_settings.update(potion_dragon_breath_active=True)
                        if not user_settings.alert_boosts.enabled: return
                    if active_item_activity == 'round-card':
                        round_card_active = True
                        if not user_settings.round_card_active:
                            await user_settings.update(round_card_active=True)
                        if not user_settings.alert_boosts.enabled: return
                    if active_item_activity == 'flask-potion':
                        potion_flask_active = True
                        if not user_settings.potion_flask_active:
                            await user_settings.update(potion_flask_active=True)
                        if not user_settings.alert_boosts.enabled: return
                    if not user_settings.alert_boosts.enabled: continue
                    active_item_emoji = emojis.BOOSTS_EMOJIS.get(active_item_activity, '')
                    time_string = active_item_match.group(2)
                    time_left = await functions.calculate_time_left_from_timestring(message, time_string)
                    if time_left < timedelta(0): return
                    reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', active_item_emoji)
                        .replace('{boost_item}', active_item_activity.replace('-', ' '))
                        .replace('  ', ' ')
                    )
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(interaction_user.id, active_item_activity, time_left,
                                                             message.channel.id, reminder_message)
                    )
                for activity in all_boosts:
                    try:
                        active_reminder = await reminders.get_user_reminder(interaction_user.id, activity)
                        await active_reminder.delete()
                    except exceptions.NoDataFoundError:
                        continue
                if user_settings.potion_dragon_breath_active != potion_dragon_breath_active:
                    await user_settings.update(potion_dragon_breath_active=potion_dragon_breath_active)
                if user_settings.round_card_active != round_card_active:
                    await user_settings.update(round_card_active=round_card_active)
                if user_settings.potion_flask_active != potion_flask_active:
                    await user_settings.update(potion_flask_active=potion_flask_active)
                if user_settings.reactions_enabled and user_settings.alert_boosts.enabled:
                    await message.add_reaction(emojis.NAVI)

        if not message.embeds:
            message_content = message.content

            # Party popper
            search_strings = [
                'uses a <:partypopper', #English
                'usa el <:partypopper', #Spanish
                'uses the <:partypopper', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for party popper message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_PARTY_POPPER,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the party popper message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                timestring_match = re.search(r'for \*\*(.+?)\*\*:', message_content.lower())
                time_left_hours = 1
                if user_settings.user_pocket_watch_multiplier < 1: time_left_hours *= 2
                time_left = timedelta(hours=time_left_hours)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.PARTY_POPPER)
                        .replace('{boost_item}', 'party popper')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'party-popper', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Alchemy potions
            search_strings = [
                '**, you\'ve received the following boosts for', #English
                '**, you\'ve received the following boosts for', #Spanish
                '**, you\'ve received the following boosts for', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ALCHEMY)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the alchemy message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                item_activity_match = re.search(r'a (.+?) \*\*(.+?)\*\*, ', message_content.lower())
                timestring_match = re.search(r'for \*\*(.+?)\*\*:', message_content.lower())
                if not item_activity_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find the item name in the alchemy message.',
                                            message)
                    return
                item_activity = item_activity_match.group(2).replace(' ','-')
                item_activity = strings.BOOSTS_ALIASES.get(item_activity, item_activity)
                if item_activity == 'dragon-breath-potion':
                    await user_settings.update(potion_dragon_breath_active=True)
                if item_activity == 'round-card':
                    await user_settings.update(round_card_active=True)
                if not user_settings.alert_boosts.enabled: return
                item_emoji = emojis.BOOSTS_EMOJIS.get(item_activity, '')
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                if user_settings.user_pocket_watch_multiplier < 1: time_left *= 2
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', item_emoji)
                        .replace('{boost_item}', item_activity.replace('-',' '))
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, item_activity, time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Valentine boost
            search_strings = [
                '`valentine boost` successfully bought', #English
                '`valentine boost` comprado(s)', #Spanish & Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_LOVE_BUY_VALENTINE_BOOST)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the valentine boost message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                time_left_hours = 1
                if user_settings.user_pocket_watch_multiplier < 1: time_left_hours *= 2
                time_left = timedelta(hours=time_left_hours)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', '❤️')
                        .replace('{boost_item}', 'valentine boost')
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'valentine-boost', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # Halloween boost
            search_strings = [
                '`halloween boost` successfully bought', #English
                '`halloween boost` comprado(s)', #Spanish & Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HAL_BUY_HALLOWEEN_BOOST)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the hal boost message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                time_left_hours = 2.5
                if user_settings.user_pocket_watch_multiplier < 1: time_left_hours *= 2
                time_left = timedelta(hours=time_left_hours)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.PUMPKIN)
                        .replace('{boost_item}', 'halloween boost')
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'halloween-boost', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # Christmas boost
            search_strings = [
                '`christmas boost` successfully bought', #English
                '`christmas boost` comprado(s)', #Spanish & Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_BUY_CHRISTMAS_BOOST)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the xmas boost message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                time_left_hours = 4
                if user_settings.user_pocket_watch_multiplier < 1: time_left_hours *= 2
                time_left = timedelta(hours=time_left_hours)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.PRESENT)
                        .replace('{boost_item}', 'christmas boost')
                        .replace('  ', ' ')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'christmas-boost', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # Round card
            search_strings = [
                '** eats a <:roundcard', #English
                '** eats a <:roundcard', #Spanish, MISSING
                '** eats a <:roundcard', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for round card message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_ROUND_CARD,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the round card message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                await user_settings.update(round_card_active=True)
                if not user_settings.alert_boosts.enabled: return
                timestring_match = re.search(r'for \*\*(.+?)\*\*:', message_content.lower())
                time_left = await functions.parse_timestring_to_timedelta(timestring_match.group(1).lower())
                if user_settings.user_pocket_watch_multiplier < 1: time_left *= 2
                await reminders.reduce_reminder_time_percentage(user.id, 90, strings.ROUND_CARD_AFFECTED_ACTIVITIES,
                                                                user_settings)
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.CARD_ROUND)
                        .replace('{boost_item}', 'round card')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'round-card', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

                
            # Mega boost
            search_strings = [
                '** uses a <:megaboost', #English
                '** uses a <:megaboost', #Spanish, MISSING
                '** uses a <:megaboost', #Portuguese, MISSING
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                user = await functions.get_interaction_user(message)
                user_command_message = None
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for mega boost message.',
                                               message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_USE_MEGA_BOOST,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the mega boost message.',
                                               message)
                        return
                    if user is None: user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_boosts.enabled: return
                time_left = timedelta(days=30)
                if user_settings.user_pocket_watch_multiplier < 1: time_left *= 2
                reminder_message = (
                        user_settings.alert_boosts.message
                        .replace('{boost_emoji}', emojis.MEGA_BOOST)
                        .replace('{boost_item}', 'mega boost')
                    )
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'mega-boost', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

# Initialization
def setup(bot):
    bot.add_cog(BoostsCog(bot))