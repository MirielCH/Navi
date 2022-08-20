# settings_clan.py
"""Contains clan settings commands"""

import asyncio

import discord
from discord.ext import commands

from database import clans, errors, reminders, users
from resources import emojis, exceptions, functions, settings, strings


class SettingsClanCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @commands.group(name='guild', invoke_without_command=True, case_insensitive=True)
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def clan(self, ctx: commands.Context, *args: str) -> None:
        """Trigger clan command detection if no subcommand was found"""
        if ctx.prefix.lower() == 'rpg ':
            if ctx.message.mentions: return
            command = self.bot.get_command(name='clan_detection')
            if command is not None: await command.callback(command.cog, ctx, *args)
        else:
            user_settings: users.User = await users.get_user(ctx.author.id)
            command_guild_stats = await functions.get_slash_command(user_settings, 'guild stats')
            command_guild_list = await functions.get_slash_command(user_settings, 'guild list')
            guide = (
                f'**Guild command reminder**\n'
                f'If you want a personal reminder for the guild command, use `{ctx.prefix}enable guild`.\n'
                f'This reminder works like every other command reminder (e.g. `hunt`). It is created when you raid or '
                f'upgrade or when you use `rpg guild` or {command_guild_stats}.\n\n'
                f'**Channel reminder**\n'
                f'The guild channel reminder works differently from the other reminders. Channel reminders are sent to '
                f'a guild channel and always **ping all guild members**.\n\n'
                f'**Setting up guild channel reminders**\n'
                f":one: Use `rpg guild list` or {command_guild_list} "
                f'to add or update your guild.\n'
                f':two: __Guild owner__: Use `{ctx.prefix}guild channel set` to set the guild channel.\n'
                f':three: __Guild owner__: Turn on reminders with `navi guild reminder on`.\n'
                f':four: __Guild owner__: Use `{ctx.prefix}guild stealth` to change the stealth threshold '
                f'(90 default).\n'
                f':five: __Guild owner__: Use `{ctx.prefix}guild upgrade-quests` to allow or deny guild members to do '
                f'guild quests below stealth threshold (allowed by default).\n'
                f':six: Use `{ctx.prefix}guild leaderbord` or `{ctx.prefix}guild lb` to check the weekly raid '
                f'leaderboard.\n\n'
                f'**Notes**\n'
                f'{emojis.BP} The guild channel does not need to be unique, you can use the same channel for '
                f'multiple guilds.\n'
                f'{emojis.BP} Reminders are always sent to the guild channel. You can, however, raid or upgrade wherever '
                f'you want, **as long as Navi can see it**. If you raid or upgrade somewhere else, use `rpg guild` or '
                f"{command_guild_stats} here to create the reminder.\n"
                f'{emojis.BP} Navi pings all guild members and thus needs no role. If you add or remove a guild member, '
                f"simply use `rpg guild list` or {command_guild_list} again.\n"
                f'{emojis.BP} Navi will tell you to upgrade until the threshold is reached and to raid afterwards.\n'
                f'{emojis.BP} If you accept a raid quest and guild quests are allowed, you will be pinged 5m before '
                f'everyone else\n'
            )
            await ctx.reply(guide)

    @clan.group(name='channel', invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def clan_channel(self, ctx: commands.Context, *args: str) -> None:
        """Check the current clan alert channel"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        if args:
            ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix))
            return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.channel_id is not None:
            channel = await functions.get_discord_channel(self.bot, clan.channel_id)
            await ctx.reply(
                f'Your current guild alert channel is `{channel.name}` (ID `{channel.id}`).\n'
                f'If you want to change this, use `{prefix}guild channel set` within your new alert channel.\n'
                f'To remove the alert channel entirely, use `{ctx.prefix}guild channel reset`'
            )
            return
        else:
            await ctx.reply(
                f'You don\'t have a guild alert channel set.\n'
                f'If you want to set one, use `{ctx.prefix}guild channel set` within your new alert channel.\n'
                f'The guild alert channel is the channel where the guild reminders are sent to.'
            )
            return

    @clan_channel.command(name='set')
    @commands.bot_has_permissions(send_messages=True)
    async def clan_channel_set(self, ctx: commands.Context) -> None:
        """Sets new clan alert channel"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_CLAN_LEADER.format(username=ctx.author.name, prefix=ctx.prefix))
            return
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to set `{ctx.channel.name}` as the alert channel '
                f'for the guild **{clan.clan_name}**? `[yes/no]`'
            )
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if answer.content.lower() not in ['yes','y']:
            await ctx.send('Aborted')
            return
        await clan.update(channel_id=ctx.channel.id)
        if clan.channel_id == ctx.channel.id:
            await ctx.send(f'`{ctx.channel.name}` is now set as your guild alert channel.')
        else:
            await ctx.send(strings.MSG_ERROR)

    @clan_channel.command(name='reset')
    @commands.bot_has_permissions(send_messages=True)
    async def clan_channel_reset(self, ctx: commands.Context) -> None:
        """Reset current clan alert channel"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_CLAN_LEADER.format(username=ctx.author.name, prefix=ctx.prefix))
            return
        if clan.channel_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you don\'t have a guild alert channel set, there is no need to reset it.\n'
            )
            return
        channel = await functions.get_discord_channel(self.bot, clan.channel_id)
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to remove `{channel.name}` as the alert channel for '
                f'the guild **{clan.clan_name}**? `[yes/no]`\n'
                f'This will also disable your guild\'s reminders.'
            )
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if answer.content.lower() not in ['yes','y']:
            await ctx.send('Aborted')
            return
        await clan.update(channel_id=None, alert_enabled=False)
        try:
            reminder: reminders.Reminder = await reminders.get_clan_reminder(clan.clan_name)
            await reminder.delete()
        except exceptions.NoDataFoundError:
            pass
        if clan.channel_id is None and not clan.alert_enabled:
            await ctx.send(f'The guild **{clan.clan_name}**\'s alert channel got reset and the reminders disabled.')
        else:
            await ctx.send(strings.MSG_ERROR)

    @clan.command(name='stealth')
    @commands.bot_has_permissions(send_messages=True)
    async def clan_stealth(self, ctx: commands.Context, *args: str) -> None:
        """Check/set the current clan stealth threshold"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_CLAN_LEADER.format(username=ctx.author.name, prefix=ctx.prefix))
            return
        if args:
            msg_wrong_argument = f'**{ctx.author.name}**, the stealth threshold needs to be a number between 1 and 95.'
            try:
                new_threshold = int(args[0])
            except:
                await ctx.reply(msg_wrong_argument)
                return
            if not 1 <= new_threshold <= 95:
                await ctx.reply(msg_wrong_argument)
                return
            await clan.update(stealth_threshold=new_threshold)
            try:
                reminder: reminders.Reminder = await reminders.get_clan_reminder(clan.clan_name)
                if new_threshold <= clan.stealth_current:
                    new_message = reminder.message.replace('upgrade','raid')
                else:
                    new_message = reminder.message.replace('raid','upgrade')
                await reminder.update(message=new_message)
            except exceptions.NoDataFoundError:
                pass
            await ctx.reply(
                f'**{ctx.author.name}**, the stealth threshold for the guild **{clan.clan_name}** is now '
                f'**{clan.stealth_threshold}**.'
            )
            return
        await ctx.reply(
                f'The current stealth threshold for the guild **{clan.clan_name}** is **{clan.stealth_threshold}**.\n'
                f'If you want to change this, use `{prefix}guild stealth [1-95]`.'
        )

    @clan.command(name='reminders', aliases=('reminder','alert'))
    @commands.bot_has_permissions(send_messages=True)
    async def clan_reminder(self, ctx: commands.Context, *args: str) -> None:
        """Check/set guild reminders"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_CLAN_LEADER.format(username=ctx.author.name, prefix=ctx.prefix))
            return
        if clan.channel_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you need to set a guild alert channel first. '
                f'Use `{ctx.prefix}guild channel set` to do so. Note that you need to be the guild owner for this.\n\n'
                f'Also check `{prefix}guild` to see how guild reminders work.'
            )
            return
        if not args:
            action = 'enabled' if clan.alert_enabled else 'disabled'
            await ctx.reply(
                f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are currently {action}.\n'
                f'Use `{prefix}guild reminder [on|off]` to change this.'
            )
            return
        if args:
            action = args[0]
            if action in ('on','enable','start'):
                action = 'enabled'
                enabled = True
            elif action in ('off','disable','stop'):
                action = 'disabled'
                enabled = False
            else:
                await ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix))
                return
            if clan.alert_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are already {action}.'
                )
                return
            await clan.update(alert_enabled=enabled)
            if clan.alert_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are now {action}.'
                )
            else:
                await ctx.reply(strings.MSG_ERROR)

    @clan.command(name='upgrade-quests', aliases=('upgradequests','upgradequest','upgrade-quest'))
    @commands.bot_has_permissions(send_messages=True)
    async def clan_upgrade_quests(self, ctx: commands.Context, *args: str) -> None:
        """Allow/deny guild quests below the stealth threshold"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_CLAN_LEADER.format(username=ctx.author.name, prefix=ctx.prefix))
            return
        if clan.channel_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you need to set a guild alert channel first. '
                f'Use `{ctx.prefix}guild channel set` to do so. Note that you need to be the guild owner for this.\n\n'
                f'Also check `{prefix}guild` to see how guild reminders work.'
            )
            return
        if not clan.alert_enabled:
            await ctx.reply(
                f'**{ctx.author.name}**, you need turn on guild reminders first. '
                f'Use `{ctx.prefix}guild reminders on` to do so. Note that you need to be the guild owner for this.\n\n'
                f'Also check `{prefix}guild` to see how guild reminders work.'
            )
            return
        if not args:
            action = 'allowed' if clan.upgrade_quests_enabled else 'not allowed'
            await ctx.reply(
                f'**{ctx.author.name}**, guild members are currently **{action}** to do guild quests below the stealth '
                f'threshold.\n'
                f'Use `{prefix}guild upgrade-quests [on|off]` to change this.'
            )
            return
        if args:
            action = args[0]
            if action in ('on','enable','start','allow','allowed'):
                action = 'allowed'
                enabled = True
            elif action in ('off','disable','stop','deny','denied'):
                action = 'not allowed'
                enabled = False
            else:
                await ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix))
                return
            if clan.upgrade_quests_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, guild members are already **{action}** to do guild quests below the stealth '
                    f'threshold.'
                )
                return
            await clan.update(upgrade_quests_enabled=enabled)
            if clan.upgrade_quests_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, guild members are now **{action}** to do guild quests below the stealth '
                    f'threshold.'
                )
            else:
                await ctx.reply(strings.MSG_ERROR)

    @clan.command(name='leaderboard', aliases=('lb',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def clan_leaderboard(self, ctx: commands.Context) -> None:
        """Shows the clan leaderboard"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED)
            return
        leaderboard: clans.ClanLeaderboard = await clans.get_leaderboard(clan)
        field_best_raids = field_worst_raids = ''
        for index, best_raid in enumerate(leaderboard.best_raids):
            emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
            await self.bot.wait_until_ready()
            field_best_raids = (
                f'{field_best_raids}\n'
                f'{emoji} **{best_raid.energy:,}** {emojis.ENERGY} by <@{best_raid.user_id}>'
            )
        for index, worst_raid in enumerate(leaderboard.worst_raids):
            emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
            await self.bot.wait_until_ready()
            field_worst_raids = (
                f'{field_worst_raids}\n'
                f'{emoji} **{worst_raid.energy:,}** {emojis.ENERGY} by <@{worst_raid.user_id}>'
            )
        if field_best_raids == '': field_best_raids = f'{emojis.BP} _No cool raids yet._'
        if field_worst_raids == '': field_worst_raids = f'{emojis.BP} _No lame raids yet._'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = f'{clan.clan_name.upper()} WEEKLY LEADERBOARD',
        )
        embed.set_footer(text='Imagine being on the lower list.')
        embed.add_field(name=f'COOL RAIDS {emojis.BEST_RAIDS}', value=field_best_raids, inline=False)
        embed.add_field(name=f'WHAT THE HELL IS THIS {emojis.WORST_RAIDS}', value=field_worst_raids, inline=False)
        await ctx.reply(embed=embed)

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
    bot.add_cog(SettingsClanCog(bot))