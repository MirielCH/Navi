# settings.py
# pyright: reportInvalidTypeForm=false
"""Contains settings commands"""

import discord
from discord.ext import bridge, commands
from discord.ext.bridge import BridgeOption
import re

from database import clans, errors, reminders, users
from content import settings as settings_cmd
from resources import emojis, exceptions, functions, settings, strings


class SettingsCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    # Bridge commands
    @bridge.bridge_command(name='on', description='Turn on Navi', aliases=('register', 'activate', 'start'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def on(self, ctx: bridge.BridgeContext) -> None:
        """Turn on Navi"""
        await settings_cmd.command_on(self.bot, ctx)

    @bridge.bridge_command(name='off', description='Turn off Navi', aliases=('deactivate','stop'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def off(self, ctx: bridge.BridgeContext) -> None:
        """Turn off Navi"""
        await settings_cmd.command_off(self.bot, ctx)

    @bridge.bridge_command(name='enable', aliases=('e',))
    @commands.bot_has_permissions(send_messages=True)
    async def enable(
        self,
        ctx: bridge.BridgeContext,
        *,
        settings: BridgeOption(str, max_lenght=1024, default=''),
    ) -> None:
        """Enable specific settings"""
        if len(settings) > 1024:
            await ctx.respond('Are you trying to write a novel here? 🤔')
            return
        await settings_cmd.command_enable_disable(self.bot, ctx, 'enable', settings.split())
        
    @bridge.bridge_command(name='disable', aliases=('d',))
    @commands.bot_has_permissions(send_messages=True)
    async def disable(
        self,
        ctx: bridge.BridgeContext,
        *,
        settings: BridgeOption(str, max_lenght=1024, default='')
    ) -> None:
        """Enable specific settings"""
        if len(settings) > 1024:
            await ctx.respond('Are you trying to write a novel here? 🤔')
            return
        await settings_cmd.command_enable_disable(self.bot, ctx, 'disable', settings.split())

    @bridge.bridge_command()
    async def purge(self, ctx: bridge.BridgeContext) -> None:
        """Purges user data from Navi"""
        await settings_cmd.command_purge_data(self.bot, ctx)

    @bridge.bridge_group(name='settings', aliases=('setting','set', 's'), invoke_without_command=True)
    async def settings_group(self, ctx: bridge.BridgeContext):
        """Settings command group"""
        command = self.bot.get_command(name='settings user')
        if command is not None: await command.callback(command.cog, ctx)

    @settings_group.command(name='alts', aliases=('alt', 'a'), description='Manage alts')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_alts(self, ctx: bridge.BridgeContext):
        """Alt settings command"""
        await settings_cmd.command_settings_alts(self.bot, ctx)
        
    @settings_group.command(name='guild', aliases=('clan', 'g'), description='Manage guild settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_clan(self, ctx: bridge.BridgeContext):
        """Guild settings command"""
        await settings_cmd.command_settings_clan(self.bot, ctx)

    aliases_settings_helpers = (
        'context-help','contexthelper','contexthelp','pethelper','pethelp','pet-helper','pet-help','heal',
        'heal-warning','healwarning','heal-warn','healwarn','trhelper','tr-helper','trhelp','tr-help','traininghelper',
        'training-helper', 'context-helper', 'h', 'helper'
    )
    @settings_group.command(name='helpers', aliases=aliases_settings_helpers, description='Manage helper settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_helpers(self, ctx: bridge.BridgeContext):
        """Helper settings command"""
        await settings_cmd.command_settings_helpers(self.bot, ctx)
        
    @settings_group.command(name='messages', aliases=('message', 'msg', 'm'), description='Manage reminder messages')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_messages(self, ctx: bridge.BridgeContext):
        """Message settings command"""
        await settings_cmd.command_settings_messages(self.bot, ctx)
        
    @settings_group.command(name='multipliers', aliases=('multiplier', 'multi'), description='Manage multipliers')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_multipliers(self, ctx: bridge.BridgeContext):
        """Multiplier settings command"""
        await settings_cmd.command_settings_multipliers(self.bot, ctx)
        
    @settings_group.command(name='partner', aliases=('p', 'marry', 'marriage'), description='Manage partner settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_partner(self, ctx: bridge.BridgeContext):
        """Partner settings command"""
        await settings_cmd.command_settings_partner(self.bot, ctx)
        
    @settings_group.command(name='portals', aliases=('portal', 'pt'), description='Manage portals')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_portals(self, ctx: bridge.BridgeContext):
        """Portal settings command"""
        await settings_cmd.command_settings_portals(self.bot, ctx)
        
    @settings_group.command(name='ready', aliases=('rd','auto-ready'), description='Manage ready settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_ready(self, ctx: bridge.BridgeContext):
        """Ready settings command"""
        await settings_cmd.command_settings_ready(self.bot, ctx)

    aliases_settings_reminders = (
        'slashmentions','ping-mode','pingmode','dnd','slash-mentions','reminder','rm',
    )
    @settings_group.command(name='reminders', aliases=aliases_settings_reminders, description='Manage reminder settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_reminders(self, ctx: bridge.BridgeContext):
        """Reminder settings command"""
        await settings_cmd.command_settings_reminders(self.bot, ctx)

    @bridge.bridge_group(name='server-settings', aliases=('serversettings','server','ss','admin'), invoke_without_command=True)
    async def server_settings_group(self, ctx: bridge.BridgeContext):
        """Server Settings command group"""
        command = self.bot.get_command(name='server-settings main')
        if command is not None: await command.callback(command.cog, ctx)
        
    @server_settings_group.command(name='main', aliases=('s','srv'), description='Manage server settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def server_settings_main(self, ctx: bridge.BridgeContext):
        """Server settings main command"""
        if (not ctx.author.guild_permissions.manage_guild
            and not (ctx.guild.id == 713541415099170836 and ctx.author.id == 619879176316649482)):
            raise commands.MissingPermissions(['manage_guild',])
            # This is to give me (Miriel) server settings access in RPG ARMY. This does NOT give me backdoor access
            # in any other server.
        await settings_cmd.command_server_settings_main(self.bot, ctx)
        
    @server_settings_group.command(name='auto-flex', aliases=('flex','auto_flex','autoflex','a',), description='Manage auto-flex server settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def server_settings_auto_flex(self, ctx: bridge.BridgeContext):
        """Server settings auto-flex command"""
        if (not ctx.author.guild_permissions.manage_guild
            and not (ctx.guild.id == 713541415099170836 and ctx.author.id == 619879176316649482)):
            raise commands.MissingPermissions(['manage_guild',])
            # This is to give me (Miriel) server settings access in RPG ARMY. This does NOT give me backdoor access
            # in any other server.
        await settings_cmd.command_server_settings_auto_flex(self.bot, ctx)
        
    @server_settings_group.command(name='event-pings', aliases=('ping','event','events','eventpings','eventping','pings'),
                                   description='Manage event ping server settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def server_settings_event_pings(self, ctx: bridge.BridgeContext):
        """Server settings event ping command"""
        if (not ctx.author.guild_permissions.manage_guild
            and not (ctx.guild.id == 713541415099170836 and ctx.author.id == 619879176316649482)):
            raise commands.MissingPermissions(['manage_guild',])
            # This is to give me (Miriel) server settings access in RPG ARMY. This does NOT give me backdoor access
            # in any other server.
        await settings_cmd.command_server_settings_event_pings(self.bot, ctx)

    @settings_group.command(name='user', aliases=('me','u','donor','track','tracking','last-tt','lasttt','donator'),
                      description='Manage user settings')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_user(self, ctx: bridge.BridgeContext):
        """User settings command"""
        await settings_cmd.command_settings_user(self.bot, ctx)


    # Text commands
    @commands.command(name='multipliers', aliases=('multiplier','multi','multis'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def multipliers(self, ctx: commands.Context, *args: str) -> None:
        """Multiplier settings (text version)"""
        await settings_cmd.command_multipliers(self.bot, ctx, args)
        
    @commands.command(name='sa', aliases=('srm','sm','srd','sp','sh','spt','sg','smulti','su','ssa','sse','ssm'))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def settings_shortcuts(self, ctx: commands.Context, *args: str) -> None:
        """Settings shortcuts"""
        settings_commands = {
            'sa': 'settings alts',
            'sg': 'settings guild',
            'sh': 'settings helpers',
            'sm': 'settings messages',
            'smulti': 'settings multipliers',
            'sp': 'settings partner',
            'spt': 'settings portals',
            'srd': 'settings ready',
            'srm': 'settings reminders',
            'ssa': 'server-settings auto-flex',
            'sse': 'server-settings event-pings',
            'ssm': 'server-settings main',
            'su': 'settings user',
        }
        command = self.bot.get_command(name=settings_commands[ctx.invoked_with.lower()])
        if command is not None: await command.callback(command.cog, ctx)


    # Events
    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Fires when a message is edited"""
        if message_before.author.id in [settings.EPIC_RPG_ID, settings.TESTY_ID]:
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
                clan_members = message_clan_members.split('\n')
                clan_member_ids = []
                if clan_leader.isnumeric():
                    clan_leader_id = int(clan_leader)
                else:
                    user_name_match = re.search(r'^(.+?)(?:#(\d+?))?$', clan_leader)
                    if not user_name_match:
                        await functions.add_warning_reaction(message_after)
                        await errors.log_error(f'Couldn\'t find user ID or name for guild list owner "{clan_leader}".',
                                                message_after)
                        return
                    username = user_name_match.group(1)
                    discriminator = user_name_match.group(2)
                    if discriminator is not None:
                        clan_leader = discord.utils.get(message_before.guild.members,
                                                        name=username, discriminator=discriminator)
                    else:
                        clan_leader = discord.utils.get(message_before.guild.members,
                                                        name=username)
                    clan_leader_id = clan_leader.id
                for member in clan_members:
                    user_id_match = re.search(r'^ID: \*\*(\d+?)\*\*$', member)
                    if user_id_match:
                        member_id = int(user_id_match.group(1))
                    else:
                        user_name_match = re.search(r'^\*\*(.+?)(?:#(\d+?))?\*\*$', member)
                        if not user_name_match:
                            await functions.add_warning_reaction(message_after)
                            await errors.log_error(f'Couldn\'t find user ID or name for guild list member "{member}".',
                                                   message_after)
                            return
                        username = user_name_match.group(1)
                        discriminator = user_name_match.group(2)
                        if discriminator is not None:
                            member = discord.utils.get(message_before.guild.members,
                                                    name=username, discriminator=discriminator)
                        else:
                            member = discord.utils.get(message_before.guild.members,
                                                    name=username)
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
                            try:
                                reminder: reminders.Reminder = await reminders.get_clan_reminder(clan.clan_name)
                                await reminder.update(clan_name=clan_name)
                            except exceptions.NoDataFoundError:
                                pass
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
                                f'If you renamed your guild: To prevent this from happening, please run '
                                f'{strings.SLASH_COMMANDS["guild list"]} immediately after renaming next time.'
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
                    if member_id is not None:
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
                                                f'{strings.SLASH_COMMANDS["guild list"]} to update it.'
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
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(SettingsCog(bot))
