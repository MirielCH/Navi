# hunt.py

import asyncio
from datetime import timedelta
from math import ceil, floor
import re

import discord
from discord import utils
from discord.ext import bridge, commands

from cache import messages
from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, regex, settings, strings


class HuntCog(commands.Cog):
    """Cog that contains the hunt detection commands"""
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
            message_author = message_title = icon_url = message_description = ''
            if embed.author is not None:
                message_author = str(embed.author.name)
                icon_url = str(embed.author.icon_url)
            if embed.title is not None: message_title = str(embed.title)
            if embed.description is not None: message_description = str(embed.description)

            # Hunt cooldown
            search_strings = [
                'you have already looked around', #English
                'ya has mirado a tu alrededor', #Spanish
                'você já olhou ao seu redor', #Portuguese
            ]
            if any(search_string in message_title.lower() for search_string in search_strings):
                user_id = user_name = user_command = last_hunt_mode = user_command_message = None
                hardmode = together = alone = old = False
                embed_users = []
                interaction_user = await functions.get_interaction_user(message)
                slash_command = True if interaction_user is not None else False
                if interaction_user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Interaction user not found for hunt cooldown message.', message)
                        return
                    interaction_user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                    try:
                        embed_users.append(message.guild.get_member(user_id))
                    except discord.NotFound:
                        pass
                else:
                    user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        embed_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if user_name_match is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in hunt cooldown message.', message)
                        return
                if not slash_command:
                    user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                    user_command_message_content = re.sub(r'\bt\b', 'together', user_command_message_content)
                    user_command_message_content = re.sub(r'\ba\b', 'alone', user_command_message_content)
                    user_command_message_content = re.sub(r'\bo\b', 'old', user_command_message_content)
                    if 'hardmode'in user_command_message_content.lower(): hardmode = True
                    if 'together'in user_command_message_content.lower(): together = True
                    if 'alone'in user_command_message_content.lower(): alone = True
                    if 'old'in user_command_message_content.lower(): old = True
                    last_hunt_mode = ''
                    if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                    if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                    if old: last_hunt_mode = f'{last_hunt_mode} old'
                    last_hunt_mode = last_hunt_mode.strip()
                if not user_settings.bot_enabled or not user_settings.alert_hunt.enabled or not user_settings.alert_hunt_partner.enabled: return
                if not user_settings.area_20_cooldowns_enabled and user_settings.current_area == 20: return
                user_command = await functions.get_slash_command(user_settings, 'hunt')
                if user_settings.last_hunt_mode != '':
                    if user_settings.slash_mentions_enabled:
                        user_command = f"{user_command} `mode: {user_settings.last_hunt_mode}`"
                    else:
                        user_command = f"{user_command} `{user_settings.last_hunt_mode}`".replace('` `', ' ')
                timestring_match = await functions.get_match_from_patterns(regex.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in hunt cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if (user_settings.multiplier_management_enabled and interaction_user in embed_users):
                    await user_settings.update_multiplier('hunt', time_left)
                if user_settings.hunt_reminders_combined:
                    try:
                        hunt_reminder = await reminders.get_user_reminder(interaction_user.id, 'hunt')
                        if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)
                        return
                    except exceptions.NoDataFoundError:
                        pass
                if time_left < timedelta(0): return
                time_left_seconds = time_left.total_seconds()
                time_left = timedelta(seconds=ceil(time_left_seconds))
                activity = 'hunt'
                command: str = user_command
                reminder_message = user_settings.alert_hunt.message.replace('{command}', command)
                if not user_settings.hunt_reminders_combined and interaction_user not in embed_users and user_settings.partner_name is not None:
                    activity: str = 'hunt-partner'
                    command: str = await functions.get_slash_command(user_settings, 'hunt')
                    reminder_message = (user_settings.alert_hunt_partner.message
                                        .replace('{command}', command)
                                        .replace('{partner}', user_settings.partner_name))
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, activity, time_left,
                                                         message.channel.id, reminder_message,
                                                         overwrite_message=False)
                )
                if activity == 'hunt':
                    await user_settings.update(hunt_end_time=utils.utcnow() + time_left)
                await functions.add_reminder_reaction(message, reminder, user_settings)


            # Rare hunt monster event reset (all languages)
            search_strings = [
                'golden wolf',
                'ruby zombie',
                'diamond unicorn',
                'emerald mermaid',
                'sapphire killer robot',
            ]
            if  (any(search_string in message_description.lower() for search_string in search_strings)
                 and (':coffin:' in message_description.lower() or '⚰️' in message_description.lower())):
                event_players = embed.fields[0].value.split('\n')[0]
                players_found = re.findall(r'\s(.+?)(?:,|$)', event_players)
                for user_name in players_found:
                    users_found = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if users_found:
                        try:
                            user_settings = await users.get_user(users_found[0].id)
                        except exceptions.FirstTimeUserError:
                            continue
                        await reminders.reduce_reminder_time_percentage(user_settings, 100, ['hunt',])

        if not message.embeds:
            message_content = ''
            for line in message.content.split('\n'):
                if not re.match(r'\bcard\b', message.content):
                    message_content = f'{message_content}\n{line}'
            message_content = message_content.strip()
            # Hunt
            search_strings = [
                'found a', #English
                'found the', #English
                'encontr', #Spanish, Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or 'pink wolf' in message_content.lower() or 'party slime' in message_content.lower()
                )
            ):
                user_name = partner_name = last_hunt_mode = user_command_message = partner = None
                hardmode = together = alone = event_mob = partner_alerts_enabled = False
                partner_christmas_area = False
                user = await functions.get_interaction_user(message)
                slash_command = False if user is None else True
                search_strings_hardmode = [
                    '(but stronger)', #English
                    '(pero más fuerte)', #Spanish
                    '(só que mais forte)', #Portuguese
                ]
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                search_strings_alone = [
                    '(but way stronger!!!)', #English
                    '(mucho más fuerte!!!)', #Spanish
                    '(muito mais forte!!!)', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_hardmode):
                    hardmode = True
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
                if any(search_string in message_content.lower() for search_string in search_strings_alone):
                    alone = True
                old = True if '__**' not in message_content.lower() else False
                search_strings_event_mobs = [
                    'horslime',
                    'christmas slime',
                    'bunny slime',
                    'pink wolf',
                    'party slime',
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_event_mobs):
                    search_strings_together = [
                        'both players', #English
                    ]
                    if any(search_string in message_content.lower() for search_string in search_strings_together):
                        together = True
                    event_mob = True
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
                        if event_mob and not slash_command:
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_HUNT)
                            )
                            if user_command_message is None:
                                await functions.add_warning_reaction(message)
                                await errors.log_error('User not found for event mob hunt message.', message)
                                return
                            user = user_command_message.author
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User names not found in hunt together message.', message)
                            return
                else:
                    search_patterns = [
                        r"\*\*(.+?)\*\* found a", #English
                        r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        if user_name.lower() == 'both players': # Needs to be updated when an event hits that uses this
                            user_name = None
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User names not found in hunt together message.', message)
                        return
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for hunt message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if together:
                    await user_settings.update(partner_name=partner_name)
                if not user_settings.bot_enabled: return
                current_time = utils.utcnow()
                if user_settings.tracking_enabled:
                    command = 'hunt' if not together else 'hunt together'
                    await tracking.insert_log_entry(user.id, message.guild.id, command, current_time)
                if user_settings.partner_id is not None:
                    partner: users.User = await users.get_user(user_settings.partner_id)
                    if partner.partner_channel_id is not None and partner.alert_partner.enabled and partner.bot_enabled:
                        partner_alerts_enabled = True
                if not user_settings.alert_hunt.enabled and not partner_alerts_enabled and not user_settings.alert_hunt_partner.enabled: return
                user_global_name = user.global_name if user.global_name is not None else user.name
                if user_settings.alert_hunt.enabled or user_settings.alert_hunt_partner.enabled:
                    hunt_command = user_command = await functions.get_slash_command(user_settings, 'hunt')
                    last_hunt_mode = ''
                    if not event_mob:
                        if hardmode:
                            last_hunt_mode = f'{last_hunt_mode} hardmode'
                        if together:
                            last_hunt_mode = f'{last_hunt_mode} together'
                        if alone:
                            last_hunt_mode = f'{last_hunt_mode} alone'
                        if old and together and slash_command:
                            last_hunt_mode = f'{last_hunt_mode} old'
                        last_hunt_mode = last_hunt_mode.strip()
                        if last_hunt_mode != '':
                            if user_settings.slash_mentions_enabled:
                                user_command = f"{user_command} `mode: {last_hunt_mode}`"
                            else:
                                user_command = f"{user_command} `{last_hunt_mode}`".replace('` `', ' ')
                    if event_mob:
                        if user_settings.last_hunt_mode is not None:
                            if user_settings.slash_mentions_enabled:
                                user_command = f"{user_command} `mode: {user_settings.last_hunt_mode}`"
                            else:
                                user_command = f"{user_command} `{user_settings.last_hunt_mode}`".replace('` `', ' ')
                        else:
                            user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                            user_command_message_content = re.sub(r'\bt\b', 'together', user_command_message_content)
                            user_command_message_content = re.sub(r'\ba\b', 'alone', user_command_message_content)
                            user_command_message_content = re.sub(r'\bo\b', 'old', user_command_message_content)
                            if 'hardmode'in user_command_message_content.lower(): hardmode = True
                            if 'together'in user_command_message_content.lower(): together = True
                            if 'alone' in user_command_message_content.lower(): alone = True
                            if 'old' in user_command_message_content.lower(): old = True
                            last_hunt_mode = ''
                            if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                            if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                            if old: last_hunt_mode = f'{last_hunt_mode} old'
                            last_hunt_mode = last_hunt_mode.strip()
                            if last_hunt_mode == '': last_hunt_mode = None
                    await user_settings.update(last_hunt_mode=last_hunt_mode)
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.edited_at if message.edited_at else message.created_at
                time_elapsed = current_time - bot_answer_time
                if together:
                    monsters_christmas = [
                        '**Elf**',
                        '**Christmas Reindeer**',
                        '**Snowman**',
                        '**Krampus**',
                        '**Yeti**',
                        '**Hyper Giant Ice Block**',
                    ]
                    partner_start_pos = message_content.find(f'**{partner_name}**:')
                    if partner_start_pos == -1:
                        partner_start_pos = message_content.find(f'while **{partner_name}**')
                    message_content_partner = message_content[partner_start_pos:]
                    for monster in monsters_christmas:
                        if monster.lower() in message_content_partner.lower():
                            partner_christmas_area = True
                            break
                donor_tier = user_settings.user_donor_tier
                donor_tier = 3 if donor_tier > 3 else donor_tier
                donor_tier_partner_hunt = user_settings.partner_donor_tier
                donor_tier_partner_hunt = 3 if donor_tier_partner_hunt > 3 else donor_tier_partner_hunt
                actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                if cooldown.donor_affected:
                    time_left_seconds = (actual_cooldown
                                         * settings.DONOR_COOLDOWNS[donor_tier]
                                         - floor(time_elapsed.total_seconds()))
                    time_left_seconds_partner_hunt = (actual_cooldown
                                                      * settings.DONOR_COOLDOWNS[donor_tier_partner_hunt]
                                                      - floor(time_elapsed.total_seconds()))
                else:
                    time_left_seconds = time_left_seconds_partner_hunt = actual_cooldown - floor(time_elapsed.total_seconds())
                    
                if user_settings.christmas_area_enabled:
                    time_left_seconds *= settings.CHRISTMAS_AREA_MULTIPLIER
                if user_settings.round_card_active:
                    time_left_seconds *= settings.ROUND_CARD_MULTIPLIER                    
                if user_settings.potion_flask_active:
                    time_left_seconds *= settings.POTION_FLASK_MULTIPLIER
                    
                if together and partner_christmas_area:
                    time_left_seconds_partner_hunt *= settings.CHRISTMAS_AREA_MULTIPLIER
                if together and partner is not None:
                    if partner.round_card_active:
                        time_left_seconds_partner_hunt *= settings.ROUND_CARD_MULTIPLIER                    
                    if partner.potion_flask_active:
                        time_left_seconds_partner_hunt *= settings.POTION_FLASK_MULTIPLIER
                    if partner.chocolate_box_unlocked:
                        time_left_seconds_partner_hunt *= settings.CHOCOLATE_BOX_MULTIPLIER

                partner_hunt_multiplier = partner.alert_hunt.multiplier if partner is not None else 1
                chocolate_box_multiplier = chocolate_box_multiplier_partner = 1
                pocket_watch_multiplier = 1 - (1.535 * (1 - user_settings.user_pocket_watch_multiplier))
                pocket_watch_multiplier_partner = 1 - (1.535 * (1 - user_settings.partner_pocket_watch_multiplier))
                if user_settings.chocolate_box_unlocked:
                    chocolate_box_multiplier = settings.CHOCOLATE_BOX_MULTIPLIER
                if partner is not None:
                    if partner.chocolate_box_unlocked:
                        chocolate_box_multiplier_partner = settings.CHOCOLATE_BOX_MULTIPLIER
                time_left = timedelta(seconds=(time_left_seconds * user_settings.alert_hunt.multiplier
                                      * pocket_watch_multiplier * chocolate_box_multiplier))
                time_left_partner_hunt = timedelta(seconds=(time_left_seconds_partner_hunt * partner_hunt_multiplier
                                                   * user_settings.alert_hunt_partner.multiplier
                                                   * pocket_watch_multiplier_partner * chocolate_box_multiplier_partner))
                await user_settings.update(hunt_end_time=current_time + time_left)
                if user_settings.hunt_reminders_combined and together:
                    time_left = max(time_left, time_left_partner_hunt)
                reminder_created = False
                if user_settings.alert_hunt.enabled and time_left >= timedelta(0):
                    reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                             message.channel.id, reminder_message)
                    )
                    reminder_created = True
                if (user_settings.alert_hunt_partner.enabled and time_left_partner_hunt >= timedelta(0) and together
                    and not user_settings.hunt_reminders_combined and user_settings.partner_name is not None):
                    reminder_message = (user_settings.alert_hunt_partner.message.replace('{command}', hunt_command)
                                        .replace('{partner}', user_settings.partner_name))
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt-partner', time_left_partner_hunt,
                                                             message.channel.id, reminder_message)
                    )
                    reminder_created = True
                if reminder_created:
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'hunt'))
                    await functions.add_reminder_reaction(message, reminder, user_settings)
                partner_start = len(message_content)
                if together and partner is not None:
                    await partner.update(partner_hunt_end_time=current_time + time_left_partner_hunt)
                    if partner_alerts_enabled:
                        partner_discord = await functions.get_discord_user(self.bot, user_settings.partner_id)
                        partner_global_name = partner_discord.global_name if partner_discord.global_name is not None else partner_discord.name
                        # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
                        alert_items = {
                            'MEGA present': emojis.PRESENT_MEGA,
                            'ULTRA present': emojis.PRESENT_ULTRA,
                            'OMEGA present': emojis.PRESENT_OMEGA,
                            'GODLY present': emojis.PRESENT_GODLY,
                            'VOID present': emojis.PRESENT_VOID,
                            'easter lootbox': emojis.LB_EASTER,
                        }
                        for lootbox in list(strings.LOOTBOXES.keys())[partner.partner_alert_threshold:]:
                            alert_items[lootbox] = strings.LOOTBOXES[lootbox]
                        search_strings = [
                            f'**{user_settings.partner_name}** got ', #English
                            f'**{user_settings.partner_name}** consiguió ', #Spanish
                            f'**{user_settings.partner_name}** conseguiu ', #Portuguese
                        ]
                        for search_string in search_strings:
                            partner_loot_start = message_content.find(search_string)
                            if partner_loot_start != -1: break
                        if partner_loot_start == -1:
                            partner_loot_start = message_content.find(f'**{user_settings.partner_name}**:')
                        if partner_loot_start != -1:
                            partner_start = partner_loot_start
                        lb_search_content = message_content[partner_start:]
                        lootbox_alert = ''
                        for lb_name, lb_emoji in alert_items.items():
                            try:
                                search_patterns = [
                                    fr"\+(.+?) (.+?) {re.escape(lb_name)}", #All languages
                                    fr"\*\* got (.+?) (.+?) {re.escape(lb_name)}", #English
                                    fr"\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) {re.escape(lb_name)}", #Spanish, Portuguese
                                ]
                                lb_match = await functions.get_match_from_patterns(search_patterns, lb_search_content)
                                if not lb_match: continue
                                lb_amount = lb_match.group(1)
                            except:
                                await errors.log_error(
                                    f'Error when looking for partner lootbox in: {lb_search_content}',
                                    message
                                )
                                return
                            partner_message = (partner.alert_partner.message
                                               .replace('{partner}', user_global_name)
                                               .replace('{loot}', f'{lb_amount} {lb_emoji} {lb_name}'))
                            if lootbox_alert == '':
                                lootbox_alert = partner_message
                            else:
                                f'{lootbox_alert}\nAlso: {partner_message}'
                        lootbox_alert = lootbox_alert.strip()
                        if lootbox_alert != '':
                            try:
                                channel = await functions.get_discord_channel(self.bot, partner.partner_channel_id)
                                if channel is not None:
                                    if partner.dnd_mode_enabled:
                                        lb_message = lootbox_alert.replace('{name}', f'**{partner_global_name}**')
                                    else:
                                        lb_message = lootbox_alert.replace('{name}', partner_discord.mention)
                                    await channel.send(lb_message)
                                    if user_settings.reactions_enabled: await message.add_reaction(emojis.PARTNER_ALERT)
                            except discord.errors.Forbidden:
                                return
                            except Exception as error:
                                await errors.log_error(
                                    f'Had the following error while trying to send the partner alert:\n{error}',
                                    message
                                )

                # Add reactions
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'omega lootbox': emojis.PANDA_SURPRISE,
                        'godly lootbox': emojis.PANDA_SURPRISE,
                        'void lootbox': emojis.PANDA_SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if (stuff_name in message_content.lower()) and (message_content.lower().rfind(stuff_name) < partner_start):
                            await message.add_reaction(stuff_emoji)
                    search_strings = [
                        f'**{user.name}** lost but ', #English 1
                        'but lost fighting', #English 2
                        'both lost fighting', #English 3
                        f'**{user.name}** perdió pero ', #Spanish 1
                        'pero perdió luchando', #Spanish 2
                        'ambos perdieron luchando', #Spanish 3
                        f'**{user.name}** perdeu, mas ', #Portuguese 1
                        'mais perdeu a luta', #Portuguese 2
                        'ambos perderam a luta', #Portuguese 3, UNCONFIRMED
                    ]
                    if any(search_string in message_content.lower() for search_string in search_strings):
                        await message.add_reaction(emojis.RIP)
                    if 'horslime' in message_content.lower():
                        await message.add_reaction(emojis.PANDA_EWW)

            # Hunt event non-slash (always English)
            search_strings = [
                'pretends to be a zombie',
                'fights the horde',
                'thankfully, the horde did not notice',
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                interaction = await functions.get_interaction_user(message)
                if interaction is None:
                    user_name = user_command = last_hunt_mode = user_command_message = None
                    hardmode = together = alone = old = False
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_HUNT, user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in hunt event non-slash message.', message)
                        return
                    user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled: return
                    current_time = utils.utcnow()
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                    if not user_settings.alert_hunt.enabled: return
                    user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                    user_command_message_content = re.sub(r'\bt\b', 'together', user_command_message_content)
                    user_command_message_content = re.sub(r'\ba\b', 'alone', user_command_message_content)
                    user_command_message_content = re.sub(r'\bo\b', 'old', user_command_message_content)
                    if 'hardmode'in user_command_message_content.lower():
                        hardmode = True
                    if 'together'in user_command_message_content.lower():
                        together = True
                    if 'alone'in user_command_message_content.lower():
                        alone = True
                    if 'old'in user_command_message_content.lower():
                        old = True
                    last_hunt_mode = ''
                    if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                    if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                    if old: last_hunt_mode = f'{last_hunt_mode} old'
                    last_hunt_mode = last_hunt_mode.strip()
                    if last_hunt_mode == '': last_hunt_mode = None
                    await user_settings.update(last_hunt_mode=last_hunt_mode)
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.last_hunt_mode != '':
                        user_command = f'{user_command} `mode: {user_settings.last_hunt_mode}`'
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    bot_answer_time = message.edited_at if message.edited_at else message.created_at
                    time_elapsed = current_time - bot_answer_time
                    donor_tier = user_settings.user_donor_tier
                    donor_tier = 3 if donor_tier > 3 else donor_tier
                    if cooldown.donor_affected:
                        time_left_seconds = (cooldown.actual_cooldown_mention()
                                            * settings.DONOR_COOLDOWNS[donor_tier]
                                            - floor(time_elapsed.total_seconds()))
                    else:
                        time_left_seconds = actual_cooldown - floor(time_elapsed.total_seconds())
                    if user_settings.christmas_area_enabled: time_left_seconds *= settings.CHRISTMAS_AREA_MULTIPLIER
                    if user_settings.round_card_active: time_left_seconds *= settings.ROUND_CARD_MULTIPLIER
                    if user_settings.potion_flask_active: time_left_seconds *= settings.POTION_FLASK_MULTIPLIER
                    time_left = timedelta(seconds=time_left_seconds * user_settings.alert_hunt.multiplier
                                          * (1 - (1.535 * (1 - user_settings.user_pocket_watch_multiplier))))
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    await functions.add_reminder_reaction(message, reminder, user_settings)

            # Hunt event slash (all languages)
            if  ((':zombie' in message_content.lower() and '#2' in message_content.lower())
                    or ':crossed_swords:' in message_content.lower() or '⚔️' in message_content.lower()
                    or ':sweat_drops:' in message_content.lower() or '💦' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is not None:
                    if interaction.name != 'hunt': return
                    user = interaction.user
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled: return
                    current_time = utils.utcnow()
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                    if not user_settings.alert_hunt.enabled: return
                    bot_answer_time = message.edited_at if message.edited_at else message.created_at
                    time_elapsed = current_time - bot_answer_time
                    together = True if user_settings.partner_id is not None else False
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.last_hunt_mode != '':
                        if user_settings.slash_mentions_enabled:
                            user_command = f"{user_command} `mode: {user_settings.last_hunt_mode}`"
                        else:
                            user_command = f"{user_command} `{user_settings.last_hunt_mode}`".replace('` `', ' ')
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    donor_tier = user_settings.user_donor_tier
                    donor_tier = 3 if donor_tier > 3 else donor_tier
                    if cooldown.donor_affected:
                        time_left_seconds = (cooldown.actual_cooldown_slash()
                                            * settings.DONOR_COOLDOWNS[donor_tier]
                                            - floor(time_elapsed.total_seconds()))
                    else:
                        time_left_seconds = actual_cooldown - floor(time_elapsed.total_seconds())
                    time_left = timedelta(seconds=time_left_seconds * user_settings.alert_hunt.multiplier
                                          * (1 - (1.535 * (1 - user_settings.user_pocket_watch_multiplier))))
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                                message.channel.id, reminder_message)
                    )
                    asyncio.ensure_future(functions.call_ready_command(self.bot, message, user, user_settings, 'hunt'))
                    await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(HuntCog(bot))
