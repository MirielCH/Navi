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

        search_strings = [
            'check the short version of this command', #English
            'revisa la versión más corta de este comando', #Spanish
            'verifique a versão curta deste comando', #Portuguese
        ]
        if all(search_string not in message_footer.lower() for search_string in search_strings): return

        user_id = user_name = None
        user = await functions.get_interaction_user(message)
        slash_command = True if user is not None else False
        if user is None:
            user_id_match = re.search(strings.REGEX_USER_ID_FROM_ICON_URL, icon_url)
            if user_id_match:
                user_id = int(user_id_match.group(1))
            else:
                user_name_match = await re.search(strings.REGEX_USERNAME_FROM_EMBED_AUTHOR, message_author)
                if user_name_match:
                    user_name = await functions.encode_text(user_name_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('User not found in cooldown message.', message)
                    return
            if user_id is not None:
                user = await message.guild.fetch_member(user_id)
            else:
                user = await functions.get_guild_member_by_name(message.guild, user_name)
        if user is None:
            await functions.add_warning_reaction(message)
            await errors.log_error('User not found in cooldowns message.', message)
            return
        try:
            user_settings: users.User = await users.get_user(user.id)
        except exceptions.FirstTimeUserError:
            return
        if not user_settings.bot_enabled: return
        cooldowns = []
        if user_settings.alert_daily.enabled:
            daily_match = re.search(r"daily`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if daily_match:
                daily_timestring = daily_match.group(1)
                user_command = strings.SLASH_COMMANDS['daily'] if slash_command else '`rpg daily`'
                daily_message = user_settings.alert_daily.message.replace('{command}', user_command)
                cooldowns.append(['daily', daily_timestring.lower(), daily_message])
        if user_settings.alert_weekly.enabled:
            weekly_match = re.search(r"weekly`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if weekly_match:
                weekly_timestring = weekly_match.group(1)
                user_command = strings.SLASH_COMMANDS['weekly'] if slash_command else '`rpg weekly`'
                weekly_message = user_settings.alert_weekly.message.replace('{command}', user_command)
                cooldowns.append(['weekly', weekly_timestring.lower(), weekly_message])
        if user_settings.alert_lootbox.enabled:
            lb_match = re.search(r"lootbox`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if lb_match:
                lootbox_name = '[lootbox]'
                if user_settings.last_lootbox is not None:
                    lootbox_name = f'{user_settings.last_lootbox} lootbox'
                if slash_command:
                    user_command = f"{strings.SLASH_COMMANDS['buy']} `item: {lootbox_name}`"
                else:
                    user_command = f'`rpg buy {lootbox_name}`'
                lb_timestring = lb_match.group(1)
                lb_message = user_settings.alert_lootbox.message.replace('{command}', user_command)
                cooldowns.append(['lootbox', lb_timestring.lower(), lb_message])
        if user_settings.alert_hunt.enabled:
            hunt_match = re.search(r'hunt(?: hardmode)?`\*\* \(\*\*(.+?)\*\*', message_fields.lower())
            if hunt_match:
                if user_settings.last_hunt_mode is not None:
                    if slash_command:
                        user_command = f"{strings.SLASH_COMMANDS['hunt']} `mode: {user_settings.last_hunt_mode}`"
                    else:
                        user_command = f'`rpg adventure {user_settings.last_hunt_mode}`'
                else:
                    if 'hardmode' in hunt_match.group(0):
                        if slash_command:
                            user_command = f"{strings.SLASH_COMMANDS['hunt']} `mode: hardmode`"
                        else:
                            user_command = '`rpg hunt hardmode`'
                    else:
                        if slash_command:
                            user_command = strings.SLASH_COMMANDS['hunt']
                        else:
                            user_command = '`rpg hunt`'
                hunt_timestring = hunt_match.group(1)
                hunt_message = user_settings.alert_hunt.message.replace('{command}', user_command)
                cooldowns.append(['hunt', hunt_timestring.lower(), hunt_message])
        if user_settings.alert_adventure.enabled:
            adv_match = re.search(r'adventure(?: hardmode)?`\*\* \(\*\*(.+?)\*\*', message_fields.lower())
            if adv_match:
                if user_settings.last_adventure_mode is not None:
                    if slash_command:
                        user_command = f"{strings.SLASH_COMMANDS['adventure']} `mode: {user_settings.last_adventure_mode}`"
                    else:
                        user_command = f'`rpg adventure {user_settings.last_adventure_mode}`'
                else:
                    if 'hardmode' in adv_match.group(0):
                        if slash_command:
                            user_command = f"{strings.SLASH_COMMANDS['adventure']} `mode: hardmode`"
                        else:
                            user_command = '`rpg adventure hardmode`'
                    else:
                        if slash_command:
                            user_command = strings.SLASH_COMMANDS['adventure']
                        else:
                            user_command = '`rpg adventure`'
                adv_timestring = adv_match.group(1)
                adv_message = user_settings.alert_adventure.message.replace('{command}', user_command)
                cooldowns.append(['adventure', adv_timestring.lower(), adv_message])
        if user_settings.alert_training.enabled:
            tr_match = re.search(r"raining`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if tr_match:
                if slash_command:
                    user_command = strings.SLASH_COMMANDS[user_settings.last_training_command]
                else:
                    user_command = f'`rpg {user_settings.last_training_command}`'
                tr_timestring = tr_match.group(1)
                tr_message = user_settings.alert_training.message.replace('{command}', user_command)
                cooldowns.append(['training', tr_timestring.lower(), tr_message])
        if user_settings.alert_quest.enabled:
            quest_match = re.search(r"quest`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if quest_match:
                if slash_command:
                    user_command = strings.SLASH_COMMANDS[user_settings.last_quest_command]
                else:
                    user_command = f'`rpg {user_settings.last_quest_command}`'
                quest_timestring = quest_match.group(1)
                quest_message = user_settings.alert_quest.message.replace('{command}', user_command)
                cooldowns.append(['quest', quest_timestring.lower(), quest_message])
        if user_settings.alert_duel.enabled:
            duel_match = re.search(r"duel`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if duel_match:
                duel_timestring = duel_match.group(1)
                user_command = strings.SLASH_COMMANDS['duel'] if slash_command else '`rpg duel`'
                duel_message = user_settings.alert_duel.message.replace('{command}', user_command)
                cooldowns.append(['duel', duel_timestring.lower(), duel_message])
        if user_settings.alert_arena.enabled:
            arena_match = re.search(r"rena`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if arena_match:
                arena_timestring = arena_match.group(1)
                user_command = strings.SLASH_COMMANDS['arena'] if slash_command else '`rpg arena`'
                arena_message = user_settings.alert_arena.message.replace('{command}', user_command)
                cooldowns.append(['arena', arena_timestring.lower(), arena_message])
        if user_settings.alert_dungeon_miniboss.enabled:
            dungmb_match = re.search(r"boss`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if dungmb_match:
                dungmb_timestring = dungmb_match.group(1)
                if slash_command:
                    user_command = f"{strings.SLASH_COMMANDS['dungeon'] or strings.SLASH_COMMANDS['miniboss']}"
                else:
                    user_command = '`rpg dungeon` or `rpg miniboss`'
                dungmb_message = user_settings.alert_dungeon_miniboss.message.replace('{command}', user_command)
                cooldowns.append(['dungeon-miniboss', dungmb_timestring.lower(), dungmb_message])
        if user_settings.alert_horse_breed.enabled:
            horse_match = re.search(r"race`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if horse_match:
                horse_timestring = horse_match.group(1)
                if slash_command:
                    user_command = f"{strings.SLASH_COMMANDS['horse breeding'] or strings.SLASH_COMMANDS['horse race']}"
                else:
                    user_command = '`rpg horse breed` or `rpg horse race`'
                horse_message = user_settings.alert_horse_breed.message.replace('{command}', user_command)
                cooldowns.append(['horse', horse_timestring.lower(), horse_message])
        if user_settings.alert_vote.enabled:
            vote_match = re.search(r"vote`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if vote_match:
                vote_timestring = vote_match.group(1)
                user_command = strings.SLASH_COMMANDS['vote'] if slash_command else '`rpg vote`'
                vote_message = user_settings.alert_vote.message.replace('{command}', user_command)
                cooldowns.append(['vote', vote_timestring.lower(), vote_message])
        if user_settings.alert_farm.enabled:
            farm_match = re.search(r"farm`\*\* \(\*\*(.+?)\*\*", message_fields.lower())
            if farm_match:
                farm_timestring = farm_match.group(1)
                if slash_command:
                    user_command = strings.SLASH_COMMANDS['farm']
                    if user_settings.last_farm_seed is not None:
                        user_command = f'{user_command} `seed: {user_settings.last_farm_seed}`'
                else:
                    user_command = 'rpg farm'
                    if user_settings.last_farm_seed is not None:
                        user_command = f'{user_command} {user_settings.last_farm_seed}'
                    user_command = f'`{user_command}`'
                farm_message = user_settings.alert_farm.message.replace('{command}', user_command)
                cooldowns.append(['farm', farm_timestring.lower(), farm_message])
        if user_settings.alert_work.enabled:
            search_patterns = [
                r'mine`\*\* \(\*\*(.+?)\*\*',
                r'pickaxe`\*\* \(\*\*(.+?)\*\*',
                r'drill`\*\* \(\*\*(.+?)\*\*',
                r'dynamite`\*\* \(\*\*(.+?)\*\*',
            ]
            work_match = await functions.get_match_from_patterns(search_patterns, message_fields.lower())
            if work_match:
                if user_settings.last_work_command is not None:
                    if slash_command:
                        user_command = strings.SLASH_COMMANDS[user_settings.last_work_command]
                    else:
                        user_command = f'`rpg {user_settings.last_work_command}`'
                else:
                    user_command = 'work command'
                work_timestring = work_match.group(1)
                work_message = user_settings.alert_work.message.replace('{command}', user_command)
                cooldowns.append(['work', work_timestring.lower(), work_message])
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