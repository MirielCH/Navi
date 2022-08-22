# hunt.py

from datetime import datetime, timedelta
import re

import discord
from discord.ext import commands

from database import cooldowns, errors, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings


class HuntCog(commands.Cog):
    """Cog that contains the hunt detection commands"""
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
                user_id = user_name = embed_user = user_command = last_hunt_mode = None
                slash_command = True
                hardmode = together = alone = new = False
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is None: slash_command = False
                user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
                if user_id_match:
                    user_id = int(user_id_match.group(1))
                else:
                    user_name_match = re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in hunt cooldown message.', message)
                        return
                if user_id is not None:
                    try:
                        embed_user = await message.guild.fetch_member(user_id)
                    except:
                        pass
                else:
                    embed_user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if embed_user is not None: user_id = embed_user.id
                if slash_command:
                    try:
                        user_settings: users.User = await users.get_user(interaction_user.id)
                    except exceptions.FirstTimeUserError:
                        return
                if not slash_command:
                    user_command_message, user_command = (
                        await functions.get_message_from_channel_history(
                            message.channel,
                            r"^rpg\s+hunt\b",
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the hunt cooldown message.', message)
                        return
                    interaction_user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(interaction_user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if user_settings.hunt_rotation_enabled and 'together' not in user_settings.last_hunt_mode:
                        together = True
                    for argument in user_command_message.content.lower().split():
                        if argument in ('h', 'hardmode') and 'hardmode' not in user_command:
                            hardmode = True
                        if argument in ('t', 'together') and 'together' not in user_command:
                            together = True
                            if user_settings.hunt_rotation_enabled and 'together' in user_settings.last_hunt_mode:
                                together = False
                        if argument in ('a', 'alone') and 'alone' not in user_command:
                            alone = True
                        if argument in ('n', 'new') and 'new' not in user_command:
                            new = True
                    if hardmode:
                        user_command = f'{user_command} hardmode'
                        last_hunt_mode = f'{last_hunt_mode} hardmode' if last_hunt_mode is not None else 'hardmode'
                    if together:
                        user_command = f'{user_command} together'
                        last_hunt_mode = f'{last_hunt_mode} together' if last_hunt_mode is not None else 'together'
                    if alone:
                        user_command = f'{user_command} alone'
                        last_hunt_mode = f'{last_hunt_mode} alone' if last_hunt_mode is not None else 'alone'
                    if new:
                        user_command = f'{user_command} new'
                        last_hunt_mode = f'{last_hunt_mode} new' if last_hunt_mode is not None else 'new'
                    user_command = f'`{user_command.strip()}`'
                if not user_settings.bot_enabled or not user_settings.alert_hunt.enabled: return
                if slash_command:
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                    if user_settings.last_hunt_mode != '':
                        user_command = f'{user_command} `mode: {user_settings.last_hunt_mode}`'
                if not slash_command and not user_settings.hunt_rotation_enabled:
                    await user_settings.update(last_hunt_mode=last_hunt_mode)
                timestring_match = await functions.get_match_from_patterns(strings.PATTERNS_COOLDOWN_TIMESTRING,
                                                                           message_title)
                if not timestring_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Timestring not found in hunt cooldown message.', message)
                    return
                timestring = timestring_match.group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                if time_left < timedelta(0): return
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
                if user_settings.hunt_rotation_enabled:
                    time_left = time_left - time_elapsed
                else:
                    cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                    partner_donor_tier = 3 if user_settings.partner_donor_tier > 3 else user_settings.partner_donor_tier
                    user_donor_tier = 3 if user_settings.user_donor_tier > 3 else user_settings.user_donor_tier
                    partner_cooldown = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[partner_donor_tier])
                    user_cooldown = (cooldown.actual_cooldown()
                                    * settings.DONOR_COOLDOWNS[user_donor_tier])
                    if (user_settings.partner_donor_tier < user_settings.user_donor_tier
                        and interaction_user == embed_user):
                        time_left_seconds = (time_left.total_seconds()
                                            + (partner_cooldown - user_cooldown)
                                            - time_elapsed.total_seconds()
                                            + 1)
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
                'encontr', #Spanish, Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)):
                user_name = partner_name = last_hunt_mode = None
                hardmode = together = alone = event_mob = found_together = False
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
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
                new = True if '__**' in message_content.lower() else False
                if 'horslime' in message_content.lower():
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
                        user_name = await functions.encode_text(user_name_match.group(1))
                        partner_name = user_name_match.group(2)
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    search_patterns = [
                        r"\*\*(.+?)\*\* found a", #English
                        r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = await functions.encode_text(user_name_match.group(1))
                        if user_name != 'Both players': # Needs to be updated when an event hits that uses this
                            user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    user_command_message, _ = (
                        await functions.get_message_from_channel_history(message.channel, r"^rpg\s+hunt\b")
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in hunt message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if found_together: await user_settings.update(partner_name=partner_name)
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                if not user_settings.alert_hunt.enabled: return
                if not slash_command:
                    user_command = 'rpg hunt'
                else:
                    user_command = await functions.get_slash_command(user_settings, 'hunt')
                arguments = ''
                if user_settings.hunt_rotation_enabled: together = not found_together
                if not event_mob:
                    if hardmode:
                        arguments = f'{arguments} hardmode'
                    if together:
                        arguments = f'{arguments} together'
                    if alone:
                        arguments = f'{arguments} alone'
                    if new and together:
                        arguments = f'{arguments} new'
                    if arguments != '':
                        last_hunt_mode = arguments.strip()
                        if slash_command:
                            user_command = f'{user_command} `mode: {arguments.strip()}`'
                        else:
                            user_command = f'{user_command} {arguments.strip()}'
                    if not slash_command: user_command = f'`{user_command}`'
                if event_mob:
                    if slash_command:
                        user_command = await functions.get_slash_command(user_settings, 'hunt')
                        if user_settings.last_hunt_mode is not None:
                          user_command = f'{user_command} `mode: {user_settings.last_hunt_mode}`'
                        elif together:
                            user_command = f'{user_command} `mode: together`'
                    else:
                        user_command_message, _ = (
                            await functions.get_message_from_channel_history(
                                message.channel, r"^rpg\s+hunt\b", user
                            )
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find a command for the hunt event mob message.', message)
                            return
                        user_command = 'rpg hunt'
                        for argument in user_command_message.content.lower().split():
                            if argument in ('h', 'hardmode'):
                                hardmode = True
                            if argument in ('t', 'together'):
                                together = False if user_settings.hunt_rotation_enabled else True
                            if argument in ('a', 'alone'):
                                alone = True
                        if hardmode:
                            user_command = f'{user_command} hardmode'
                            last_hunt_mode = f'{last_hunt_mode} hardmode' if last_hunt_mode is not None else 'hardmode'
                        if together:
                            user_command = f'{user_command} together'
                            last_hunt_mode = f'{last_hunt_mode} together' if last_hunt_mode is not None else 'together'
                        if alone:
                            user_command = f'{user_command} alone'
                            last_hunt_mode = f'{last_hunt_mode} alone' if last_hunt_mode is not None else 'alone'
                        user_command = f'`{user_command.strip()}`'
                await user_settings.update(last_hunt_mode=last_hunt_mode)
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier
                    and not user_settings.hunt_rotation_enabled):
                    donor_tier = user_settings.partner_donor_tier
                else:
                    donor_tier = user_settings.user_donor_tier
                donor_tier = 3 if donor_tier > 3 else donor_tier
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)
                partner_start = len(message_content)
                if user_settings.partner_id is not None:
                    partner: users.User = await users.get_user(user_settings.partner_id)
                    partner_discord = await functions.get_discord_user(self.bot, user_settings.partner_id)
                    # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
                    if found_together:
                        lootboxes = {
                            'common lootbox': emojis.LB_COMMON,
                            'uncommon lootbox': emojis.LB_UNCOMMON,
                            'rare lootbox': emojis.LB_RARE,
                            'EPIC lootbox': emojis.LB_EPIC,
                            'EDGY lootbox': emojis.LB_EDGY,
                            'OMEGA lootbox': emojis.LB_OMEGA,
                            'MEGA present': emojis.PRESENT_MEGA,
                            'ULTRA present': emojis.PRESENT_ULTRA,
                            'OMEGA present': emojis.PRESENT_OMEGA,
                            'GODLY present': emojis.PRESENT_GODLY,
                            'easter lootbox': emojis.EASTER_LOOTBOX,
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
                                               .replace('{user}', user.name)
                                               .replace('{loot}', f'{lb_amount} {lb_emoji} {lb_name}'))
                            if lootbox_alert == '':
                                lootbox_alert = partner_message
                            else:
                                f'{lootbox_alert}\nAlso: {partner_message}'
                        lootbox_alert = lootbox_alert.strip()
                        if (partner.partner_channel_id is not None
                            and partner.alert_partner.enabled
                            and partner.bot_enabled
                            and lootbox_alert != ''):
                            try:
                                if partner.dnd_mode_enabled:
                                    lb_message = f'**{partner_discord.name}**, {lootbox_alert}'
                                else:
                                    if partner.ping_after_message:
                                        lb_message = f'{lootbox_alert} {partner_discord.mention}'
                                    else:
                                        lb_message = f'{partner_discord.mention} {lootbox_alert}'
                                channel = await functions.get_discord_channel(self.bot, partner.partner_channel_id)
                                await channel.send(lb_message)
                                if user_settings.reactions_enabled: await message.add_reaction(emojis.PARTNER_ALERT)
                            except Exception as error:
                                await errors.log_error(
                                    f'Had the following error while trying to send the partner alert:\n{error}',
                                    message
                                )
                    if (found_together and partner.hardmode_mode_enabled and not event_mob
                        and not user_settings.hunt_rotation_enabled):
                        hm_message = (
                            f'**{partner_discord.name}** is currently **hardmoding**.\n'
                            f'If you want to hardmode too, please activate hardmode mode and hunt solo.'
                        )
                        if user_settings.dnd_mode_enabled:
                            hm_message = f'**{user.name}**, {hm_message}'
                        else:
                            if user_settings.ping_after_message:
                                hm_message = f'{hm_message} {user.mention}'
                            else:
                                hm_message = f'{user.mention} {hm_message}'
                        await message.channel.send(hm_message)
                    elif (not found_together and not partner.hardmode_mode_enabled and not event_mob
                          and not user_settings.hunt_rotation_enabled):
                        partner_discord = await functions.get_discord_user(self.bot, user_settings.partner_id)
                        hm_message = (
                            f'**{partner_discord.name}** is not hardmoding, '
                            f'feel free to take them hunting.'
                        )
                        if user_settings.dnd_mode_enabled:
                            hm_message = f'**{user.name}**, {hm_message}'
                        else:
                            if user_settings.ping_after_message:
                                hm_message = f'{hm_message} {user.mention}'
                            else:
                                hm_message = f'{user.mention} {hm_message}'
                        await message.channel.send(hm_message)
                # Add reactions
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'OMEGA lootbox': emojis.SURPRISE,
                        'GODLY lootbox': emojis.SURPRISE,
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
                if interaction is not None: return
                user_name = user_command = last_hunt_mode = None
                hardmode = together = found_together = alone = new = False
                user_name_match = re.search(strings.REGEX_NAME_FROM_MESSAGE, message_content)
                if user_name_match:
                    user_name = await functions.encode_text(user_name_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await('User not found in hunt event non-slash message.', message)
                    return
                user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in hunt event non-slash message.', message)
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                if not user_settings.alert_hunt.enabled: return
                user_command_message, user_command = (
                        await functions.get_message_from_channel_history(
                            message.channel, r"^rpg\s+hunt\b", user
                        )
                    )
                if user_command_message is None:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find a command for the hunt event non-slash message.', message)
                    return
                if user_settings.hunt_rotation_enabled and 'together' not in user_settings.last_hunt_mode:
                    together = True
                for argument in user_command_message.content.lower().split():
                    if argument in ('h', 'hardmode'):
                        hardmode = True
                    if argument in ('t', 'together'):
                        found_together = True
                        together = False if user_settings.hunt_rotation_enabled else True
                    if argument in ('a', 'alone'):
                        alone = True
                if hardmode:
                    user_command = f'{user_command} hardmode'
                    last_hunt_mode = f'{last_hunt_mode} hardmode' if last_hunt_mode is not None else 'hardmode'
                if together:
                    user_command = f'{user_command} together'
                    last_hunt_mode = f'{last_hunt_mode} together' if last_hunt_mode is not None else 'together'
                if alone:
                    user_command = f'{user_command} alone'
                    last_hunt_mode = f'{last_hunt_mode} alone' if last_hunt_mode is not None else 'alone'
                user_command = f'`{user_command}`'
                await user_settings.update(last_hunt_mode=last_hunt_mode)
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
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

            # Hunt event slash (all languages)
            if  (('<:zombie' in message_content.lower() and '#2' in message_content.lower())
                 or ':crossed_swords:' in message_content.lower()
                 or ':sweat_drops:' in message_content.lower()):
                user_name = user_command = None
                interaction = await functions.get_interaction(message)
                if interaction is None: return
                if interaction.name != 'hunt': return
                user = interaction.user
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                user_command = await functions.get_slash_command(user_settings, 'hunt')
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                if not user_settings.alert_hunt.enabled: return
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                together = found_together = True if user_settings.partner_id is not None else False
                if user_settings.hunt_rotation_enabled:
                    together = False if 'together' in user_settings.last_hunt_mode else True
                if (found_together and user_settings.partner_donor_tier < user_settings.user_donor_tier
                    and not user_settings.hunt_rotation_enabled):
                    donor_tier = user_settings.partner_donor_tier
                else:
                    donor_tier = user_settings.user_donor_tier
                donor_tier = 3 if donor_tier > 3 else donor_tier
                if cooldown.donor_affected:
                    time_left_seconds = (cooldown.actual_cooldown()
                                        * settings.DONOR_COOLDOWNS[donor_tier]
                                        - time_elapsed.total_seconds())
                else:
                    time_left_seconds = cooldown.actual_cooldown() - time_elapsed.total_seconds()
                time_left = timedelta(seconds=time_left_seconds)
                if time_left < timedelta(0): return
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                if user_settings.auto_ready_enabled: await functions.call_ready_command(self.bot, message, user)


# Initialization
def setup(bot):
    bot.add_cog(HuntCog(bot))