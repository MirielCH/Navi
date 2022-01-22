# settings_clan.py
"""Contains clan settings commands"""

import asyncio

import discord
from discord.ext import commands

from database import clans, reminders, users
from resources import emojis, exceptions, settings, strings


class SettingsClanCog(commands.Cog):
    """Cog with user settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commands
    @commands.group(name='guild', invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, read_message_history=True)
    async def clan(self, ctx: commands.Context, *args: str) -> None:
        """Trigger clan command detection if no subcommand was found"""
        if ctx.prefix.lower() == 'rpg ':
            if ctx.message.mentions: return
            command = self.bot.get_command(name='clan_detection')
            if command is not None: await command.callback(command.cog, ctx, *args)

    @clan.group(name='channel', invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def clan_channel(self, ctx: commands.Context, *args: str) -> None:
        """Check the current clan alert channel"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        if args:
            ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix), mention_author=False)
            return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        if clan.channel_id is not None:
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(clan.channel_id)
            await ctx.reply(
                f'Your current guild alert channel is `{channel.name}` (ID `{channel.id}`).\n'
                f'If you want to change this, use `{prefix}guild channel set` within your new alert channel.\n'
                f'To remove the alert channel entirely, use `{ctx.prefix}guild channel reset`',
                mention_author=False
            )
            return
        else:
            await ctx.reply(
                f'You don\'t have a guild alert channel set.\n'
                f'If you want to set one, use `{ctx.prefix}guild channel set` within your new alert channel.\n'
                f'The guild alert channel is the channel where the guild reminders are sent to.',
                mention_author=False
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
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_GUILD_LEADER.format(username=ctx.author.name), mention_author=False)
            return
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to set `{ctx.channel.name}` as the alert channel '
                f'for the guild **{clan.clan_name}**? `[yes/no]`',
                mention_author=False
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
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        if clan.leader_id != ctx.author.id:
            await ctx.reply(strings.MSG_NOT_GUILD_LEADER.format(username=ctx.author.name), mention_author=False)
            return
        if clan.channel_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you don\'t have a guild alert channel set, there is no need to reset it.\n',
                mention_author=False
            )
            return
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(clan.channel_id)
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to remove `{channel.name}` as the alert channel for '
                f'the guild **{clan.clan_name}**? `[yes/no]`\n'
                f'This will also disable your guild\'s reminders.',
                mention_author=False
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
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        if args:
            msg_wrong_argument = f'**{ctx.author.name}**, the stealth threshold needs to be a number between 1 and 100.'
            try:
                new_threshold = int(args[0])
            except:
                await ctx.reply(msg_wrong_argument, mention_author=False)
                return
            if not 1 <= new_threshold <= 100:
                await ctx.reply(msg_wrong_argument, mention_author=False)
                return
            await clan.update(stealth_threshold=new_threshold)
            await ctx.reply(
                f'**{ctx.author.name}**, the stealth threshold for the guild **{clan.clan_name}** is now '
                f'**{clan.stealth_threshold}**.',
                mention_author=False
            )
            return
        await ctx.reply(
                f'The current stealth threshold for the guild **{clan.clan_name}** is **{clan.stealth_threshold}**.\n'
                f'If you want to change this, use `{prefix}guild stealth [1-100]`.',
                mention_author=False
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
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        if not args:
            action = 'enabled' if clan.alert_enabled else 'disabled'
            await ctx.reply(
                f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are currently {action}.\n'
                f'Use `{prefix}guild reminder [on|off]` to change this.',
                mention_author=False
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
                await ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix), mention_author=False)
                return
            if clan.alert_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are already {action}.',
                    mention_author=False
                )
                return
            await clan.update(alert_enabled=enabled)
            if clan.alert_enabled == enabled:
                await ctx.reply(
                    f'**{ctx.author.name}**, reminders for the guild **{clan.clan_name}** are now {action}.',
                    mention_author=False
                )
            else:
                await ctx.reply(strings.MSG_ERROR, mention_author=False)

    @clan.command(name='leaderboard', aliases=('lb',))
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def clan_leaderboard(self, ctx: commands.Context) -> None:
        """Shows the clan leaderboard"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            clan: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.reply(strings.MSG_CLAN_NOT_REGISTERED, mention_author=False)
            return
        leaderboard: clans.ClanLeaderboard = await clans.get_leaderboard(clan)
        field_best_raids = field_worst_raids = ''
        for index, best_raid in enumerate(leaderboard.best_raids):
            emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
            await self.bot.wait_until_ready()
            user = self.bot.get_user(best_raid.user_id)
            field_best_raids = f'{field_best_raids}\n{emoji} **{best_raid.energy:,}** by {user.mention}'
        for index, worst_raid in enumerate(leaderboard.worst_raids):
            emoji = getattr(emojis, f'LEADERBOARD_{index+1}')
            await self.bot.wait_until_ready()
            user = self.bot.get_user(worst_raid.user_id)
            field_worst_raids = f'{field_worst_raids}\n{emoji} **{worst_raid.energy:,}** by {user.mention}'
        if field_best_raids == '': field_best_raids = f'{emojis.BP} _No cool raids yet._'
        if field_worst_raids == '': field_worst_raids = f'{emojis.BP} _No lame raids yet._'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = f'{clan.clan_name.upper()} WEEKLY LEADERBOARD',
        )
        embed.set_footer(text='Imagine being on the lower list.')
        embed.add_field(name=f'COOL RAIDS {emojis.BEST_RAIDS}', value=field_best_raids, inline=False)
        embed.add_field(name=f'WHAT THE HELL IS THIS {emojis.WORST_RAIDS}', value=field_worst_raids, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    # Events
    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Fires when a message is edited"""
        if message_before.author.id == settings.EPIC_RPG_ID:
            if message_before.content.find('loading the EPIC guild member list...') > -1:
                message_clan_name = str(message_after.embeds[0].fields[0].name)
                message_clan_members = str(message_after.embeds[0].fields[0].value)
                message_clan_leader = str(message_after.embeds[0].footer.text)
                clan_name = message_clan_name.replace(' members','').replace('**','')
                clan_leader = message_clan_leader.replace('Owner: ','')
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
                        discriminator = member[member.find('#')+1:]
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
                            leader = self.bot.get_user(clan.leader_id)
                            await message_after.channel.send(
                                f'{leader.mention} Found two guilds with unmatching members with you as a leader which '
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