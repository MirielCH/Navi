# cooldowns.py

from datetime import timedelta
import re

import discord
from discord import utils
from discord.ext import bridge, commands
from datetime import timedelta

from cache import messages
from database import alts, errors, reminders, users
from database import cooldowns as cooldowns_db
from resources import emojis, exceptions, functions, regex, settings, strings


class CooldownsCog(commands.Cog):
    """Cog that contains the cooldowns detection commands"""
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
        row: discord.Component
        for row in message_after.components:
            if isinstance(row, discord.ActionRow):
                for component in row.children:
                    if isinstance(component, (discord.Button, discord.SelectMenu)):
                        if component.disabled:
                            return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if not message.embeds: return
        embed: discord.Embed = message.embeds[0]
        message_author = message_footer = message_fields = icon_url = message_description = ''
        if embed.description is not None:
            message_description = embed.description
        if embed.author is not None:
            message_author = str(embed.author.name)
            icon_url = embed.author.icon_url
        for field in embed.fields:
            message_fields = f'{message_fields}\n{str(field.value)}'.strip()
        if embed.footer is not None: message_footer = str(embed.footer.text)

        # Cooldown
        search_strings = [
            'check the short version of this command', #English
            'revisa la versión más corta de este comando', #Spanish
            'verifique a versão curta deste comando', #Portuguese
        ]
        if any(search_string in message_footer.lower() for search_string in search_strings):
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
                    return
            if interaction_user not in embed_users:
                user_alts = await alts.get_alts(interaction_user.id)
                alt_found = False
                if user_alts:
                    for embed_user in embed_users:
                        if embed_user is not None:
                            if embed_user.id in user_alts:
                                interaction_user = message.guild.get_member(embed_user.id)
                                alt_found = True
                if not alt_found: return
            try:
                user_settings: users.User = await users.get_user(interaction_user.id)
            except exceptions.FirstTimeUserError:
                return
            if not user_settings.bot_enabled: return
            # Anniversary event reduction update
            search_patterns = [
                r'anniversary event cooldown reduction\*\*: (\d+?)%',
                r'reducción de cooldown del evento de aniversario\*\*: (\d+?)%',
                r'redução do cooldown do evento de aniversário\*\*: (\d+?)%',
            ]
            anniversary_event_match = await functions.get_match_from_patterns(search_patterns,
                                                                              message_description)
            if anniversary_event_match:
                event_reduction = int(anniversary_event_match.group(1))
                anniversary_activities = [
                    'arena',
                    'card-hand',
                    'quest',
                    'dungeon-miniboss',
                    'lootbox',
                    'hunt',
                    'adventure',
                    'training',
                    'work',
                    'horse',
                    'duel',
                    'quest-decline',
                    'epic',
                    'farm',
                ]
                all_cooldowns = await cooldowns_db.get_all_cooldowns()
                if all_cooldowns[0].event_reduction_slash != event_reduction:
                    for cooldown in all_cooldowns:
                        if cooldown.activity in anniversary_activities:
                            await cooldown.update(event_reduction_slash=event_reduction,
                                                event_reduction_mention=event_reduction)
            cooldowns = []
            ready_commands = []
            if user_settings.alert_daily.enabled:
                daily_match = re.search(r"daily`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if daily_match:
                    daily_timestring = daily_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'daily')
                    daily_message = user_settings.alert_daily.message.replace('{command}', user_command)
                    cooldowns.append(['daily', daily_timestring.lower(), daily_message])
                else:
                    ready_commands.append('daily')
            if user_settings.alert_weekly.enabled:
                weekly_match = re.search(r"weekly`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if weekly_match:
                    weekly_timestring = weekly_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'weekly')
                    weekly_message = user_settings.alert_weekly.message.replace('{command}', user_command)
                    cooldowns.append(['weekly', weekly_timestring.lower(), weekly_message])
                else:
                    ready_commands.append('weekly')
            if user_settings.alert_lootbox.enabled:
                lb_match = re.search(r"lootbox`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if lb_match:
                    user_command = await functions.get_slash_command(user_settings, 'buy')
                    lootbox_name = '[lootbox]' if user_settings.last_lootbox == '' else f'{user_settings.last_lootbox} lootbox'
                    if user_settings.slash_mentions_enabled:
                        user_command = f"{user_command} `item: {lootbox_name}`"
                    else:
                        user_command = f"{user_command} `{lootbox_name}`".replace('` `', ' ')
                    lb_timestring = lb_match.group(1)
                    lb_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                    cooldowns.append(['lootbox', lb_timestring.lower(), lb_message])
                else:
                    ready_commands.append('lootbox')
            if user_settings.alert_card_hand.enabled:
                card_hand_match = re.search(r"hand`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if card_hand_match:
                    card_hand_timestring = card_hand_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'card hand')
                    card_hand_message = user_settings.alert_card_hand.message.replace('{command}', user_command)
                    cooldowns.append(['card-hand', card_hand_timestring.lower(), card_hand_message])
                else:
                    ready_commands.append('card-hand')
            if user_settings.alert_hunt.enabled and not user_settings.hunt_reminders_combined:
                hunt_match = re.search(r'hunt(?: hardmode)?`\*\* \(\*\*(.+?)\*\*', message_fields.lower())
                if hunt_match:
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.last_hunt_mode != '':
                        if user_settings.slash_mentions_enabled:
                            user_command = f"{user_command} `mode: {user_settings.last_hunt_mode}`"
                        else:
                            user_command = f"{user_command} `{user_settings.last_hunt_mode}`".replace('` `', ' ')
                    else:
                        if 'hardmode' in hunt_match.group(0):
                            if user_settings.slash_mentions_enabled:
                                user_command = f"{user_command} `mode: hardmode`"
                            else:
                                user_command = f"{user_command} `hardmode`".replace('` `', ' ')
                    hunt_timestring = hunt_match.group(1)
                    hunt_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    cooldowns.append(['hunt', hunt_timestring.lower(), hunt_message])
                else:
                    ready_commands.append('hunt')
            if user_settings.alert_adventure.enabled:
                adv_match = re.search(r'adventure(?: hardmode)?`\*\* \(\*\*(.+?)\*\*', message_fields.lower())
                if adv_match:
                    user_command = await functions.get_slash_command(user_settings, 'adventure')
                    if user_settings.last_adventure_mode != '':
                        if user_settings.slash_mentions_enabled:
                            user_command = f"{user_command} `mode: {user_settings.last_adventure_mode}`"
                        else:
                            user_command = f"{user_command} `{user_settings.last_adventure_mode}`".replace('` `', ' ')
                    else:
                        if 'hardmode' in adv_match.group(0):
                            if user_settings.slash_mentions_enabled:
                                user_command = f"{user_command} `mode: hardmode`"
                            else:
                                user_command = f"{user_command} `hardmode`".replace('` `', ' ')
                    adv_timestring = adv_match.group(1)
                    adv_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                    cooldowns.append(['adventure', adv_timestring.lower(), adv_message])
                else:
                    ready_commands.append('adventure')
            if user_settings.alert_training.enabled:
                tr_match = re.search(r"raining`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if tr_match:
                    user_command = await functions.get_slash_command(user_settings, user_settings.last_training_command)
                    tr_timestring = tr_match.group(1)
                    tr_message = user_settings.alert_training.message.replace('{command}', user_command)
                    cooldowns.append(['training', tr_timestring.lower(), tr_message])
                else:
                    ready_commands.append('training')
            if user_settings.alert_quest.enabled:
                quest_match = re.search(r"quest`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if quest_match:
                    user_command = await functions.get_slash_command(user_settings, user_settings.last_quest_command)
                    quest_timestring = quest_match.group(1)
                    quest_message = user_settings.alert_quest.message.replace('{command}', user_command)
                    cooldowns.append(['quest', quest_timestring.lower(), quest_message])
                else:
                    ready_commands.append('quest')
            if user_settings.alert_duel.enabled:
                duel_match = re.search(r"duel`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if duel_match:
                    duel_timestring = duel_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'duel')
                    duel_message = user_settings.alert_duel.message.replace('{command}', user_command)
                    cooldowns.append(['duel', duel_timestring.lower(), duel_message])
                else:
                    ready_commands.append('duel')
            if user_settings.alert_arena.enabled:
                arena_match = re.search(r"rena`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if arena_match:
                    arena_timestring = arena_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'arena')
                    arena_message = user_settings.alert_arena.message.replace('{command}', user_command)
                    cooldowns.append(['arena', arena_timestring.lower(), arena_message])
                else:
                    ready_commands.append('arena')
            if user_settings.alert_dungeon_miniboss.enabled:
                dungmb_match = re.search(r"boss`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if dungmb_match:
                    dungmb_timestring = dungmb_match.group(1)
                    command_dungeon = await functions.get_slash_command(user_settings, 'dungeon')
                    command_miniboss = await functions.get_slash_command(user_settings, 'miniboss')
                    user_command = f"{command_dungeon} or {command_miniboss}"
                    dungmb_message = user_settings.alert_dungeon_miniboss.message.replace('{command}', user_command)
                    cooldowns.append(['dungeon-miniboss', dungmb_timestring.lower(), dungmb_message])
                else:
                    ready_commands.append('dungeon-miniboss')
            if user_settings.alert_horse_breed.enabled:
                horse_match = re.search(r"race`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if horse_match:
                    horse_timestring = horse_match.group(1)
                    command_breed = await functions.get_slash_command(user_settings, 'horse breeding')
                    command_race = await functions.get_slash_command(user_settings, 'horse race')
                    user_command = f"{command_breed} or {command_race}"
                    horse_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                    cooldowns.append(['horse', horse_timestring.lower(), horse_message])
                else:
                    ready_commands.append('horse')
            if user_settings.alert_vote.enabled:
                vote_match = re.search(r"vote`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if vote_match:
                    vote_timestring = vote_match.group(1)
                    user_command = await functions.get_slash_command(user_settings, 'vote')
                    vote_message = user_settings.alert_vote.message.replace('{command}', user_command)
                    cooldowns.append(['vote', vote_timestring.lower(), vote_message])
                else:
                    ready_commands.append('vote')
            if user_settings.alert_farm.enabled:
                farm_match = re.search(r"farm`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
                if farm_match:
                    farm_timestring = farm_match.group(1)
                    user_command = await functions.get_farm_command(user_settings)
                    farm_message = user_settings.alert_farm.message.replace('{command}', user_command)
                    cooldowns.append(['farm', farm_timestring.lower(), farm_message])
                else:
                    ready_commands.append('farm')
            if user_settings.alert_work.enabled:
                search_patterns = [
                    r'mine`\*\* \(\*\*(.+?)\*\*',
                    r'pickaxe`\*\* \(\*\*(.+?)\*\*',
                    r'drill`\*\* \(\*\*(.+?)\*\*',
                    r'dynamite`\*\* \(\*\*(.+?)\*\*',
                ]
                work_match = await functions.get_match_from_patterns(search_patterns, message_fields.lower())
                if work_match:
                    if user_settings.last_work_command != '':
                        user_command = await functions.get_slash_command(user_settings, user_settings.last_work_command)
                    else:
                        user_command = 'work command'
                    work_timestring = work_match.group(1)
                    work_message = user_settings.alert_work.message.replace('{command}', user_command)
                    cooldowns.append(['work', work_timestring.lower(), work_message])
                else:
                    ready_commands.append('work')
            for cooldown in cooldowns:
                cd_activity = cooldown[0]
                cd_timestring = cooldown[1]
                cd_message = cooldown[2]
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20 and cd_activity != 'vote':
                    continue
                time_left = await functions.parse_timestring_to_timedelta(cd_timestring)
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                current_time = utils.utcnow()
                time_elapsed = current_time - bot_answer_time
                time_left -= time_elapsed
                if time_left < timedelta(0): continue
                time_left = timedelta(seconds=time_left.total_seconds() + 1)
                if user_settings.multiplier_management_enabled:
                    await user_settings.update_multiplier(cd_activity, time_left)
                if time_left.total_seconds() > 0:
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(interaction_user.id, cd_activity, time_left,
                                                             message.channel.id, cd_message, overwrite_message=False)
                    )
                    if not reminder.record_exists:
                        await message.channel.send(strings.MSG_ERROR)
                        return
                if cd_activity == 'hunt':
                    await user_settings.update(hunt_end_time=current_time + time_left)
            for activity in ready_commands:
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(interaction_user.id, activity)
                except exceptions.NoDataFoundError:
                    continue
                await reminder.delete()
                if reminder.record_exists:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(f'Had an error deleting the reminder with activity "{activity}".', message)
            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

        # Ready
        search_strings = [
            'check the long version of this command', #English
            'revisa la versión más larga de este comando', #Spanish
            'verifique a versão longa deste comando', #Portuguese
        ]
        if any(search_string in message_footer.lower() for search_string in search_strings):
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
                    embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                if not user_name_match or not embed_users:
                    return
            if interaction_user not in embed_users: return
            if not user_settings.bot_enabled: return
            ready_commands = []
            if user_settings.alert_daily.enabled and 'daily`**' in message_fields.lower():
                ready_commands.append('daily')
            if user_settings.alert_weekly.enabled and 'weekly`**' in message_fields.lower():
                ready_commands.append('weekly')
            if user_settings.alert_lootbox.enabled and 'lootbox`**' in message_fields.lower():
                ready_commands.append('lootbox')
            if user_settings.alert_card_hand.enabled and 'hand`**' in message_fields.lower():
                ready_commands.append('card-hand')
            if user_settings.alert_hunt.enabled:
                hunt_match = re.search(r'hunt(?: hardmode)?`\*\*', message_fields.lower())
                if hunt_match: ready_commands.append('hunt')
            if user_settings.alert_adventure.enabled:
                adv_match = re.search(r'adventure(?: hardmode)?`\*\*', message_fields.lower())
                if adv_match: ready_commands.append('adventure')
            if user_settings.alert_training.enabled and 'raining`**' in message_fields.lower():
                ready_commands.append('training')
            if user_settings.alert_quest.enabled and 'quest`**' in message_fields.lower():
                ready_commands.append('quest')
            if user_settings.alert_duel.enabled and 'duel`**' in message_fields.lower():
                ready_commands.append('duel')
            if user_settings.alert_arena.enabled and 'rena`**' in message_fields.lower():
                ready_commands.append('arena')
            if user_settings.alert_dungeon_miniboss.enabled and 'boss`**' in message_fields.lower():
                ready_commands.append('dungeon-miniboss')
            if user_settings.alert_horse_breed.enabled and 'race`**' in message_fields.lower():
                ready_commands.append('horse')
            if user_settings.alert_vote.enabled and 'vote`**' in message_fields.lower():
                ready_commands.append('vote')
            if user_settings.alert_farm.enabled and 'farm`**' in message_fields.lower():
                ready_commands.append('farm')
            if user_settings.alert_work.enabled:
                search_strings_work = [
                    r'mine`**',
                    r'pickaxe`**',
                    r'drill`**',
                    r'dynamite`**',
                ]
                if any(search_string in message_fields.lower() for search_string in search_strings_work):
                    ready_commands.append('work')
            for activity in ready_commands:
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(interaction_user.id, activity)
                except exceptions.NoDataFoundError:
                    continue
                await reminder.delete()
                if reminder.record_exists:
                    await functions.add_warning_reaction(message)
                    await errors.log_error(f'Had an error deleting the reminder with activity "{activity}".', message)
            if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(CooldownsCog(bot))