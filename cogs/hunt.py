# hunt.py

import asyncio
from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from cache import messages
from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, regex, settings, strings


class HuntCog(commands.Cog):
    """Cog that contains the hunt detection commands"""
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
            message_author = message_title = icon_url = ''
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url
            if embed.title: message_title = str(embed.title)

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
                        embed_users = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user_name_match is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Embed user not found in hunt cooldown message.', message)
                        return
                if not slash_command:
                    user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                    user_command_message_content = re.sub(r'\bt\b', 'together', user_command_message_content)
                    user_command_message_content = re.sub(r'\ba\b', 'alone', user_command_message_content)
                    user_command_message_content = re.sub(r'\bo\b', 'old', user_command_message_content)
                    if user_settings.hunt_rotation_enabled and 'together' not in user_settings.last_hunt_mode:
                        together = True
                    if 'hardmode'in user_command_message_content.lower():
                        hardmode = True
                    if 'together'in user_command_message_content.lower():
                        together = True
                        if user_settings.hunt_rotation_enabled and 'together' in user_settings.last_hunt_mode:
                            together = False
                    if 'alone'in user_command_message_content.lower():
                        alone = True
                    if 'old'in user_command_message_content.lower():
                        old = True
                    last_hunt_mode = ''
                    if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                    if together: last_hunt_mode = f'{last_hunt_mode} together'
                    if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                    if old: last_hunt_mode = f'{last_hunt_mode} old'
                    last_hunt_mode = last_hunt_mode.strip()
                    if not user_settings.hunt_rotation_enabled:
                        if last_hunt_mode == '': last_hunt_mode = None
                        await user_settings.update(last_hunt_mode=last_hunt_mode)
                if not user_settings.bot_enabled or not user_settings.alert_hunt.enabled: return
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
                time_left_seconds = time_left.total_seconds()
                if time_left < timedelta(0): return
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                if user_settings.hunt_rotation_enabled:
                    time_left = time_left - time_elapsed
                    #if user_settings.christmas_area_enabled:
                    #    time_left_seconds *= 0.9
                    time_left_seconds *= user_settings.alert_hunt.multiplier
                else:
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                    partner_donor_tier = 3 if user_settings.partner_donor_tier > 3 else user_settings.partner_donor_tier
                    user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                    partner_cooldown = (actual_cooldown
                                        * settings.DONOR_COOLDOWNS[partner_donor_tier])
                    user_cooldown = (actual_cooldown
                                    * settings.DONOR_COOLDOWNS[user_donor_tier]
                                    * user_settings.alert_hunt.multiplier)
                    if (user_settings.partner_donor_tier < user_settings.user_donor_tier
                        and interaction_user in embed_users):
                        time_left_seconds = (time_left_seconds
                                            + (partner_cooldown - user_cooldown)
                                            - time_elapsed.total_seconds()
                                            + 1)
                        #if user_settings.christmas_area_enabled: time_left_seconds *= 0.9
                time_left = timedelta(seconds=time_left_seconds)
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                overwrite_message = False if user_settings.hunt_rotation_enabled else True
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message,
                                                         overwrite_message=overwrite_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
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
                    or 'pink wolf' in message_content.lower()
                )
            ):
                user_name = partner_name = last_hunt_mode = user_command_message = partner = None
                hardmode = together = alone = event_mob = found_together = partner_alerts_enabled = False
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
                    together = found_together = True
                if any(search_string in message_content.lower() for search_string in search_strings_alone):
                    alone = True
                old = True if '__**' not in message_content.lower() else False
                search_strings_event_mobs = [
                    'horslime',
                    'christmas slime',
                    'pink wolf',
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_event_mobs):
                    search_strings_together = [
                        'both players', #English
                    ]
                    if any(search_string in message_content.lower() for search_string in search_strings_together):
                        together = found_together = True
                    event_mob = True
                if found_together:
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
                        if user_name == 'Both players': # Needs to be updated when an event hits that uses this
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
                if found_together:
                    await user_settings.update(partner_name=partner_name)
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                if user_settings.partner_id is not None:
                    partner: users.User = await users.get_user(user_settings.partner_id)
                    if partner.partner_channel_id is not None and partner.alert_partner.enabled and partner.bot_enabled:
                        partner_alerts_enabled = True
                if not user_settings.alert_hunt.enabled and not partner_alerts_enabled: return
                if user_settings.alert_hunt.enabled:
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    last_hunt_mode = ''
                    if user_settings.hunt_rotation_enabled: together = not found_together
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
                            if 'hardmode'in user_command_message_content.lower():
                                hardmode = True
                            if 'together'in user_command_message_content.lower():
                                together = True
                                if user_settings.hunt_rotation_enabled and 'together' in user_settings.last_hunt_mode:
                                    together = False
                            if 'alone'in user_command_message_content.lower():
                                alone = True
                            if 'old'in user_command_message_content.lower():
                                old = True
                            last_hunt_mode = ''
                            if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                            if together: last_hunt_mode = f'{last_hunt_mode} together'
                            if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                            if old: last_hunt_mode = f'{last_hunt_mode} old'
                            last_hunt_mode = last_hunt_mode.strip()
                            if last_hunt_mode == '': last_hunt_mode = None
                    await user_settings.update(last_hunt_mode=last_hunt_mode)
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                if found_together:
                    monsters_christmas = [
                        '**Elf**',
                        '**Christmas Reindeer**',
                        '**Snowman**',
                        'Krampus',
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
                if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier):
                    donor_tier_partner_hunt = user_settings.partner_donor_tier
                    if not user_settings.hunt_rotation_enabled:
                        donor_tier = user_settings.partner_donor_tier
                    else:
                        donor_tier = user_settings.user_donor_tier
                else:
                    donor_tier = donor_tier_partner_hunt = user_settings.user_donor_tier
                donor_tier = 3 if donor_tier > 3 else donor_tier
                donor_tier_partner_hunt = 3 if donor_tier_partner_hunt > 3 else donor_tier_partner_hunt
                actual_cooldown = cooldown.actual_cooldown_slash() if slash_command else cooldown.actual_cooldown_mention()
                if cooldown.donor_affected:
                    time_left_seconds = (actual_cooldown
                                        * settings.DONOR_COOLDOWNS[donor_tier]
                                        - time_elapsed.total_seconds())
                    time_left_seconds_partner_hunt = (actual_cooldown
                                                    * settings.DONOR_COOLDOWNS[donor_tier_partner_hunt]
                                                    - time_elapsed.total_seconds())
                else:
                    time_left_seconds = time_left_seconds_partner_hunt = actual_cooldown - time_elapsed.total_seconds()
                #if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier
                #    and user_settings.partner_donor_tier < 3 and partner_christmas_area):
                #    time_left_seconds *= 0.9
                #elif user_settings.christmas_area_enabled and not found_together:
                #    time_left_seconds *= 0.9
                #elif (user_settings.christmas_area_enabled and not partner_christmas_area
                #      and user_settings.hunt_rotation_enabled and found_together):
                #    time_left_seconds *= 0.9
                #elif user_settings.christmas_area_enabled and partner_christmas_area and found_together:
                #    time_left_seconds *= 0.9
                time_left = timedelta(seconds=time_left_seconds * user_settings.alert_hunt.multiplier)
                time_left_partner_hunt = timedelta(seconds=time_left_seconds_partner_hunt)
                if time_left < timedelta(0): return
                if user_settings.alert_hunt.enabled:
                    reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                            message.channel.id, reminder_message)
                    )
                    if user_settings.auto_ready_enabled:
                        asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                    await functions.add_reminder_reaction(message, reminder, user_settings)
                partner_start = len(message_content)
                if found_together and partner is not None:
                    await partner.update(partner_hunt_end_time=current_time + time_left_partner_hunt)
                    if partner_alerts_enabled:
                        partner_discord = await functions.get_discord_user(self.bot, user_settings.partner_id)
                        # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
                        lootboxes = {
                            'common lootbox': emojis.LB_COMMON,
                            'uncommon lootbox': emojis.LB_UNCOMMON,
                            'rare lootbox': emojis.LB_RARE,
                            'EPIC lootbox': emojis.LB_EPIC,
                            'EDGY lootbox': emojis.LB_EDGY,
                            'OMEGA lootbox': emojis.LB_OMEGA,
                            'GODLY lootbox': emojis.LB_GODLY,
                            'VOID lootbox': emojis.LB_VOID,
                            'MEGA present': emojis.PRESENT_MEGA,
                            'ULTRA present': emojis.PRESENT_ULTRA,
                            'OMEGA present': emojis.PRESENT_OMEGA,
                            'GODLY present': emojis.PRESENT_GODLY,
                            'VOID present': emojis.PRESENT_VOID,
                            'easter lootbox': emojis.LB_EASTER,
                            'EPIC berry': emojis.EPIC_BERRY,
                        }
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
                        for lb_name, lb_emoji in lootboxes.items():
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
                                               .replace('{partner}', user.name)
                                               .replace('{loot}', f'{lb_amount} {lb_emoji} {lb_name}'))
                            if lootbox_alert == '':
                                lootbox_alert = partner_message
                            else:
                                f'{lootbox_alert}\nAlso: {partner_message}'
                        lootbox_alert = lootbox_alert.strip()
                        if lootbox_alert != '':
                            try:
                                if partner.dnd_mode_enabled:
                                    lb_message = lootbox_alert.replace('{name}', f'**{partner_discord.name}**')
                                else:
                                    lb_message = lootbox_alert.replace('{name}', partner_discord.mention)
                                channel = await functions.get_discord_channel(self.bot, partner.partner_channel_id)
                                await channel.send(lb_message)
                                if user_settings.reactions_enabled: await message.add_reaction(emojis.PARTNER_ALERT)
                            except Exception as error:
                                await errors.log_error(
                                    f'Had the following error while trying to send the partner alert:\n{error}',
                                    message
                                )

                # Add reactions
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'OMEGA lootbox': emojis.PANDA_SURPRISE,
                        'GODLY lootbox': emojis.PANDA_SURPRISE,
                        'VOID lootbox': emojis.PANDA_SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if (stuff_name in message_content) and (message_content.rfind(stuff_name) < partner_start):
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
                    if any(search_string in message_content for search_string in search_strings):
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
                    hardmode = together = found_together = alone = old = False
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
                    current_time = datetime.utcnow().replace(microsecond=0)
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                    if not user_settings.alert_hunt.enabled: return
                    if user_settings.hunt_rotation_enabled and 'together' not in user_settings.last_hunt_mode:
                        together = True
                    user_command_message_content = re.sub(r'\bh\b', 'hardmode', user_command_message.content.lower())
                    user_command_message_content = re.sub(r'\bt\b', 'together', user_command_message_content)
                    user_command_message_content = re.sub(r'\ba\b', 'alone', user_command_message_content)
                    user_command_message_content = re.sub(r'\bo\b', 'old', user_command_message_content)
                    if user_settings.hunt_rotation_enabled and 'together' not in user_settings.last_hunt_mode:
                        together = True
                    if 'hardmode'in user_command_message_content.lower():
                        hardmode = True
                    if 'together'in user_command_message_content.lower():
                        together = True
                        if user_settings.hunt_rotation_enabled and 'together' in user_settings.last_hunt_mode:
                            together = False
                    if 'alone'in user_command_message_content.lower():
                        alone = True
                    if 'old'in user_command_message_content.lower():
                        old = True
                    last_hunt_mode = ''
                    if hardmode: last_hunt_mode = f'{last_hunt_mode} hardmode'
                    if together: last_hunt_mode = f'{last_hunt_mode} together'
                    if alone: last_hunt_mode = f'{last_hunt_mode} alone'
                    if old: last_hunt_mode = f'{last_hunt_mode} old'
                    last_hunt_mode = last_hunt_mode.strip()
                    if last_hunt_mode == '': last_hunt_mode = None
                    await user_settings.update(last_hunt_mode=last_hunt_mode)
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.last_hunt_mode != '':
                        user_command = f'{user_command} `mode: {user_settings.last_hunt_mode}`'
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                    time_elapsed = current_time - bot_answer_time
                    together = True if user_settings.partner_id is not None else False
                    if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier
                        and not user_settings.hunt_rotation_enabled):
                        donor_tier = user_settings.partner_donor_tier
                    else:
                        donor_tier = user_settings.user_donor_tier
                    donor_tier = 3 if donor_tier > 3 else donor_tier
                    if cooldown.donor_affected:
                        time_left_seconds = (cooldown.actual_cooldown_mention()
                                            * settings.DONOR_COOLDOWNS[donor_tier]
                                            - time_elapsed.total_seconds())
                    else:
                        time_left_seconds = actual_cooldown - time_elapsed.total_seconds()
                    #if user_settings.christmas_area_enabled: time_left_seconds *= 0.9
                    time_left = timedelta(seconds=time_left_seconds * user_settings.alert_hunt.multiplier)
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
                    current_time = datetime.utcnow().replace(microsecond=0)
                    if user_settings.tracking_enabled:
                        await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                    if not user_settings.alert_hunt.enabled: return
                    bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                    time_elapsed = current_time - bot_answer_time
                    found_together = True if user_settings.partner_id is not None else False
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.hunt_rotation_enabled:
                        if 'together' in user_settings.last_hunt_mode:
                            last_hunt_mode = user_settings.last_hunt_mode.replace('together','').replace(' ','')
                        else:
                            last_hunt_mode = f'{user_settings.last_hunt_mode} together'.strip()
                        await user_settings.update(last_hunt_mode=last_hunt_mode)
                    if user_settings.last_hunt_mode != '':
                        if user_settings.slash_mentions_enabled:
                            user_command = f"{user_command} `mode: {user_settings.last_hunt_mode}`"
                        else:
                            user_command = f"{user_command} `{user_settings.last_hunt_mode}`".replace('` `', ' ')
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier
                        and not user_settings.hunt_rotation_enabled):
                        donor_tier = user_settings.partner_donor_tier
                    else:
                        donor_tier = user_settings.user_donor_tier
                    donor_tier = 3 if donor_tier > 3 else donor_tier
                    if cooldown.donor_affected:
                        time_left_seconds = (cooldown.actual_cooldown_slash()
                                            * settings.DONOR_COOLDOWNS[donor_tier]
                                            - time_elapsed.total_seconds())
                    else:
                        time_left_seconds = actual_cooldown - time_elapsed.total_seconds()
                    time_left = timedelta(seconds=time_left_seconds * user_settings.alert_hunt.multiplier)
                    if time_left < timedelta(0): return
                    reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                    reminder: reminders.Reminder = (
                        await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                                message.channel.id, reminder_message)
                    )
                    if user_settings.auto_ready_enabled:
                        asyncio.ensure_future(functions.call_ready_command(self.bot, message, user))
                    await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(HuntCog(bot))