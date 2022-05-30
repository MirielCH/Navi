# cooldowns.py

import re

import discord
from discord.ext import commands
from datetime import datetime

from database import errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class CooldownsCog(commands.Cog):
    """Cog that contains the cooldowns detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return

        if not message.embeds: return
        embed: discord.Embed = message.embeds[0]
        message_author = message_footer = message_fields = icon_url = ''
        if embed.author:
            message_author = str(embed.author.name)
            icon_url = embed.author.icon_url
        for field in embed.fields:
            message_fields = f'{message_fields}\n{str(field.value)}'.strip()
        if embed.footer: message_footer = str(embed.footer.text)

        if not 'check the short version of this command' in message_footer.lower(): return

        user_id = user_name = None
        user = await functions.get_interaction_user(message)
        slash_command = True if user is not None else False
        if user is None:
            try:
                user_id = int(re.search("avatars\/(.+?)\/", icon_url).group(1))
            except:
                try:
                    user_name = re.search("^(.+?)'s cooldowns", message_author).group(1)
                    user_name = await functions.encode_text(user_name)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in cooldown message: {message.embeds[0].fields}',
                        message
                    )
                    return
            if user_id is not None:
                user = await message.guild.fetch_member(user_id)
            else:
                user = await functions.get_guild_member_by_name(message.guild, user_name)
        if user is None:
            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                await message.add_reaction(emojis.WARNING)
            await errors.log_error(
                f'User not found in cooldowns message: {message.embeds[0].fields}',
                message
            )
            return
        try:
            user_settings: users.User = await users.get_user(user.id)
        except exceptions.FirstTimeUserError:
            return
        if not user_settings.bot_enabled: return
        cooldowns = []
        if user_settings.alert_daily.enabled:
            try:
                daily_search = re.search("Daily`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Daily cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if daily_search is not None:
                daily_timestring = daily_search.group(1)
                user_command = '/daily' if slash_command else 'rpg daily'
                daily_message = user_settings.alert_daily.message.replace('{command}', user_command)
                cooldowns.append(['daily', daily_timestring.lower(), daily_message])
        if user_settings.alert_weekly.enabled:
            try:
                weekly_search = re.search("Weekly`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Weekly cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if weekly_search is not None:
                weekly_timestring = weekly_search.group(1)
                user_command = '/weekly' if slash_command else 'rpg weekly'
                weekly_message = user_settings.alert_weekly.message.replace('{command}', user_command)
                cooldowns.append(['weekly', weekly_timestring.lower(), weekly_message])
        if user_settings.alert_lootbox.enabled:
            try:
                lb_search = re.search("Lootbox`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Lootbox cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if lb_search is not None:
                lb_timestring = lb_search.group(1)
                user_command = '/buy item: [lootbox]' if slash_command else 'rpg buy [lootbox]'
                lb_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                cooldowns.append(['lootbox', lb_timestring.lower(), lb_message])
        if user_settings.alert_adventure.enabled:
            if 'Adventure hardmode`**' in message_fields:
                adv_search_string = 'Adventure hardmode`\*\* \(\*\*(.+?)\*\*'
                adv_command = '/adventure mode: hardmode' if slash_command else 'rpg adventure hardmode'
            else:
                adv_search_string = 'Adventure`\*\* \(\*\*(.+?)\*\*'
                adv_command = '/adventure' if slash_command else 'rpg adventure'
            try:
                adv_search = re.search(adv_search_string, message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Adventure cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if adv_search is not None:
                adv_timestring = adv_search.group(1)
                adv_message = user_settings.alert_adventure.message.replace('{command}', adv_command)
                cooldowns.append(['adventure', adv_timestring.lower(), adv_message])
        if user_settings.alert_training.enabled:
            if 'Ultraining`**' in message_fields:
                tr_command = '/ultraining' if slash_command else 'rpg ultraining'
            else:
                tr_command = '/training' if slash_command else 'rpg training'
            try:
                tr_search = re.search("raining`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Training cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if tr_search is not None:
                tr_timestring = tr_search.group(1)
                tr_message = user_settings.alert_training.message.replace('{command}', tr_command)
                cooldowns.append(['training', tr_timestring.lower(), tr_message])
        if user_settings.alert_quest.enabled:
            try:
                quest_search = re.search("quest`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Quest cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if quest_search is not None:
                quest_timestring = quest_search.group(1)
                user_command = '/quest start' if slash_command else 'rpg quest'
                quest_message = user_settings.alert_quest.message.replace('{command}', user_command)
                cooldowns.append(['quest', quest_timestring.lower(), quest_message])
        if user_settings.alert_duel.enabled:
            try:
                duel_search = re.search("Duel`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Duel cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if duel_search is not None:
                duel_timestring = duel_search.group(1)
                user_command = '/duel' if slash_command else 'rpg duel'
                duel_message = user_settings.alert_duel.message.replace('{command}', user_command)
                cooldowns.append(['duel', duel_timestring.lower(), duel_message])
        if user_settings.alert_arena.enabled:
            try:
                arena_search = re.search("rena`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Arena cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if arena_search is not None:
                arena_timestring = arena_search.group(1)
                user_command = '/arena' if slash_command else 'rpg arena'
                arena_message = user_settings.alert_arena.message.replace('{command}', user_command)
                cooldowns.append(['arena', arena_timestring.lower(), arena_message])
        if user_settings.alert_dungeon_miniboss.enabled:
            try:
                dungmb_search = re.search("boss`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Miniboss cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if dungmb_search is not None:
                dungmb_timestring = dungmb_search.group(1)
                user_command = '/dungeon or /miniboss' if slash_command else 'rpg dungeon / miniboss'
                dungmb_message = user_settings.alert_dungeon_miniboss.message.replace('{command}', user_command)
                cooldowns.append(['dungeon-miniboss', dungmb_timestring.lower(), dungmb_message])
        if user_settings.alert_horse_breed.enabled:
            try:
                horse_search = re.search("race`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Horse cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if horse_search is not None:
                horse_timestring = horse_search.group(1)
                user_command = '/horse breeding or /horse race' if slash_command else 'rpg horse breed / race'
                horse_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                cooldowns.append(['horse', horse_timestring.lower(), horse_message])
        if user_settings.alert_vote.enabled:
            try:
                vote_search = re.search("Vote`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Vote cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if vote_search is not None:
                vote_timestring = vote_search.group(1)
                user_command = '/vote' if slash_command else 'rpg vote'
                vote_message = user_settings.alert_vote.message.replace('{command}', user_command)
                cooldowns.append(['vote', vote_timestring.lower(), vote_message])
        if user_settings.alert_farm.enabled:
            try:
                farm_search = re.search("Farm`\*\* \(\*\*(.+?)\*\*", message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Farm cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if farm_search is not None:
                farm_timestring = farm_search.group(1)
                user_command = '/farm' if slash_command else 'rpg farm'
                farm_message = user_settings.alert_farm.message.replace('{command}', user_command)
                cooldowns.append(['farm', farm_timestring.lower(), farm_message])
        if user_settings.alert_work.enabled:
            if 'Mine`**' in message_fields: work_search_string = 'Mine`\*\* \(\*\*(.+?)\*\*'
            elif 'Pickaxe`**' in message_fields: work_search_string = 'Pickaxe`\*\* \(\*\*(.+?)\*\*'
            elif 'Drill`**' in message_fields: work_search_string = 'Drill`\*\* \(\*\*(.+?)\*\*'
            else: work_search_string = 'Dynamite`\*\* \(\*\*(.+?)\*\*'
            try:
                work_search = re.search(work_search_string, message_fields)
            except Exception as error:
                if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                    await message.add_reaction(emojis.WARNING)
                await errors.log_error(
                    f'Work cooldown not found in cooldown message: {message.embeds[0].fields}',
                    message
                )
                return
            if work_search is not None:
                work_timestring = work_search.group(1)
                work_message = user_settings.alert_work.message.replace('{command}', 'work command')
                cooldowns.append(['work', work_timestring.lower(), work_message])
        current_time = datetime.utcnow().replace(microsecond=0)
        for cooldown in cooldowns:
            cd_activity = cooldown[0]
            cd_timestring = cooldown[1]
            cd_message = cooldown[2]
            time_left = await functions.calculate_time_left_from_timestring(message, cd_timestring)
            if time_left.total_seconds() > 0:
                reminder: reminders.Reminder = (
                    await reminders.insert_user_reminder(user.id, cd_activity, time_left,
                                                            message.channel.id, cd_message, overwrite_message=False)
                )
                if not reminder.record_exists:
                    await message.channel.send(strings.MSG_ERROR)
                    return
        if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(CooldownsCog(bot))