# settings_partner.py
"""Contains partner settings commands"""

import asyncio

import discord
from discord.ext import commands

from database import users
from resources import emojis, exceptions, strings


class SettingsPartnerCog(commands.Cog):
    """Cog with partner settings commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    @commands.bot_has_permissions(send_messages=True)
    async def partner(self, ctx: commands.Context, *args: str) -> None:
        """Check/set current partner"""
        def partner_check(m: discord.Message) -> bool:
            return m.author in ctx.message.mentions and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        if not ctx.message.mentions:
            if user.partner_id is None:
                await ctx.reply(
                    f'**{ctx.author.name}**, you don\'t have a partner set.\n'
                    f'Setting a partner will allow you to set up partner lootbox alerts and the hardmode mode.\n\n'
                    f'If you want to set a partner, use this command to ping them (`{prefix}partner @User`)\n'
                    f'Note that your partner needs to be in the same server and needs to be able to answer.\n'
                )
            else:
                await self.bot.wait_until_ready()
                partner = self.bot.get_user(user.partner_id)
                await ctx.reply(
                    f'Your current partner is **{partner.name}**.\n'
                    f'If you want to change this, use this command to ping your new partner (`{prefix}partner @User`)\n'
                    f'To remove your partner entirely, use `{prefix}partner reset`.'
                )
                return
        if ctx.message.mentions:
            if user.partner_id:
                await ctx.reply(
                    f'**{ctx.author.name}**, you already have a partner.\n'
                    f'Use `{prefix}partner reset` to remove your old one first.'
                )
                return
            new_partner = ctx.message.mentions[0]
            try:
                partner: users.User = await users.get_user(new_partner.id)
            except exceptions.FirstTimeUserError:
                await ctx.reply(
                    f'**{new_partner.name}** is not registered with this bot yet. They need to do `{prefix}on` first.'
                )
                return
            await ctx.reply(
                f'{new_partner.mention}, **{ctx.author.name}** wants to set you as their partner. '
                f'Do you accept? `[yes/no]`'
            )
            try:
                answer = await self.bot.wait_for('message', check=partner_check, timeout=30)
                if answer.content.lower() not in ['yes','y']:
                    await ctx.send('Aborted.')
                    return
            except asyncio.TimeoutError:
                await ctx.send(f'**{ctx.author.name}**, your lazy partner didn\'t answer in time.')
                return
            await user.update(partner_id=partner.user_id, partner_donor_tier=partner.user_donor_tier)
            await partner.update(partner_id=user.user_id, partner_donor_tier=user.user_donor_tier)
            if user.partner_id == new_partner.id and partner.partner_id == ctx.author.id:
                await ctx.send(
                    f'**{ctx.author.name}**, {new_partner.name} is now set as your partner.\n'
                    f'**{new_partner.name}**, {ctx.author.name} is now set as your partner.\n'
                    f'You may now kiss the brides.'
                )
            else:
                await ctx.send(strings.MSG_ERROR)

    @partner.command(name='reset')
    @commands.bot_has_permissions(send_messages=True)
    async def partner_reset(self, ctx: commands.Context) -> None:
        """Reset current partner"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        if user.partner_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you don\'t have a partner set, there is no need to reset it.\n'
            )
        else:
            try:
                await ctx.reply(
                    f'**{ctx.author.name}**, this will reset both your partner **and** your partner\'s partner '
                    f'(which is you, heh).\n'
                    f'This also resets the partner donor tier back to 0.\n\n'
                    f'Do you accept? `[yes/no]`'
                )
                answer = await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
                return
            if answer.content.lower() not in ['yes','y']:
                await ctx.send('Aborted')
                return
            partner: users.User = await users.get_user(user.partner_id)
            await user.update(partner_id=None, partner_donor_tier=0)
            await partner.update(partner_id=None, partner_donor_tier=0)
            if user.partner_id is None and partner.partner_id is None:
                await ctx.send('Your partner settings were reset.')
            else:
                await ctx.send(strings.MSG_ERROR)

    @partner.command(name='donor', aliases=('donator',))
    @commands.bot_has_permissions(send_messages=True)
    async def partner_donor(self, ctx: commands.Context, *args: str) -> None:
        """Sets partner donor tier"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        msg_syntax = strings.MSG_SYNTAX.format(syntax=f'`{prefix}partner donor [tier]`')
        user: users.User = await users.get_user(ctx.author.id)
        possible_tiers = f'Possible tiers:'
        for index, donor_tier in enumerate(strings.DONOR_TIERS):
            possible_tiers = f'{possible_tiers}\n{emojis.BP}`{index}` : {donor_tier}'
        if not args:
            await ctx.reply(
                f'**{ctx.author.name}**, your partner\'s EPIC RPG donor tier is **{user.user_donor_tier}** '
                f'({strings.DONOR_TIERS[user.user_donor_tier]}).\n'
                f'If you want to change this, use `{prefix}partner donor [tier]`.\n\n{possible_tiers}'
            )
            return
        if args:
            try:
                donor_tier = int(args[0])
            except:
                await ctx.reply(f'{msg_syntax}\n\n{possible_tiers}')
                return
            if donor_tier > len(strings.DONOR_TIERS) - 1:
                await ctx.reply(f'{msg_syntax}\n\n{possible_tiers}')
                return
            if user.partner_id is not None:
                await ctx.reply(
                    f'**{ctx.author.name}**, you currently have a partner set. The partner donor tier is '
                    f'automatically synchronized with your partner.\n'
                    f'If the donor tier of your partner is wrong, they have to change it themselves using '
                    f'`{prefix}donor [tier]`.'
                )
                return
            await user.update(partner_donor_tier=donor_tier)
            await ctx.reply(
                f'**{ctx.author.name}**, your partner\'s EPIC RPG donor tier is now set to **{user.partner_donor_tier}** '
                f'({strings.DONOR_TIERS[user.partner_donor_tier]}).\n'
                f'Please note that the `hunt together` cooldown can only be accurately calculated if '
                f'`{prefix}donor [tier]` is set correctly as well.'
            )

    @partner.group(name='channel', invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def partner_channel(self, ctx: commands.Context, *args: str) -> None:
        """Check current partner alert channel"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        if args:
            await ctx.reply(strings.MSG_INVALID_ARGUMENT.format(prefix=prefix))
            return
        user: users.User = await users.get_user(ctx.author.id)
        if user.partner_channel_id is not None:
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(user.partner_channel_id)
            await ctx.reply(
                f'Your current partner alert channel is `{channel.name}` (ID `{channel.id}`).\n'
                f'If you want to change this, use `{prefix}partner channel set` within your new alert channel.\n'
                f'To remove the alert channel entirely, use `{ctx.prefix}partner channel reset`'
            )
            return
        else:
            await ctx.reply(
                f'You don\'t have a partner alert channel set.\n'
                f'If you want to set one, use `{ctx.prefix}partner channel set` within your new alert channel.\n'
                f'The partner alert channel is the channel where you get notified if your partner finds a lootbox '
                f'for you while hunting.'
            )
            return

    @partner_channel.command(name='set')
    @commands.bot_has_permissions(send_messages=True)
    async def partner_channel_set(self, ctx: commands.Context) -> None:
        """Sets new partner alert channel"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to set `{ctx.channel.name}` as your partner alert channel? '
                f'`[yes/no]`'
            )
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if answer.content.lower() not in ['yes','y']:
            await ctx.send('Aborted')
            return
        await user.update(partner_channel_id=ctx.channel.id)
        if user.partner_channel_id == ctx.channel.id:
            await ctx.send(f'`{ctx.channel.name}` is now set as your partner alert channel.')
        else:
            await ctx.send(strings.MSG_ERROR)

    @partner_channel.command(name='reset')
    @commands.bot_has_permissions(send_messages=True)
    async def partner_channel_reset(self, ctx: commands.Context) -> None:
        """Reset current partner alert channel"""
        def check(m: discord.Message) -> bool:
            return m.author == ctx.author and m.channel == ctx.channel

        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        user: users.User = await users.get_user(ctx.author.id)
        if user.partner_channel_id is None:
            await ctx.reply(
                f'**{ctx.author.name}**, you don\'t have a partner alert channel set, there is no need to reset it.\n'
            )
            return
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(user.partner_channel_id)
        try:
            await ctx.reply(
                f'**{ctx.author.name}**, do you want to remove `{channel.name}` as your partner alert channel? '
                f'`[yes/no]`\n'
                f'This will also disable your partner alerts.'
            )
            answer = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
            return
        if answer.content.lower() not in ['yes','y']:
            await ctx.send('Aborted')
            return
        await user.update(partner_channel_id=None, alert_partner_enabled=False)
        if user.partner_channel_id is None and not user.alert_partner.enabled:
            await ctx.send('Your partner alert channel got reset and your partner alert disabled.')
        else:
            await ctx.send(strings.MSG_ERROR)


# Initialization
def setup(bot):
    bot.add_cog(SettingsPartnerCog(bot))