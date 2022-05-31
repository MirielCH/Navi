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
            if 'you have already looked around' in message_title.lower():
                user_id = user_name = embed_user = user_command = None
                interaction_user = await functions.get_interaction_user(message)
                if interaction_user is not None: user_command = '/hunt'
                try:
                    user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
                except:
                    try:
                        user_name = re.search("^(.+?)'s cooldown", message_author).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in hunt cooldown message: {message.embeds[0].fields}',
                            message
                        )
                        return
                if user_id is not None:
                    try:
                        embed_user = await message.guild.fetch_member(user_id)
                    except:
                        pass
                else:
                    embed_user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if embed_user is not None: user_id = embed_user.id
                if user_command is None:
                    message_history = await message.channel.history(limit=50).flatten()
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if msg.content.lower().replace(' ','').startswith('rpghunt'):
                                user_command_message = msg
                                interaction_user = msg.author
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the hunt cooldown message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                    user_command = user_command[8:].strip()
                    arguments = ''
                    for argument in user_command.split():
                        if argument in ('h', 'hardmode') and 'hardmode' not in arguments:
                            arguments = f'{arguments} hardmode'
                        if argument in ('t', 'together') and 'together' not in arguments:
                            arguments = f'{arguments} together'
                        if argument in ('a', 'alone') and 'alone' not in arguments:
                            arguments = f'{arguments} alone'
                        if argument in ('n', 'new') and 'new' not in arguments:
                            arguments = f'{arguments} new'
                    user_command = f'rpg hunt {arguments.strip()}'
                try:
                    user_settings: users.User = await users.get_user(interaction_user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.alert_hunt.enabled: return
                timestring = re.search("wait at least \*\*(.+?)\*\*...", message_title).group(1)
                time_left = await functions.calculate_time_left_from_timestring(message, timestring)
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                current_time = datetime.utcnow().replace(microsecond=0)
                time_elapsed = current_time - bot_answer_time
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
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(interaction_user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)

        if not message.embeds:
            message_content = message.content
            # Hunt
            if ('found a' in message_content.lower()
                and any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)):
                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                hardmode = True if '(but stronger)' in message_content.lower() else False
                alone = True if '(way stronger!!!)' in message_content.lower() else False
                together = True if 'hunting together' in message_content.lower() else False
                new = True if '__**' in message_content.lower() else False
                if together:
                    name_search = re.search("\*\*(.+?)\*\* and \*\*(.+?)\*\*", message_content)
                    user_name = name_search.group(1)
                    user_name = await functions.encode_text(user_name)
                    partner_name = name_search.group(2)
                if user is None:
                    if not together:
                        user_name_search = re.search("\*\*(.+?)\*\* found a", message_content)
                        user_name = user_name_search.group(1)
                        user_name = await functions.encode_text(user_name)
                    if user_name != 'Both players':
                        user = await functions.get_guild_member_by_name(message.guild, user_name)
                    if user is None:
                        message_history = await message.channel.history(limit=50).flatten()
                        for msg in message_history:
                            if msg.content is not None:
                                if msg.content.lower().replace(' ','').startswith('rpghunt'):
                                    user = msg.author
                                    break
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in hunt message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if together: await user_settings.update(partner_name=partner_name)
                if not user_settings.bot_enabled: return
                current_time = datetime.utcnow().replace(microsecond=0)
                if user_settings.tracking_enabled:
                    await tracking.insert_log_entry(user.id, message.guild.id, 'hunt', current_time)
                if not user_settings.alert_hunt.enabled: return
                if not slash_command:
                    user_command = 'rpg hunt'
                else:
                    user_command = '/hunt'
                    if hardmode or alone or together: user_command = f'{user_command} mode:'
                if hardmode: user_command = f'{user_command} hardmode'
                if alone: user_command = f'{user_command} alone'
                if together: user_command = f'{user_command} together'
                if new: user_command = f'{user_command} new'
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                if together and user_settings.partner_donor_tier < user_settings.user_donor_tier:
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
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)
                partner_start = len(message_content)
                if user_settings.partner_id is not None:
                    partner: users.User = await users.get_user(user_settings.partner_id)
                    await self.bot.wait_until_ready()
                    partner_discord = self.bot.get_user(user_settings.partner_id)
                    # Check for lootboxes, hardmode and send alert. This checks for the set partner, NOT for the automatically detected partner, to prevent shit from happening
                    if together:
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
                        partner_start = message_content.find(f'**{user_settings.partner_name}** got ')
                        if partner_start == -1:
                            partner_start = message_content.find(f'**{user_settings.partner_name}**:')
                        lb_search_content = message_content[partner_start:]
                        lootbox_alert = ''
                        for lb_name, lb_emoji in lootboxes.items():
                            try:
                                lb_search = re.search(f"\*\* got (.+?) (.+?) {re.escape(lb_name)}", lb_search_content)
                                if lb_search is None:
                                    lb_search = re.search(f"\+(.+?) (.+?) {re.escape(lb_name)}", lb_search_content)
                                if lb_search is None:
                                    continue
                                lb_amount = lb_search.group(1)
                            except:
                                await errors.log_error(
                                    f'Error when looking for partner lootbox in: {lb_search_content}',
                                    message
                                )
                                return
                            partner_message = (partner.alert_partner.message
                                               .replace('{user}', user.name)
                                               .replace('{loot}', f'{lb_amount} {lb_emoji} {lb_name}'))
                            lootbox_alert = partner_message if lootbox_alert == '' else f'{lootbox_alert}\nAlso: {partner_message}'
                        lootbox_alert = lootbox_alert.strip()
                        if (partner.partner_channel_id is not None
                            and partner.alert_partner.enabled
                            and partner.bot_enabled
                            and lootbox_alert != ''):
                            try:
                                if partner.dnd_mode_enabled:
                                    lb_message = f'**{partner_discord.name}**, {lootbox_alert}'
                                else:
                                    lb_message = f'{partner_discord.mention} {lootbox_alert}'
                                await self.bot.wait_until_ready()
                                await self.bot.get_channel(partner.partner_channel_id).send(lb_message)
                                if user_settings.reactions_enabled: await message.add_reaction(emojis.PARTNER_ALERT)
                            except Exception as error:
                                await errors.log_error(
                                    f'Had the following error while trying to send the partner alert:\n{error}',
                                    message
                                )
                    if together and partner.hardmode_mode_enabled:
                        hm_message = user.mention if not user_settings.dnd_mode_enabled else f'**{user.name}**,'
                        hm_message = (
                            f'{hm_message} **{partner_discord.name}** is currently **hardmoding**.\n'
                            f'If you want to hardmode too, please activate hardmode mode and hunt solo.'
                        )
                        await message.channel.send(hm_message)
                    elif not together and not partner.hardmode_mode_enabled:
                        partner_discord = self.bot.get_user(user_settings.partner_id)
                        hm_message = user.mention if not user_settings.dnd_mode_enabled else f'**{user.name}**,'
                        hm_message = (
                            f'{hm_message} **{partner_discord.name}** is not hardmoding, '
                            f'feel free to take them hunting.'
                        )
                        await message.channel.send(hm_message)
                if user_settings.reactions_enabled:
                    found_stuff = {
                        'OMEGA lootbox': emojis.SURPRISE,
                        'GODLY lootbox': emojis.SURPRISE,
                    }
                    for stuff_name, stuff_emoji in found_stuff.items():
                        if (stuff_name in message_content) and (message_content.rfind(stuff_name) < partner_start):
                            await message.add_reaction(stuff_emoji)
                    # Add an F if the user died
                    if ((message_content.find(f'**{user.name}** lost but ') > -1)
                        or (message_content.find('but lost fighting') > -1)):
                        await message.add_reaction(emojis.RIP)

            # Hunt event
            if ('pretends to be a zombie' in message_content.lower()
                or 'fights the horde' in message_content.lower()
                or 'thankfully, the horde did not notice' in message_content.lower()):
                user_name = user_command = None
                user = await functions.get_interaction_user(message)
                if user is not None:
                    user_command = '/hunt'
                else:
                    try:
                        user_name = re.search("\*\*(.+?)\*\*", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await(
                            f'User not found in hunt event message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in hunt event message: {message_content}',
                        message
                    )
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
                message_history = await message.channel.history(limit=50).flatten()
                if user_command is None:
                    user_command_message = None
                    for msg in message_history:
                        if msg.content is not None:
                            if (msg.content.lower().startswith('rpg ') and 'hunt' in msg.content.lower()
                                and msg.author == user):
                                user_command_message = msg
                                break
                    if user_command_message is None:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            'Couldn\'t find a command for the hunt event message.',
                            message
                        )
                        return
                    user_command = user_command_message.content.lower()
                    user_command = user_command[8:].strip()
                    if 'h ' in user_command or user_command.endswith(' h'):
                        user_command = user_command.replace('h','hardmode')
                    if 't ' in user_command or user_command.endswith(' t'):
                        user_command = user_command.replace('t',' together')
                    if 'a ' in user_command or user_command.endswith(' a'):
                        user_command = user_command.replace('a',' alone')
                    user_command = " ".join(user_command.split())
                    user_command = f'rpg hunt {user_command}'
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown('hunt')
                bot_answer_time = message.created_at.replace(microsecond=0, tzinfo=None)
                time_elapsed = current_time - bot_answer_time
                together = True if user_settings.partner_id is not None else False
                if together and user_settings.partner_donor_tier < user_settings.user_donor_tier:
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
                reminder_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, 'hunt', time_left,
                                                         message.channel.id, reminder_message)
                )
                await functions.add_reminder_reaction(message, reminder, user_settings)


# Initialization
def setup(bot):
    bot.add_cog(HuntCog(bot))