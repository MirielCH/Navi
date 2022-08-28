# settings_clan.py
"""Contains clan settings commands"""

import discord
from discord.commands import SlashCommandGroup, slash_command, Option
from discord.ext import commands

from database import clans, errors, reminders, users
from content import settings as settings_cmd
from resources import emojis, exceptions, functions, settings, strings


class SettingsCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @slash_command()
    async def on(self, ctx: discord.ApplicationContext) -> None:
        """Turn on Navi"""
        await settings_cmd.command_on(self.bot, ctx)

    @slash_command()
    async def off(self, ctx: discord.ApplicationContext) -> None:
        """Turn off Navi"""
        await settings_cmd.command_off(self.bot, ctx)

    cmd_settings = SlashCommandGroup(
        "settings",
        "Settings commands",
    )

    # Commands
    @cmd_settings.command()
    async def guild(self, ctx: discord.ApplicationContext) -> None:
        """Manage guild settings"""
        await settings_cmd.command_settings_clan(self.bot, ctx)

    @cmd_settings.command()
    async def helpers(self, ctx: discord.ApplicationContext) -> None:
        """Manage helper settings"""
        await settings_cmd.command_settings_helpers(self.bot, ctx)

    @cmd_settings.command()
    async def messages(self, ctx: discord.ApplicationContext) -> None:
        """Manage reminder messages"""
        await settings_cmd.command_settings_messages(self.bot, ctx)

    @cmd_settings.command()
    async def partner(
        self,
        ctx: discord.ApplicationContext,
        new_partner: Option(discord.User, 'Set a new partner', default=None)) -> None:
        """Manage partner settings"""
        await settings_cmd.command_settings_partner(self.bot, ctx, new_partner)

    @cmd_settings.command()
    async def reminders(self, ctx: discord.ApplicationContext) -> None:
        """Manage reminder settings"""
        await settings_cmd.command_settings_reminders(self.bot, ctx)

    @cmd_settings.command()
    async def user(self, ctx: discord.ApplicationContext) -> None:
        """Manage user settings"""
        await settings_cmd.command_settings_user(self.bot, ctx)

    # Events
    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Fires when a message is edited"""
        if message_before.author.id == settings.EPIC_RPG_ID:
            search_strings = [
                'loading the epic guild member list...', #English
                'cargando la lista épica de miembros...', #Spanish
                'carregando lista de membros épica...', #Portuguese
            ]
            if any(search_string in message_before.content.lower() for search_string in search_strings):
                message_clan_name = str(message_after.embeds[0].fields[0].name)
                message_clan_members = str(message_after.embeds[0].fields[0].value)
                message_clan_leader = str(message_after.embeds[0].footer.text)
                search_patterns = [
                    r'^\*\*(.+?)\*\* members', #English
                    r'^Mi?embros de \*\*(.+?)\*\*', #Spanish, Portuguese
                ]
                clan_name_match = await functions.get_match_from_patterns(search_patterns, message_clan_name)
                if clan_name_match:
                    clan_name = clan_name_match.group(1)
                else:
                    await functions.add_warning_reaction(message_after)
                    await errors.log_error(f'Clan name not found in guild list message: {message_clan_name}', message_after)
                    return
                search_patterns = [
                    r'Owner: (.+?)$', #English
                    r'Líder: (.+?)$', #Spanish, Portuguese
                ]
                clan_leader_match = await functions.get_match_from_patterns(search_patterns, message_clan_leader)
                if clan_leader_match:
                    clan_leader = clan_leader_match.group(1)
                else:
                    await functions.add_warning_reaction(message_after)
                    await errors.log_error('Clan owner not found in guild list message: {message_clan_leader}', message_after)
                    return
                clan_members = message_clan_members.replace('ID: ','').replace('**','')
                clan_members = clan_members.split('\n')
                clan_member_ids = []
                if clan_leader.isnumeric():
                    clan_leader_id = int(clan_leader)
                else:
                    username = clan_leader[:clan_leader.find('#')]
                    discriminator = clan_leader[clan_leader.find('#')+1:]
                    clan_leader = discord.utils.get(message_before.guild.members,
                                                    name=username, discriminator=discriminator)
                    clan_leader_id = clan_leader.id
                for member in clan_members:
                    if member.isnumeric():
                        member_id = int(member)
                    else:
                        username = member[:member.find('#')]
                        discriminator = member[member.find('#') + 1:]
                        member = discord.utils.get(message_before.guild.members,
                                                   name=username, discriminator=discriminator)
                        member_id = member.id
                    clan_member_ids.append(member_id)
                if len(clan_member_ids) < 10:
                    clan_member_ids_full = [None] * 10
                    for index, member_id in enumerate(clan_member_ids):
                        clan_member_ids_full[index] = member_id
                    clan_member_ids = clan_member_ids_full
                try:
                    clan: clans.Clan = await clans.get_clan_by_user_id(clan_leader_id)
                    if clan.leader_id == clan_leader_id and clan.clan_name != clan_name:
                        if clan.member_ids == tuple(clan_member_ids):
                            reminder: reminders.Reminder = await reminders.get_clan_reminder(clan.clan_name)
                            await reminder.update(clan_name=clan_name)
                            await clan.update(clan_name=clan_name)
                        else:
                            try:
                                reminder: reminders.Reminder = await reminders.get_clan_reminder(clan.clan_name)
                                await reminder.delete()
                            except exceptions.NoDataFoundError:
                                pass
                            await clans.delete_clan_leaderboard(clan.clan_name)
                            await clan.delete()
                            await self.bot.wait_until_ready()
                            await message_after.channel.send(
                                f'<@{clan.leader_id}> Found two guilds with unmatching members with you as an owner which '
                                f'is an invalid state I can\'t resolve.\n'
                                f'As a consequence I deleted the guild **{clan.clan_name}** including **all settings and '
                                f'the leaderboard** from the database and added **{clan_name}** as a new guild.\n\n'
                                f'If you renamed your guild: To prevent this from happening, please run `rpg guild list`'
                                f'immediately after renaming next time.'
                            )
                except exceptions.NoDataFoundError:
                    pass
                try:
                    clan: clans.Clan = await clans.get_clan_by_clan_name(clan_name)
                    await clan.update(leader_id=clan_leader_id, member_ids=clan_member_ids)
                except exceptions.NoDataFoundError:
                    clan: clans.Clan = await clans.insert_clan(clan_name, clan_leader_id, clan_member_ids)
                if not clan.record_exists or clan.leader_id != clan_leader_id or clan.member_ids != tuple(clan_member_ids):
                    if settings.DEBUG_MODE: await message_after.channel.send(strings.MSG_ERROR)
                    return
                for member_id in clan.member_ids:
                    try:
                        user: users.User = await users.get_user(member_id)
                        if user.clan_name != clan.clan_name:
                            try:
                                old_clan: clans.Clan = await clans.get_clan_by_clan_name(user.clan_name)
                                old_leader_id = None if old_clan.leader_id == member_id else old_clan.leader_id
                                old_member_ids = []
                                for old_member_id in old_clan.member_ids:
                                    if old_member_id == member_id:
                                        old_member_ids.append(None)
                                    else:
                                        old_member_ids.append(old_member_id)
                                old_member_ids = sorted(old_member_ids, key=lambda id: (id is None, id))
                                if old_leader_id is None and all(id is None for id in old_member_ids):
                                    await old_clan.delete()
                                    await message_after.channel.send(
                                        f'Removed the guild **{old_clan.clan_name}** because it doesn\'t have any '
                                        f'registered members anymore.'
                                    )
                                else:
                                    await old_clan.update(leader_id=old_leader_id, member_ids=old_member_ids)
                                    if old_leader_id is None:
                                        await message_after.channel.send(
                                            f'Note that the guild **{old_clan.clan_name}** doesn\'t have an owner '
                                            f'registered anymore. Please tell one of the remaining members to use '
                                            f'`rpg guild list` to update it.'
                                        )
                            except exceptions.NoDataFoundError:
                                pass
                        await user.update(clan_name=clan.clan_name)
                        if user.clan_name != clan.clan_name:
                            await message_after.channel.send(strings.MSG_ERROR)
                            return
                    except exceptions.FirstTimeUserError:
                        pass
                users_with_clan_name = await users.get_users_by_clan_name(clan_name)
                for user in users_with_clan_name:
                    if not user.user_id in clan_member_ids: await user.update(clan_name=None)
                await message_after.add_reaction(emojis.NAVI)


# Initialization
def setup(bot):
    bot.add_cog(SettingsCog(bot))