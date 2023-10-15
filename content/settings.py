# settings.py
"""Contains settings commands"""

import asyncio
from datetime import timezone
import re
from typing import List, Optional, Union

import discord
from discord.ext import commands

from database import clans, guilds, portals, reminders, tracking, users
from resources import emojis, exceptions, functions, settings, strings, views


SETTINGS_HELPERS = [
    'context-helper',
    'heal-warning',
    'pet-helper',
    'ruby-counter',
    'training-helper',
]

SETTINGS_HELPER_ALIASES = {
    'ctx': 'context-helper',
    'context': 'context-helper',
    'contexthelp': 'context-helper',
    'contexthelper': 'context-helper',
    'context-help': 'context-helper',
    'ctx-help': 'context-helper',
    'ctxhelp': 'context-helper',
    'ctxhelper': 'context-helper',
    'ctx-helper': 'context-helper',
    'heal': 'heal-warning',
    'healwarn': 'heal-warning',
    'heal-warn': 'heal-warning',
    'healwarning': 'heal-warning',
    'pethelper': 'pet-helper',
    'pethelp': 'pet-helper',
    'pet-catch': 'pet-helper',
    'pet-catch-helper': 'pet-helper',
    'pet-catchhelper': 'pet-helper',
    'petcatchhelper': 'pet-helper',
    'petcatchhelp': 'pet-helper',
    'petcatch-help': 'pet-helper',
    'petcatch-helper': 'pet-helper',
    'ruby': 'ruby-counter',
    'rubycounter': 'ruby-counter',
    'rubycount': 'ruby-counter',
    'ruby-count': 'ruby-counter',
    'counter': 'ruby-counter',
    'tr-helper': 'training-helper',
    'tr-help': 'training-helper',
    'trhelp': 'training-helper',
    'trhelper': 'training-helper',
    'traininghelp': 'training-helper',
    'traininghelper': 'training-helper',
}

SETTINGS_HELPER_COLUMNS = {
    'context-helper': 'context_helper',
    'heal-warning': 'heal_warning',
    'pet-helper': 'pet_helper',
    'ruby-counter': 'ruby_counter',
    'training-helper': 'training_helper',
}

SETTINGS_USER = [
    'auto-ready',
    'dnd-mode',
    'hardmode-mode',
    'hunt-rotation',
    'slash-mentions',
    'tracking',
]

SETTINGS_USER_ALIASES = {
    'dnd': 'dnd-mode',
    'dndmode': 'dnd-mode',
    'hm': 'hardmode-mode',
    'hardmode': 'hardmode-mode',
    'hardmodemode': 'hardmode-mode',
    'hm-mode': 'hardmode-mode',
    'hmmode': 'hardmode-mode',
    'huntrotation': 'hunt-rotation',
    'rotation': 'hunt-rotation',
    'huntswitch': 'hunt-rotation',
    'switch': 'hunt-rotation',
    'hunt-switch': 'hunt-rotation',
    'slash': 'slash-mentions',
    'mention': 'slash-mentions',
    'mentions': 'slash-mentions',
    'slashmention': 'slash-mentions',
    'slashmentions': 'slash-mentions',
    'slash-commands': 'slash-mentions',
    'slash-command': 'slash-mentions',
    'slashcommand': 'slash-mentions',
    'slashcommands': 'slash-mentions',
    'track': 'tracking',
    'commandtrack': 'tracking',
    'commandtracking': 'tracking',
    'command-tracking': 'tracking',
    'command-track': 'tracking',
    'cmd-track': 'tracking',
    'cmd-tracking': 'tracking',
    'cmdtrack': 'tracking',
    'cmdtracking': 'tracking',
    'rd': 'auto-ready',
    'ready': 'auto-ready',
    'autoready': 'auto-ready',
}

SETTINGS_USER_COLUMNS = {
    'auto-ready': 'auto_ready',
    'dnd-mode': 'dnd_mode',
    'hardmode-mode': 'hardmode_mode',
    'hunt-rotation': 'hunt_rotation',
    'slash-mentions': 'slash_mentions',
    'tracking': 'tracking',
}

# --- Commands ---
async def command_on(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """On command"""
    first_time_user = False
    try:
        user: users.User = await users.get_user(ctx.author.id)
        if user.bot_enabled:
            await ctx.respond(f'**{ctx.author.name}**, I\'m already turned on.', ephemeral=True)
            return
    except exceptions.FirstTimeUserError:
        user = await users.insert_user(ctx.author.id)
        first_time_user = True
    if not user.bot_enabled: await user.update(bot_enabled=True)
    if not user.bot_enabled:
        await ctx.respond(strings.MSG_ERROR, ephemeral=True)
        return
    if not first_time_user:
        await ctx.respond(f'Hey! **{ctx.author.name}**! Welcome back!')
    else:
        field_settings = (
            f'You may want to have a look at my settings. You can also set your EPIC RPG donor tier there.\n'
            f'Click the button below or use {await functions.get_navi_slash_command(bot, "settings user")}.'
        )
        field_tracking = (
            f'I track the amount of some EPIC RPG commands you use. Check '
            f'{await functions.get_navi_slash_command(bot, "stats")} to see what commands are tracked.\n'
            f'**__No personal data is processed or stored in any way!__**\n'
            f'You can opt-out of command tracking in {await functions.get_navi_slash_command(bot, "stats")} '
            f'or in your user settings.\n\n'
        )
        field_auto_flex = (
            f'This bot has an auto flex feature. If auto flexing is turned on by the server admin, I will automatically '
            f'post certain rare events (rare lootboxes, high tier loot, etc) to an auto flex channel.\n'
            f'If you don\'t like this, you can turn it off in your user settings.\n'
        )
        field_privacy = (
            f'To read more about what data is processed and why, feel free to check the privacy policy found in '
            f'{await functions.get_navi_slash_command(bot, "help")}.'
        )
        img_navi = discord.File(settings.IMG_NAVI, filename='navi.png')
        image_url = 'attachment://navi.png'
        embed = discord.Embed(
            title = f'Hey! {ctx.author.name}! Hello!'.upper(),
            description = (
                f'I am here to help you with your EPIC RPG commands!\n'
                f'Have a look at {await functions.get_navi_slash_command(bot, "help")} for a list of my own commands.'
            ),
            color =  settings.EMBED_COLOR,
        )
        embed.add_field(name='SETTINGS', value=field_settings, inline=False)
        embed.add_field(name='COMMAND TRACKING', value=field_tracking, inline=False)
        embed.add_field(name='AUTO FLEXING', value=field_auto_flex, inline=False)
        embed.add_field(name='PRIVACY POLICY', value=field_privacy, inline=False)
        embed.set_thumbnail(url=image_url)
        view = views.OneButtonView(ctx, discord.ButtonStyle.blurple, 'pressed', '➜ Settings')
        interaction = await ctx.respond(embed=embed, file=img_navi, view=view)
        view.interaction_message = interaction
        await view.wait()
        if view.value == 'pressed':
            await functions.edit_interaction(interaction, view=None)
            await command_settings_user(bot, ctx)


async def command_off(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """Off command"""
    user: users.User = await users.get_user(ctx.author.id)
    if not user.bot_enabled:
        await ctx.respond(f'**{ctx.author.name}**, I\'m already turned off.', ephemeral=True)
        return
    answer = (
        f'**{ctx.author.name}**, turning me off will disable me completely. This includes all helpers, the command '
        f'tracking, auto flexing and the reminders. It will also delete all of your active reminders.\n'
        f'Are you sure?'
    )
    view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
    interaction = await ctx.respond(answer, view=view)
    view.interaction_message = interaction
    await view.wait()
    if view.value is None:
        await functions.edit_interaction(
            interaction, content=f'**{ctx.author.name}**, you didn\'t answer in time.', view=None)
    elif view.value == 'confirm':
        await user.update(bot_enabled=False)
        try:
            active_reminders = await reminders.get_active_user_reminders(ctx.author.id)
            for reminder in active_reminders:
                await reminder.delete()
        except exceptions.NoDataFoundError:
            pass
        if not user.bot_enabled:
            answer = (
                f'**{ctx.author.name}**, I\'m now turned off.\n'
                f'All active reminders were deleted.'
            )
            await functions.edit_interaction(interaction, content=answer, view=None)
        else:
            await ctx.followup.send(strings.MSG_ERROR)
            return
    else:
        await functions.edit_interaction(interaction, content='Aborted.', view=None)


async def command_purge_data(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """Purge data command"""
    user_settings: users.User = await users.get_user(ctx.author.id)
    answer_aborted = f'**{ctx.author.name}**, phew, was worried there for a second.'
    answer_timeout = f'**{ctx.author.name}**, you didn\'t answer in time.'
    answer = (
        f'{emojis.WARNING} **{ctx.author.name}**, this will purge your user data from Navi **completely** {emojis.WARNING}\n\n'
        f'This includes the following:\n'
        f'{emojis.BP} Your alts\n'
        f'{emojis.BP} All reminders\n'
        f'{emojis.BP} All raids in the current guild leaderboard\n'
        f'{emojis.BP} Your complete command tracking history\n'
        f'{emojis.BP} Your user portals\n'
        f'{emojis.BP} And finally, your user settings\n\n'
        f'**There is no coming back from this**.\n'
        f'You will of course be able to start using Navi again, but all of your data will start '
        f'from scratch.\n'
        f'Are you **SURE**?'
    )
    view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.green])
    interaction = await ctx.respond(answer, view=view)
    view.interaction_message = interaction
    await view.wait()
    if view.value is None:
        await functions.edit_interaction(
            interaction, content=answer_timeout, view=None
        )
    elif view.value == 'confirm':
        await functions.edit_interaction(interaction, view=None)
        answer = (
            f'{emojis.WARNING} **{ctx.author.name}**, just a friendly final warning {emojis.WARNING}\n'
            f'**ARE YOU SURE?**'
        )
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.green])
        interaction = await ctx.respond(answer, view=view)
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(
                interaction, content=answer_timeout, view=None
            )
        elif view.value == 'confirm':
            cur = settings.NAVI_DB.cursor()
            await functions.edit_interaction(
                interaction, content='Purging user settings...',
                view=None
            )
            if user_settings.partner_id is not None:
                try:
                    partner_settings: users.User = await users.get_user(user_settings.partner_id)
                    await partner_settings.update(partner_id=None)
                except exceptions.FirstTimeUserError:
                    pass
            cur.execute('DELETE FROM users WHERE user_id=?', (ctx.author.id,))
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction, content='Purging alts...',
                view=None
            )
            cur.execute('DELETE FROM alts WHERE user1_id=? OR user2_id=?', (ctx.author.id, ctx.author.id))
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction, content='Purging reminders...',
                view=None
            )
            cur.execute('DELETE FROM reminders_users WHERE user_id=?', (ctx.author.id,))
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction, content='Purging raid data...',
                view=None
            )
            cur.execute('DELETE FROM clans_raids WHERE user_id=?', (ctx.author.id,))
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction, content='Purging portals...',
                view=None
            )
            cur.execute('DELETE FROM users_portals WHERE user_id=?', (ctx.author.id,))
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction, content='Purging tracking data... (this can take a while)',
                view=None
            )
            try:
                log_entries =  await tracking.get_all_log_entries(ctx.author.id)
            except exceptions.NoDataFoundError:
                log_entries = []
            for log_entry in log_entries:
                await log_entry.delete()
                await asyncio.sleep(0.01)
            await asyncio.sleep(1)
            await functions.edit_interaction(
                interaction,
                content=f'{emojis.ENABLED} **{ctx.author.name}**, you are now gone and forgotton. Thanks for using me!',
                view=None
            )   
        else:
            await functions.edit_interaction(
                interaction, content=answer_aborted, view=None
            )
    else:
        await functions.edit_interaction(
            interaction, content=answer_aborted, view=None
        )
        

async def command_settings_alts(bot: discord.Bot, ctx: discord.ApplicationContext,
                                switch_view: Optional[discord.ui.View] = None) -> None:
    """Alt settings command"""
    interaction = user_settings = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    if switch_view is not None: switch_view.stop()
    view = views.SettingsAltsView(ctx, bot, user_settings, embed_settings_alts)
    embed = await embed_settings_alts(bot, ctx, user_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()

    
async def command_settings_clan(bot: discord.Bot, ctx: discord.ApplicationContext,
                                switch_view: Optional[discord.ui.View] = None) -> None:
    """Clan settings command"""
    user_settings: users.User = await users.get_user(ctx.author.id)
    clan_settings = interaction = None
    if switch_view is not None:
        clan_settings = getattr(switch_view, 'clan_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
    if clan_settings is None:
        try:
            clan_settings: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            await ctx.respond(
                f'Your guild is not registered with me yet. Use {strings.SLASH_COMMANDS["guild list"]} '
                f'to do that first.',
                ephemeral=True
            )
            return
    if switch_view is not None: switch_view.stop()
    view = views.SettingsClanView(ctx, bot, clan_settings, embed_settings_clan)
    embed = await embed_settings_clan(bot, ctx, clan_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_helpers(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   switch_view: Optional[discord.ui.View] = None) -> None:
    """Helper settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    view = views.SettingsHelpersView(ctx, bot, user_settings, embed_settings_helpers)
    embed = await embed_settings_helpers(bot, ctx, user_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_portals(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   switch_view: Optional[discord.ui.View] = None) -> None:
    """Portals settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    try:
        user_portals = list(await portals.get_portals(ctx.author.id))
    except exceptions.NoDataFoundError:
        user_portals = []
    view = views.SettingsPortalsView(ctx, bot, user_settings, user_portals, embed_settings_portals)
    embed = await embed_settings_portals(bot, ctx, user_settings, user_portals)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_messages(bot: discord.Bot, ctx: discord.ApplicationContext,
                                    switch_view: Optional[discord.ui.View] = None) -> None:
    """Reminder message settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    view = views.SettingsMessagesView(ctx, bot, user_settings, embed_settings_messages, 'all')
    embeds = await embed_settings_messages(bot, ctx, user_settings, 'all')
    if interaction is None:
        interaction = await ctx.respond(embeds=embeds, view=view)
    else:
        await functions.edit_interaction(interaction, embeds=embeds, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_multipliers(bot: discord.Bot, ctx: discord.ApplicationContext,
                                       switch_view: Optional[discord.ui.View] = None) -> None:
    """Reminder multiplier settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    view = views.SettingsMultipliersView(ctx, bot, user_settings, embed_settings_multipliers)
    embed = await embed_settings_multipliers(bot, ctx, user_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()
    

async def command_settings_partner(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   switch_view: Optional[discord.ui.View] = None) -> None:
    """Partner settings command"""
    user_settings = interaction = partner_settings = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        partner_settings = getattr(switch_view, 'partner_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    if partner_settings is None and user_settings.partner_id is not None:
        try:
            partner_settings: users.User = await users.get_user(user_settings.partner_id)
        except exceptions.NoDataFoundError:
            await ctx.respond(strings.MSG_ERROR, ephemeral=True)
            return
    view = views.SettingsPartnerView(ctx, bot, user_settings, partner_settings, embed_settings_partner)
    embed = await embed_settings_partner(bot, ctx, user_settings, partner_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_ready(bot: discord.Bot, ctx: discord.ApplicationContext,
                                 switch_view: Optional[discord.ui.View] = None) -> None:
    """ready settings command"""
    user_settings = clan_settings = interaction = None
    if switch_view is not None:
        clan_settings = getattr(switch_view, 'clan_settings', None)
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    if clan_settings is None:
        try:
            clan_settings: clans.Clan = await clans.get_clan_by_user_id(ctx.author.id)
        except exceptions.NoDataFoundError:
            clan_settings = None
    view = views.SettingsReadyView(ctx, bot, user_settings, clan_settings, embed_settings_ready)
    embed = await embed_settings_ready(bot, ctx, user_settings, clan_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_reminders(bot: discord.Bot, ctx: discord.ApplicationContext,
                                     switch_view: Optional[discord.ui.View] = None) -> None:
    """Reminder settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    view = views.SettingsRemindersView(ctx, bot, user_settings, embed_settings_reminders)
    embed = await embed_settings_reminders(bot, ctx, user_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_server(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """Server settings command"""
    guild_settings: guilds.Guild = await guilds.get_guild(ctx.guild.id)
    view = views.SettingsServerView(ctx, bot, guild_settings, embed_settings_server)
    embed = await embed_settings_server(bot, ctx, guild_settings)
    interaction = await ctx.respond(embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_settings_user(bot: discord.Bot, ctx: discord.ApplicationContext,
                                switch_view: Optional[discord.ui.View] = None) -> None:
    """User settings command"""
    user_settings = interaction = None
    if switch_view is not None:
        user_settings = getattr(switch_view, 'user_settings', None)
        interaction = getattr(switch_view, 'interaction', None)
        switch_view.stop()
    if user_settings is None:
        user_settings: users.User = await users.get_user(ctx.author.id)
    view = views.SettingsUserView(ctx, bot, user_settings, embed_settings_user)
    embed = await embed_settings_user(bot, ctx, user_settings)
    if interaction is None:
        interaction = await ctx.respond(embed=embed, view=view)
    else:
        await functions.edit_interaction(interaction, embed=embed, view=view)
    view.interaction = interaction
    await view.wait()


async def command_enable_disable(bot: discord.Bot, ctx: Union[discord.ApplicationContext, commands.Context],
                                 action: str, settings: List[str]) -> None:
    """Enables/disables specific settings"""
    user_settings: users.User = await users.get_user(ctx.author.id)
    enabled = True if action == 'enable' else False
    possible_reminders = 'Reminders:'
    for activity in strings.ACTIVITIES_ALL:
        possible_reminders = f'{possible_reminders}\n{emojis.BP} `{activity}`'
    possible_helpers = 'Helpers:'
    for helper in sorted(SETTINGS_HELPERS):
        possible_helpers = f'{possible_helpers}\n{emojis.BP} `{helper}`'
    possible_user = 'User settings:'
    for setting in sorted(SETTINGS_USER):
        possible_user = f'{possible_user}\n{emojis.BP} `{setting}`'

    if not settings:
        await functions.reply_or_respond(
            ctx,
            f'This command can be used to quickly enable or disable certain settings.\n'
            f'You can disable multiple settings at once by separating them with a space.\n\n'
            f'**Possible settings**\n'
            f'{possible_reminders}\n\n'
            f'{possible_helpers}\n\n'
            f'{possible_user}'
        )
        return

    for index, setting in enumerate(settings):
        if setting in strings.ACTIVITIES_ALIASES: settings[index] = strings.ACTIVITIES_ALIASES[setting]
        if setting in SETTINGS_HELPER_ALIASES: settings[index] = SETTINGS_HELPER_ALIASES[setting]
        if setting in SETTINGS_USER_ALIASES: settings[index] = SETTINGS_USER_ALIASES[setting]

    if 'all' in settings:
        if not enabled:
            answer_delete = (
                f'**{ctx.author.name}**, this will turn off all reminders which will also delete all of your active '
                f'reminders. Are you sure?'
            )
            view = views.ConfirmCancelView(ctx, [discord.ButtonStyle.red, discord.ButtonStyle.grey])
            if isinstance(ctx, discord.ApplicationContext):
                interaction_message = await ctx.respond(answer_delete, view=view)
            else:
                interaction_message = await ctx.reply(answer_delete, view=view)
            view.interaction_message = interaction_message
            await view.wait()
            if view.value == 'confirm':
                if isinstance(ctx, discord.ApplicationContext):
                    await functions.edit_interaction(interaction_message, view=None)
                else:
                    await interaction_message.edit(view=None)
            else:
                if isinstance(ctx, discord.ApplicationContext):
                    await functions.edit_interaction(interaction_message, content='Aborted.', view=None)
                else:
                    await interaction_message.edit(content='Aborted', view=None)
                return
        for setting in settings.copy():
            if setting in strings.ACTIVITIES:
                settings.remove(setting)
        settings += strings.ACTIVITIES
        settings.remove('all')

    updated_reminders = []
    updated_helpers = []
    updated_user = []
    ignored_settings = []
    answer_reminders = answer_helpers = answer_user = answer_ignored = ''
    settings = list(dict.fromkeys(settings))
    for setting in settings:
        if setting in strings.ACTIVITIES: updated_reminders.append(setting)
        elif setting in SETTINGS_HELPERS: updated_helpers.append(setting)
        elif setting in SETTINGS_USER: updated_user.append(setting)
        else: ignored_settings.append(setting)

    kwargs = {}
    if updated_reminders:
        answer_reminders = f'{action.capitalize()}d reminders for the following activities:'
        for activity in updated_reminders:
            kwargs[f'{strings.ACTIVITIES_COLUMNS[activity]}_enabled'] = enabled
            answer_reminders = f'{answer_reminders}\n{emojis.BP}`{activity}`'
            if not enabled:
                if activity == 'pets':
                    try:
                        all_reminders = await reminders.get_active_user_reminders(ctx.author.id)
                        for reminder in all_reminders:
                            if 'pets' in reminder.activity: await reminder.delete()
                    except:
                        pass
                try:
                    reminder: reminders.Reminder = await reminders.get_user_reminder(ctx.author.id, activity)
                    await reminder.delete()
                except exceptions.NoDataFoundError:
                    pass

    if updated_helpers:
        answer_helpers = f'{action.capitalize()}d the following helpers:'
        for helper in updated_helpers:
            kwargs[f'{SETTINGS_HELPER_COLUMNS[helper]}_enabled'] = enabled
            answer_helpers = f'{answer_helpers}\n{emojis.BP}`{helper}`'

    if updated_user:
        answer_user = f'{action.capitalize()}d the following user settings:'
        for setting in updated_user:
            kwargs[f'{SETTINGS_USER_COLUMNS[setting]}_enabled'] = enabled
            answer_user = f'{answer_user}\n{emojis.BP}`{setting}`'

    if updated_reminders or updated_helpers or updated_user:
        await user_settings.update(**kwargs)

    if ignored_settings:
        answer_ignored = f'Couldn\'t find the following settings:'
        for setting in ignored_settings:
            answer_ignored = f'{answer_ignored}\n{emojis.BP}`{setting}`'

    answer = ''
    if answer_reminders != '':
        answer = answer_reminders
    if answer_helpers != '':
        answer = f'{answer}\n\n{answer_helpers}'
    if answer_user != '':
        answer = f'{answer}\n\n{answer_user}'
    if answer_ignored != '':
        answer = f'{answer}\n\n{answer_ignored}'

    await functions.reply_or_respond(ctx, answer.strip())


# --- Embeds ---
async def embed_settings_alts(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User) -> discord.Embed:
    """Alt settings embed"""
    alts = f'{emojis.BP} No alts set'
    alt_count = 0
    if user_settings.alts:
        alts = ''
        for alt_id in user_settings.alts:
            alts = f'{alts}\n{emojis.BP} <@{alt_id}>'
            alt_count += 1
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S ALTS',
        description = (
            f'_You can ping alts in reminders and quickly view their status in '
            f'{await functions.get_navi_slash_command(bot, "ready")}, '
            f'{await functions.get_navi_slash_command(bot, "list")}'
            f' and {await functions.get_navi_slash_command(bot, "stats")}._'
        )
    )
    embed.add_field(name=f'ALTS ({alt_count}/24)', value=alts, inline=False)
    return embed


async def embed_settings_clan(bot: discord.Bot, ctx: discord.ApplicationContext, clan_settings: clans.Clan) -> discord.Embed:
    """Guild settings embed"""
    reminder_enabled = await functions.bool_to_text(clan_settings.alert_enabled)
    if clan_settings.upgrade_quests_enabled:
        clan_upgrade_quests = f'{emojis.ENABLED}`Allowed`'
    else:
        clan_upgrade_quests = f'{emojis.DISABLED}`Not allowed`'
    if clan_settings.channel_id is not None:
        clan_channel = f'<#{clan_settings.channel_id}>'
    else:
        clan_channel = '`N/A`'
    if clan_settings.quest_user_id is not None:
        quest_user = f'<@{clan_settings.quest_user_id}>'
    else:
        quest_user = '`None`'

    overview = (
        f'{emojis.BP} **Name**: `{clan_settings.clan_name}`\n'
        f'{emojis.BP} **Owner**: <@{clan_settings.leader_id}>\n'
    )
    reminder = (
        f'{emojis.BP} **Guild channel**: {clan_channel}\n'
        f'{emojis.DETAIL} _Reminders will always be sent to this channel._\n'
        f'{emojis.BP} **Reminder**: {reminder_enabled}\n'
        f'{emojis.BP} **Stealth threshold**: `{clan_settings.stealth_threshold}`\n'
        f'{emojis.DETAIL} _Navi will tell you to upgrade below threshold and raid afterwards._\n'
    )
    quests = (
        f'{emojis.BP} **Quests below stealth threshold**: {clan_upgrade_quests}\n'
        f'{emojis.BP} **Member currently on quest**: {quest_user}\n'
        f'{emojis.DETAIL} _The member on a guild quest will get pinged 5 minutes early._'
    )
    members = ''
    member_count = 0
    for member_id in clan_settings.member_ids:
        if member_id is not None:
            members = f'{members}\n{emojis.BP} <@{member_id}>'
            member_count += 1
    members = f'{members.strip()}\n\n➜ _Use {strings.SLASH_COMMANDS["guild list"]} to update guild members._'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{clan_settings.clan_name} GUILD SETTINGS',
        description = (
            f'_Settings to set up a guild reminder for the whole guild. Note that if you enable this reminder, Navi will '
            f'ping **all guild members**.\n'
            f'If you just want to get reminded for the guild command yourself, there is a separate reminder for that in '
            f'`Reminder settings` below._'
        )
    )
    embed.add_field(name='OVERVIEW', value=overview, inline=False)
    embed.add_field(name='REMINDER', value=reminder, inline=False)
    embed.add_field(name='GUILD QUESTS', value=quests, inline=False)
    embed.add_field(name=f'MEMBERS ({member_count}/10)', value=members, inline=False)
    return embed


async def embed_settings_helpers(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User) -> discord.Embed:
    """Helper settings embed"""
    tr_helper_mode = 'Buttons' if user_settings.training_helper_button_mode else 'Text'
    pet_helper_mode = 'Icons' if user_settings.pet_helper_icon_mode else 'Commands'
    ruby_counter_mode = 'Buttons' if user_settings.ruby_counter_button_mode else 'Text'
    ping_mode_setting = 'After' if user_settings.ping_after_message else 'Before'
    helpers = (
        f'{emojis.BP} **Context helper**: {await functions.bool_to_text(user_settings.context_helper_enabled)}\n'
        f'{emojis.DETAIL} _Shows some helpful slash commands depending on context (mostly slash only)._\n'
        f'{emojis.BP} **Heal warning**: {await functions.bool_to_text(user_settings.heal_warning_enabled)}\n'
        f'{emojis.DETAIL} _Warns you when you are about to die._\n'
        #f'{emojis.BP} **Megarace Helper**: {await functions.bool_to_text(user_settings.megarace_helper_enabled)}\n'
        #f'{emojis.DETAIL} _Provides the optimal answers for the horse festival megarace._\n'
        f'{emojis.BP} **Pet catch helper**: {await functions.bool_to_text(user_settings.pet_helper_enabled)}\n'
        f'{emojis.DETAIL} _Tells you which commands to use when you encounter a pet._\n'
        f'{emojis.BP} **Ruby counter**: {await functions.bool_to_text(user_settings.ruby_counter_enabled)}\n'
        f'{emojis.DETAIL} _Keeps track of your rubies and helps with ruby training._\n'
    )
    helpers2 = (
        f'{emojis.BP} **Training helper**: {await functions.bool_to_text(user_settings.training_helper_enabled)}\n'
        f'{emojis.DETAIL} _Provides the answers for all training types except ruby training._\n'
        f'{emojis.BP} **Farm helper mode**: `{strings.FARM_HELPER_MODES[user_settings.farm_helper_mode]}`\n'
        f'{emojis.DETAIL} _Changes your farm reminder according to the mode and your inventory._\n'
        #f'{emojis.BP} **Pumpkin bat helper** {emojis.PET_PUMPKIN_BAT}: '
        #f'{await functions.bool_to_text(user_settings.halloween_helper_enabled)}\n'
        #f'{emojis.DETAIL} _Provides the answers for the halloween boss._\n'
    )
    helper_settings = (
        f'{emojis.BP} **Pet catch helper style**: `{pet_helper_mode}`\n'
        f'{emojis.BP} **Ruby counter style**: `{ruby_counter_mode}`\n'
        f'{emojis.BP} **Training helper style**: `{tr_helper_mode}`\n'
        f'{emojis.BP} **Ping mode**: `{ping_mode_setting}` helper message\n'
        f'{emojis.DETAIL} _This setting has no effect on button helpers and if DND mode is on._\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S HELPER SETTINGS',
        description = '_Settings to toggle some helpful little features._'
    )
    embed.add_field(name='HELPERS (I)', value=helpers, inline=False)
    embed.add_field(name='HELPERS (II)', value=helpers2, inline=False)
    embed.add_field(name='HELPER SETTINGS', value=helper_settings, inline=False)
    return embed


async def embed_settings_portals(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                                 user_portals: List[portals.Portal]) -> discord.Embed:
    """Portals settings embed"""
    message_style = 'Embed' if user_settings.portals_as_embed else 'Normal message'
    portal_list = ''
    for index, portal in enumerate(user_portals):
        portal_list = f'{portal_list}\n{emojis.BP} {index + 1}: <#{portal.channel_id}> ({portal.channel_id})'
    if not portal_list: portal_list = f'{emojis.BP} _No portals set._'
    portal_settings = (
        f'{emojis.BP} **Message style**: `{message_style}`\n'
        f'{emojis.BP} **Mobile spacing**: {await functions.bool_to_text(user_settings.portals_spacing_enabled)}'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S PORTAL SETTINGS',
        description = '_Portals will take you to another channel. You can add up to 20 portals._'
    )
    embed.add_field(name='PORTALS', value=portal_list, inline=False)
    embed.add_field(name='SETTINGS', value=portal_settings, inline=False)
    return embed


async def embed_settings_messages(bot: discord.Bot, ctx: discord.ApplicationContext,
                                  user_settings: users.User, activity: str) -> List[discord.Embed]:
    """Reminder message specific activity embed"""
    embed_no = 1
    embed_descriptions = {embed_no: ''}
    embeds = []
    if activity == 'all':
        description = ''
        for activity in strings.ACTIVITIES:
            title = f'{ctx.author.name.upper()}\'S REMINDER MESSAGES'
            activity_column = strings.ACTIVITIES_COLUMNS[activity]
            alert = getattr(user_settings, activity_column)
            alert_message = (
                f'{emojis.BP} **{activity.replace("-"," ").capitalize()}**\n'
                f'{emojis.DETAIL} {alert.message}'
            )
            activity = activity.replace('-',' ').capitalize()
            if len(embed_descriptions[embed_no]) + len(alert_message) > 4096:
                embed_no += 1
                embed_descriptions[embed_no] = ''
            embed_descriptions[embed_no] = f'{embed_descriptions[embed_no]}\n{alert_message}'
        for embed_no, description in embed_descriptions.items():
            embed = discord.Embed(
                color = settings.EMBED_COLOR,
                title = title if embed_no < 2 else None,
                description = description
            )
            embeds.append(embed)
    else:
        activity_column = strings.ACTIVITIES_COLUMNS[activity]
        alert = getattr(user_settings, activity_column)
        title = f'{activity.replace("-"," ")} REMINDER MESSAGE'.upper()
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = title if embed_no < 2 else None
        )
        allowed_placeholders = ''
        for placeholder_match in re.finditer('\{(.+?)\}', strings.DEFAULT_MESSAGES[activity]):
            placeholder = placeholder_match.group(1)
            placeholder_description = strings.PLACEHOLDER_DESCRIPTIONS.get(placeholder, '')
            allowed_placeholders = (
                f'{allowed_placeholders}\n'
                f'{emojis.BP} **{{{placeholder}}}**'
            )
            if placeholder_description != '':
                allowed_placeholders = f'{allowed_placeholders}\n{emojis.DETAIL}_{placeholder_description}_'
        if allowed_placeholders == '':
            allowed_placeholders = f'_There are no placeholders available for this message._'
        embed.add_field(name='CURRENT MESSAGE', value=f'{emojis.BP} {alert.message}', inline=False)
        embed.add_field(name='SUPPORTED PLACEHOLDERS', value=allowed_placeholders.strip(), inline=False)
        embeds = [embed,]

    return embeds


async def embed_settings_multipliers(bot: discord.Bot, ctx: discord.ApplicationContext,
                                     user_settings: users.User) -> discord.Embed:
    """Reminder multiplier settings embed"""
    multipliers = (
        f'{emojis.BP} **Adventure**: `{user_settings.alert_adventure.multiplier}`\n'
        #f'{emojis.BP} **Chimney** {emojis.XMAS_SOCKS}: `{user_settings.alert_chimney.multiplier}`\n'
        f'{emojis.BP} **Daily**: `{user_settings.alert_daily.multiplier}`\n'
        f'{emojis.BP} **Duel**: `{user_settings.alert_duel.multiplier}`\n'
        f'{emojis.BP} **EPIC items**: `{user_settings.alert_epic.multiplier}`\n'
        f'{emojis.BP} **Farm**: `{user_settings.alert_farm.multiplier}`\n'
        f'{emojis.BP} **Hunt**: `{user_settings.alert_hunt.multiplier}`\n'
        f'{emojis.BP} **Lootbox**: `{user_settings.alert_lootbox.multiplier}`\n'
        f'{emojis.BP} **Quest**: `{user_settings.alert_quest.multiplier}`\n'
        f'{emojis.BP} **Training**: `{user_settings.alert_training.multiplier}`\n'
        f'{emojis.BP} **Weekly**: `{user_settings.alert_weekly.multiplier}`\n'
        f'{emojis.BP} **Work**: `{user_settings.alert_work.multiplier}`\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S REMINDER MULTIPLIERS',
        description = (
            f'_Multipliers are applied to all reminder times._\n'
            f'_These are for **personal** differences (e.g. area 18, returning event)._\n'
            f'_These are **not** for global event reductions. Those are set by your Navi admin and can be '
            f'viewed in {await functions.get_navi_slash_command(bot, "event-reductions")}._\n'
        )
    )
    embed.add_field(name='MULTIPLIERS', value=multipliers, inline=False)
    return embed


async def embed_settings_partner(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                                 partner_settings: Optional[users.User] = None) -> discord.Embed:
    """Partner settings embed"""
    partner = partner_partner_channel = user_partner_channel = partner_alert_threshold = '`N/A`'
    if user_settings.partner_channel_id is not None:
        user_partner_channel = f'<#{user_settings.partner_channel_id}>'
    if partner_settings is not None:
        partner = f'<@{user_settings.partner_id}>'
        if partner_settings.partner_channel_id is not None:
            partner_partner_channel = f'<#{partner_settings.partner_channel_id}>'
        partner_alert_threshold_name = list(strings.LOOTBOXES.keys())[partner_settings.partner_alert_threshold]
        partner_alert_threshold = f'{strings.LOOTBOXES[partner_alert_threshold_name]} `{partner_alert_threshold_name}`'
    user_alert_threshold_name = list(strings.LOOTBOXES.keys())[user_settings.partner_alert_threshold]
    user_partner_alert_threshold = f'{strings.LOOTBOXES[user_alert_threshold_name]} `{user_alert_threshold_name}`'
    partner_donor_tier = strings.DONOR_TIERS[user_settings.partner_donor_tier]
    partner_donor_tier_emoji = strings.DONOR_TIERS_EMOJIS[partner_donor_tier]
    partner_donor_tier = f'{partner_donor_tier_emoji} `{partner_donor_tier}`'.lstrip('None ')
    partner_pocket_watch_reduction = 100 - (100 * user_settings.partner_pocket_watch_multiplier)
    donor_tier = (
        f'{emojis.BP} **Partner donor tier**: {partner_donor_tier}\n'
        f'{emojis.BP} **Partner pocket watch reduction**: `{partner_pocket_watch_reduction:g}` %\n'
        f'_You can only change these settings if you have no partner set._\n'
        f'_If you do, this is synchronized with your partner instead._\n'
    )
    settings_user = (
        f'{emojis.BP} **Partner**: {partner}\n'
        f'{emojis.BP} **Partner alert channel**: {user_partner_channel}\n'
        f'{emojis.DETAIL} _Lootbox alerts are sent to this channel._\n'
        f'{emojis.BP} **Partner alert lootbox threshold**: {user_partner_alert_threshold}\n'
    )
    settings_partner = (
        f'{emojis.BP} **Partner alert channel**: {partner_partner_channel}\n'
        f'{emojis.BP} **Partner alert lootbox threshold**: {partner_alert_threshold}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S PARTNER SETTINGS',
        description = (
            f'_Settings for your partner. To add or change your partner, use the menu below._\n'
        )
    )
    embed.add_field(name='EPIC RPG DONOR TIER & POCKET WATCH', value=donor_tier, inline=False)
    embed.add_field(name='YOUR SETTINGS', value=settings_user, inline=False)
    embed.add_field(name='YOUR PARTNER\'S SETTINGS', value=settings_partner, inline=False)
    return embed


async def embed_settings_ready(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                               clan_settings: Optional[clans.Clan] = None) -> discord.Embed:
    """Ready settings embed"""
    async def bool_to_text(boolean: bool) -> str:
        return f'{emojis.ENABLED}`Visible`' if boolean else f'{emojis.DISABLED}`Hidden`'

    if clan_settings is None:
        clan_alert_visible = '`N/A`'
    else:
        clan_alert_visible = await bool_to_text(clan_settings.alert_visible)
    auto_ready_enabled = f'{emojis.ENABLED}`Enabled`' if user_settings.auto_ready_enabled else f'{emojis.DISABLED}`Disabled`'
    ping_user_enabled = f'{emojis.ENABLED}`Enabled`' if user_settings.ready_ping_user else f'{emojis.DISABLED}`Disabled`'
    frequency = 'After all commands' if user_settings.ready_after_all_commands else 'After hunt only'
    message_style = 'Embed' if user_settings.ready_as_embed else 'Normal message'
    up_next_tyle = 'Timestamp' if user_settings.ready_up_next_as_timestamp else 'Static time'
    if user_settings.ready_up_next_show_hidden_reminders:
        up_next_hidden_reminders = f'{emojis.ENABLED}`Enabled`'
    else:
        up_next_hidden_reminders = f'{emojis.DISABLED}`Disabled`'
    other_field_position = 'Top' if user_settings.ready_other_on_top else 'Bottom'
    if user_settings.ready_pets_claim_after_every_pet:
        pets_claim_type = 'After every pet'
    else:
        pets_claim_type = 'When all pets are back'
    field_settings = (
        f'{emojis.BP} **Auto-ready**: {auto_ready_enabled}\n'
        f'{emojis.BP} **Auto-ready frequency**: `{frequency}`\n'
        f'{emojis.BP} **Auto-ready pings user**: {ping_user_enabled}\n'
        f'{emojis.BP} **Message style**: `{message_style}`\n'
        f'{emojis.BP} **Embed color**: `#{user_settings.ready_embed_color}`\n'
        f'{emojis.BP} **Guild channel reminder**: {clan_alert_visible}\n'
        f'{emojis.BP} **{strings.SLASH_COMMANDS["pets claim"]} type**: `{pets_claim_type}`\n'
        f'{emojis.BP} **Position of "other commands"**: `{other_field_position}`\n'
    )
    trade_daily = (
        f'_Daily trades will only show up if you have a top hat!_\n'
        f'{emojis.BP} **Daily trades**: {await bool_to_text(user_settings.ready_trade_daily_visible)}\n'
        f'{emojis.BP} **When daily trades are done**: {await bool_to_text(user_settings.ready_trade_daily_completed_visible)}\n'
    )
    up_next_reminder = (
        f'{emojis.BP} **Reminder**: {await bool_to_text(user_settings.ready_up_next_visible)}\n'
        f'{emojis.BP} **Style**: `{up_next_tyle}`\n'
        f'{emojis.DETAIL} _If timestamps are inaccurate, set your local time correctly._\n'
        f'{emojis.BP} **Also show hidden reminders**: {up_next_hidden_reminders}\n'
    )
    other_commands = (
        f'{emojis.BP} **{strings.SLASH_COMMANDS["cd"]} command**: '
        f'{await bool_to_text(user_settings.cmd_cd_visible)}\n'
        f'{emojis.BP} **{strings.SLASH_COMMANDS["inventory"]} command**: '
        f'{await bool_to_text(user_settings.cmd_inventory_visible)}\n'
        f'{emojis.BP} **{await functions.get_navi_slash_command(bot, "ready")} command**: '
        f'{await bool_to_text(user_settings.cmd_ready_visible)}\n'
        f'{emojis.BP} **{await functions.get_navi_slash_command(bot, "slashboard")} command**: '
        f'{await bool_to_text(user_settings.cmd_slashboard_visible)}\n'
    )
    command_event_reminders = (
        f'{emojis.BP} _Choose "Manage visible commands and command channels" below to change these settings._'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S READY LIST SETTINGS',
        description = (
            f'_General settings for the {await functions.get_navi_slash_command(bot, "ready")} list._\n'
            f'_Note that the ready list does not list commands for reminders that are turned off._'
        )
    )
    embed.add_field(name='SETTINGS', value=field_settings, inline=False)
    embed.add_field(name='DAILY TRADES', value=trade_daily, inline=False)
    embed.add_field(name='UP NEXT REMINDER', value=up_next_reminder, inline=False)
    embed.add_field(name='OTHER COMMANDS', value=other_commands, inline=False)
    embed.add_field(name='VISIBLE COMMANDS & COMMAND CHANNELS', value=command_event_reminders, inline=False)
    return embed


async def embed_settings_ready_reminders(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                                         clan_settings: Optional[clans.Clan] = None) -> discord.Embed:
    """Ready reminders settings embed"""
    async def bool_to_text(boolean: bool) -> str:
        return f'{emojis.ENABLED}`Visible`' if boolean else f'{emojis.DISABLED}`Hidden`'

    if user_settings.ready_channel_arena is not None:
        channel_arena = f'<#{user_settings.ready_channel_arena}>'
    else:
        channel_arena = '`N/A`'
    if user_settings.ready_channel_duel is not None:
        channel_duel = f'<#{user_settings.ready_channel_duel}>'
    else:
        channel_duel = '`N/A`'
    if user_settings.ready_channel_dungeon is not None:
        channel_dungeon = f'<#{user_settings.ready_channel_dungeon}>'
    else:
        channel_dungeon = '`N/A`'
    if user_settings.ready_channel_horse is not None:
        channel_horse = f'<#{user_settings.ready_channel_horse}>'
    else:
        channel_horse = '`N/A`'

    command_reminders = (
        #f'{emojis.BP} **Advent calendar** {emojis.XMAS_SOCKS}: {await bool_to_text(user_settings.alert_advent.visible)}\n'
        f'{emojis.BP} **Adventure**: {await bool_to_text(user_settings.alert_adventure.visible)}\n'
        f'{emojis.BP} **Arena**: {await bool_to_text(user_settings.alert_arena.visible)}\n'
        f'{emojis.BP} **Boo** {emojis.PUMPKIN}: {await bool_to_text(user_settings.alert_boo.visible)}\n'
        #f'{emojis.BP} **Cel dailyquest** {emojis.COIN_CELEBRATION}: '
        #f'{await bool_to_text(user_settings.alert_cel_dailyquest.visible)}\n'
        #f'{emojis.BP} **Cel multiply** {emojis.COIN_CELEBRATION}: '
        #f'{await bool_to_text(user_settings.alert_cel_multiply.visible)}\n'
        #f'{emojis.BP} **Cel sacrifice** {emojis.COIN_CELEBRATION}: '
        #f'{await bool_to_text(user_settings.alert_cel_sacrifice.visible)}\n'
        #f'{emojis.BP} **Chimney** {emojis.XMAS_SOCKS}: {await bool_to_text(user_settings.alert_chimney.visible)}\n'
        f'{emojis.BP} **Daily**: {await bool_to_text(user_settings.alert_daily.visible)}\n'
        f'{emojis.BP} **Duel**: {await bool_to_text(user_settings.alert_duel.visible)}\n'
        f'{emojis.BP} **Dungeon / Miniboss**: {await bool_to_text(user_settings.alert_dungeon_miniboss.visible)}\n'
        f'{emojis.BP} **EPIC items**: {await bool_to_text(user_settings.alert_epic.visible)}\n'
        f'{emojis.BP} **Farm**: {await bool_to_text(user_settings.alert_farm.visible)}\n'
        f'{emojis.BP} **Guild**: {await bool_to_text(user_settings.alert_guild.visible)}\n'
        f'{emojis.BP} **Horse**: {await bool_to_text(user_settings.alert_horse_breed.visible)}\n'
    )
    command_reminders2 = (
        f'{emojis.BP} **Hunt**: {await bool_to_text(user_settings.alert_hunt.visible)}\n'
        f'{emojis.BP} **Lootbox**: {await bool_to_text(user_settings.alert_lootbox.visible)}\n'
        #f'{emojis.BP} **Megarace**: {await bool_to_text(user_settings.alert_megarace.visible)}\n'
        #f'{emojis.BP} **Minirace**: {await bool_to_text(user_settings.alert_minirace.visible)}\n'
        f'{emojis.BP} **Pets**: {await bool_to_text(user_settings.alert_pets.visible)}\n'
        f'{emojis.BP} **Quest**: {await bool_to_text(user_settings.alert_quest.visible)}\n'
        f'{emojis.BP} **Training**: {await bool_to_text(user_settings.alert_training.visible)}\n'
        f'{emojis.BP} **Vote**: {await bool_to_text(user_settings.alert_vote.visible)}\n'
        f'{emojis.BP} **Weekly**: {await bool_to_text(user_settings.alert_weekly.visible)}\n'
        f'{emojis.BP} **Work**: {await bool_to_text(user_settings.alert_work.visible)}\n'
    )
    event_reminders = (
        f'{emojis.BP} **Big arena**: {await bool_to_text(user_settings.alert_big_arena.visible)}\n'
        f'{emojis.BP} **Horse race**: {await bool_to_text(user_settings.alert_horse_race.visible)}\n'
        f'{emojis.BP} **Lottery**: {await bool_to_text(user_settings.alert_lottery.visible)}\n'
        f'{emojis.BP} **Minin\'tboss**: {await bool_to_text(user_settings.alert_not_so_mini_boss.visible)}\n'
        f'{emojis.BP} **Pet tournament**: {await bool_to_text(user_settings.alert_pet_tournament.visible)}\n'
    )
    command_channels = (
        f'_Command channels are shown below the corresponding ready command._\n'
        f'{emojis.BP} **Arena channel**: {channel_arena}\n'
        f'{emojis.BP} **Duel channel**: {channel_duel}\n'
        f'{emojis.BP} **Dungeon channel**: {channel_dungeon}\n'
        f'{emojis.BP} **Horse breed channel**: {channel_horse}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S READY LIST REMINDER SETTINGS',
        description = (
            f'_Settings to toggle visibility of reminders in {await functions.get_navi_slash_command(bot, "ready")}._\n'
            f'_Hiding a reminder removes it from the ready list but does **not** disable the reminder itself._'
        )
    )
    embed.add_field(name='COMMAND REMINDERS I', value=command_reminders, inline=False)
    embed.add_field(name='COMMAND REMINDERS II', value=command_reminders2, inline=False)
    embed.add_field(name='EVENT REMINDERS', value=event_reminders, inline=False)
    embed.add_field(name='COMMAND CHANNELS', value=command_channels, inline=False)
    return embed


async def embed_settings_reminders(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   user_settings: users.User) -> discord.Embed:
    """Reminder settings embed"""
    reminder_channel = '`Last channel the reminder was updated in`'
    if user_settings.reminder_channel_id is not None:
        reminder_channel = f'<#{user_settings.reminder_channel_id}>'
    behaviour = (
        f'{emojis.BP} **DND mode**: {await functions.bool_to_text(user_settings.dnd_mode_enabled)}\n'
        f'{emojis.DETAIL} _If DND mode is enabled, Navi won\'t ping you._\n'
        f'{emojis.BP} **Hunt rotation**: {await functions.bool_to_text(user_settings.hunt_rotation_enabled)}\n'
        f'{emojis.DETAIL} _Rotates hunt reminders between `hunt` and `hunt together`._\n'
        f'{emojis.BP} **Slash commands in reminders**: {await functions.bool_to_text(user_settings.slash_mentions_enabled)}\n'
        f'{emojis.DETAIL} _If you can\'t see slash mentions properly, update your Discord app._\n'
        f'{emojis.BP} **Reminder channel**: {reminder_channel}\n'
        f'{emojis.DETAIL} _If a channel is set, all reminders are sent to that channel._\n'
        #f'{emojis.BP} **Christmas area mode** {emojis.XMAS_SOCKS}: {await functions.bool_to_text(user_settings.christmas_area_enabled)}\n'
        #f'{emojis.DETAIL} _Reduces your reminders by 10%._\n'
    )
    command_reminders = (
        #f'{emojis.BP} **Advent calendar** {emojis.XMAS_SOCKS}: '
        #f'{await functions.bool_to_text(user_settings.alert_advent.enabled)}\n'
        f'{emojis.BP} **Adventure**: {await functions.bool_to_text(user_settings.alert_adventure.enabled)}\n'
        f'{emojis.BP} **Arena**: {await functions.bool_to_text(user_settings.alert_arena.enabled)}\n'
        f'{emojis.BP} **Boo** {emojis.PUMPKIN}: {await functions.bool_to_text(user_settings.alert_boo.enabled)}\n'
        #f'{emojis.BP} **Chimney** {emojis.XMAS_SOCKS}: {await functions.bool_to_text(user_settings.alert_chimney.enabled)}\n'
        f'{emojis.BP} **Boost items**: {await functions.bool_to_text(user_settings.alert_boosts.enabled)}\n'
        #f'{emojis.BP} **Cel dailyquest** {emojis.COIN_CELEBRATION}: '
        #f'{await functions.bool_to_text(user_settings.alert_cel_dailyquest.enabled)}\n'
        #f'{emojis.BP} **Cel multiply** {emojis.COIN_CELEBRATION}: '
        #f'{await functions.bool_to_text(user_settings.alert_cel_multiply.enabled)}\n'
        #f'{emojis.BP} **Cel sacrifice** {emojis.COIN_CELEBRATION}: '
        #f'{await functions.bool_to_text(user_settings.alert_cel_sacrifice.enabled)}\n'
        f'{emojis.BP} **Daily**: {await functions.bool_to_text(user_settings.alert_daily.enabled)}\n'
        f'{emojis.BP} **Duel**: {await functions.bool_to_text(user_settings.alert_duel.enabled)}\n'
        f'{emojis.BP} **Dungeon / Miniboss**: {await functions.bool_to_text(user_settings.alert_dungeon_miniboss.enabled)}\n'
        f'{emojis.BP} **EPIC items**: {await functions.bool_to_text(user_settings.alert_epic.enabled)}\n'
        f'{emojis.BP} **Farm**: {await functions.bool_to_text(user_settings.alert_farm.enabled)}\n'
        f'{emojis.BP} **Guild**: {await functions.bool_to_text(user_settings.alert_guild.enabled)}\n'
        f'{emojis.DETAIL} _For the guild channel reminder switch to `Guild settings`._\n'
        f'{emojis.BP} **Horse**: {await functions.bool_to_text(user_settings.alert_horse_breed.enabled)}\n'
    )
    command_reminders2 = (
        f'{emojis.BP} **Hunt**: {await functions.bool_to_text(user_settings.alert_hunt.enabled)}\n'
        f'{emojis.BP} **Lootbox**: {await functions.bool_to_text(user_settings.alert_lootbox.enabled)}\n'
        f'{emojis.BP} **Maintenance**: {await functions.bool_to_text(user_settings.alert_maintenance.enabled)}\n'
        #f'{emojis.BP} **Megarace**: {await functions.bool_to_text(user_settings.alert_megarace.enabled)}\n'
        #f'{emojis.BP} **Minirace**: {await functions.bool_to_text(user_settings.alert_minirace.enabled)}\n'
        f'{emojis.BP} **Partner alert**: {await functions.bool_to_text(user_settings.alert_partner.enabled)}\n'
        f'{emojis.DETAIL} _Lootbox alerts are sent to this channel._\n'
        f'{emojis.DETAIL} _Requires a partner alert channel set in `Partner settings`._\n'
        f'{emojis.BP} **Pets**: {await functions.bool_to_text(user_settings.alert_pets.enabled)}\n'
        f'{emojis.BP} **Quest**: {await functions.bool_to_text(user_settings.alert_quest.enabled)}\n'
        f'{emojis.BP} **Training**: {await functions.bool_to_text(user_settings.alert_training.enabled)}\n'
        f'{emojis.BP} **Vote**: {await functions.bool_to_text(user_settings.alert_vote.enabled)}\n'
        f'{emojis.BP} **Weekly**: {await functions.bool_to_text(user_settings.alert_weekly.enabled)}\n'
        f'{emojis.BP} **Work**: {await functions.bool_to_text(user_settings.alert_work.enabled)}'
    )
    event_reminders = (
        f'{emojis.BP} **Big arena**: {await functions.bool_to_text(user_settings.alert_big_arena.enabled)}\n'
        f'{emojis.BP} **Horse race**: {await functions.bool_to_text(user_settings.alert_horse_race.enabled)}\n'
        f'{emojis.BP} **Lottery**: {await functions.bool_to_text(user_settings.alert_lottery.enabled)}\n'
        f'{emojis.BP} **Minin\'tboss**: {await functions.bool_to_text(user_settings.alert_not_so_mini_boss.enabled)}\n'
        f'{emojis.BP} **Pet tournament**: {await functions.bool_to_text(user_settings.alert_pet_tournament.enabled)}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S REMINDER SETTINGS',
        description = (
            f'_Settings to toggle your reminders._\n'
            f'_Note that disabling a reminder also deletes the reminder from my database._'
        )
    )
    embed.add_field(name='REMINDER BEHAVIOUR', value=behaviour, inline=False)
    embed.add_field(name='REMINDERS (I)', value=command_reminders, inline=False)
    embed.add_field(name='REMINDERS (II)', value=command_reminders2, inline=False)
    embed.add_field(name='EVENT REMINDERS', value=event_reminders, inline=False)
    return embed


async def embed_settings_server(bot: discord.Bot, ctx: discord.ApplicationContext,
                                guild_settings: guilds.Guild) -> discord.Embed:
    """Server settings embed"""
    if guild_settings.auto_flex_channel_id is not None:
        auto_flex_channel = f'<#{guild_settings.auto_flex_channel_id}>'
    else:
        auto_flex_channel = '`N/A`'
    server_settings = (
        f'{emojis.BP} **Prefix**: `{guild_settings.prefix}`\n'
        f'{emojis.DETAIL} _If you want to have a space after the prefix, you need to input it as `"prefix "`._'
        f'{emojis.BP} **Auto flex**: {await functions.bool_to_text(guild_settings.auto_flex_enabled)}\n'
        f'{emojis.BP} **Auto flex channel**: {auto_flex_channel}\n'
    )
    auto_flex_alerts_1 = (
        f'{emojis.BP} Alchemy: **Brew electronical potion**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_brew_electronical_enabled)}\n'
        f'{emojis.BP} Artifacts: **Craft an artifact**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_artifacts_enabled)}\n'
        f'{emojis.BP} Drop: **EPIC berries from `hunt` or `adventure`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_epic_berry_enabled)}\n'
        f'{emojis.BP} Drop: **EPIC berries from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_epicberry_enabled)}\n'
        f'{emojis.BP} Drop: **GODLY lootbox from `hunt` or `adventure`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_godly_enabled)}\n'
        f'{emojis.BP} Drop: **HYPER logs from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_hyperlog_enabled)}\n'
        f'{emojis.BP} Drop: **OMEGA lootbox from `hunt` or `adventure`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_omega_enabled)}\n'
        f'{emojis.DETAIL} _Hardmode drops only count if it\'s `3` or more._\n'
        f'{emojis.BP} Drop: **Lost lootboxes in area 18**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_a18_enabled)}\n'
        f'{emojis.BP} Drop: **Party popper from any lootbox**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_party_popper_enabled)}\n'
    )
    auto_flex_alerts_2 = (
        f'{emojis.BP} Drop: **SUPER fish from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_superfish_enabled)}\n'
        f'{emojis.BP} Drop: **TIME capsule from GODLY lootbox**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_godly_tt_enabled)}\n'
        f'{emojis.BP} Drop: **ULTIMATE logs from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_ultimatelog_enabled)}\n'
        f'{emojis.BP} Drop: **ULTRA log from EDGY lootbox**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_edgy_ultra_enabled)}\n'
        f'{emojis.BP} Drop: **ULTRA log from OMEGA lootbox**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_omega_ultra_enabled)}\n'
        f'{emojis.BP} Drop: **ULTRA logs from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_ultralog_enabled)}\n'
        f'{emojis.BP} Drop: **VOID lootbox from `hunt` or `adventure`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_lb_void_enabled)}\n'
        f'{emojis.BP} Drop: **Watermelons from work commands**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_work_watermelon_enabled)}\n'
        f'{emojis.BP} Event: **Get ULTRA-EDGY in enchant event**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_enchant_enabled)}\n'
        f'{emojis.BP} Event: **Get 20 levels in farm event**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_farm_enabled)}\n'
        f'{emojis.BP} Event: **Kill mysterious man in heal event**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_heal_enabled)}\n'
    )
    auto_flex_alerts_3 = (
        f'{emojis.BP} Event: **Evolve OMEGA lootbox in lootbox event**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_lb_enabled)}\n'
        f'{emojis.BP} Event: **Successfully fly in void training event**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_training_enabled)}\n'
        f'{emojis.BP} Forging: **Forge GODLY cookie**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_forge_cookie_enabled)}\n'
        f'{emojis.BP} Gambling: **Lose coin in coinflip**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_event_coinflip_enabled)}\n'
        f'{emojis.BP} Pets: **Catch pet with EPIC skill in `training`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_pets_catch_epic_enabled)}\n'
        f'{emojis.BP} Pets: **Catch pet with timetraveler skill in `training`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_pets_catch_tt_enabled)}\n'
        f'{emojis.BP} Pets: **Get OMEGA lootbox from snowman pet**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_pets_claim_omega_enabled)}\n'
        f'{emojis.BP} Progress: **Ascension**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_pr_ascension_enabled)}\n'
        f'{emojis.BP} Progress: **Time travel milestones**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_time_travel_enabled)}\n'
        f'{emojis.DETAIL} _TT `1`, `3`, `5`, `10`, `25`, `50`, `100`, `150`, `200`, `250` and `300`_\n'
    )
    auto_flex_alerts_seasonal = (
        f'{emojis.BP} Christmas: **Get stuck in `xmas chimney`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_xmas_chimney_enabled)}\n'
        f'{emojis.BP} Christmas: **Drop EPIC snowballs**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_xmas_snowball_enabled)}\n'
        f'{emojis.BP} Christmas: **Drop GODLY presents**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_xmas_godly_enabled)}\n'
        f'{emojis.BP} Christmas: **Drop VOID presents**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_xmas_void_enabled)}\n'
        f'{emojis.BP} Halloween: **Drop sleepy potion or suspicious broom in `hal boo`**: '
        f'{await functions.bool_to_text(guild_settings.auto_flex_hal_boo_enabled)}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.guild.name.upper()} SERVER SETTINGS',
        description = (
            f'_Serverwide settings._\n'
            f'_Note that due to their rarity, some auto flexes may only be picked up in **English**._\n'
        )
    )
    embed.add_field(name='SETTINGS', value=server_settings, inline=False)
    embed.add_field(name='AUTO FLEXES (I)', value=auto_flex_alerts_1, inline=False)
    embed.add_field(name='AUTO FLEXES (II)', value=auto_flex_alerts_2, inline=False)
    embed.add_field(name='AUTO FLEXES (III)', value=auto_flex_alerts_3, inline=False)
    embed.add_field(name='AUTO FLEXES (SEASONAL)', value=auto_flex_alerts_seasonal, inline=False)
    return embed


async def embed_settings_user(bot: discord.Bot, ctx: discord.ApplicationContext,
                              user_settings: users.User) -> discord.Embed:
    """User settings embed"""
    try:
        tt_timestamp = int(user_settings.last_tt.replace(tzinfo=timezone.utc).timestamp())
    except OSError as error: # Windows throws an error if datetime is set to 0 apparently
        tt_timestamp = 0
    ascension = 'Ascended' if user_settings.ascended else 'Not ascended'
    user_donor_tier = strings.DONOR_TIERS[user_settings.user_donor_tier]
    user_donor_tier_emoji = strings.DONOR_TIERS_EMOJIS[user_donor_tier]
    user_donor_tier = f'{user_donor_tier_emoji} `{user_donor_tier}`'.lstrip('None ')
    partner_donor_tier = strings.DONOR_TIERS[user_settings.partner_donor_tier]
    partner_donor_tier_emoji = strings.DONOR_TIERS_EMOJIS[partner_donor_tier]
    partner_donor_tier = f'{partner_donor_tier_emoji} `{partner_donor_tier}`'.lstrip('None ')
    user_pocket_watch_reduction = 100 - (user_settings.user_pocket_watch_multiplier * 100)
    partner_pocket_watch_reduction = 100 - (user_settings.partner_pocket_watch_multiplier * 100)

    bot = (
        f'{emojis.BP} **Bot**: {await functions.bool_to_text(user_settings.bot_enabled)}\n'
        f'{emojis.DETAIL} _You can toggle this by using {await functions.get_navi_slash_command(bot, "on")} '
        f'and {await functions.get_navi_slash_command(bot, "off")}._\n'
        f'{emojis.BP} **Reactions**: {await functions.bool_to_text(user_settings.reactions_enabled)}\n'
        f'{emojis.BP} **Auto flex**: {await functions.bool_to_text(user_settings.auto_flex_enabled)}\n'
        f'{emojis.DETAIL} _Auto flexing only works if it\'s also enabled in the server settings._\n'
        f'{emojis.DETAIL} _Some flexes are **English only**._\n'
    )
    epic_rpg_user = (
        f'{emojis.BP} **Donor tier**: {user_donor_tier}\n'
        f'{emojis.BP} **Pocket watch reduction**: `{user_pocket_watch_reduction:g}` %\n'
        f'{emojis.DETAIL} _Use {strings.SLASH_COMMANDS["artifacts"]} to update this setting._\n'
        f'{emojis.BP} **Ascension**: `{ascension}`\n'
        f'{emojis.DETAIL} _Use {strings.SLASH_COMMANDS["professions stats"]} to update this setting._\n'
    )
    epic_rpg_partner = (
        f'{emojis.BP} **Donor tier**: {partner_donor_tier}\n'
        f'{emojis.BP} **Pocket watch reduction**: `{partner_pocket_watch_reduction:g}` %\n'
        f'_You can only change these settings if you have no partner set._\n'
        f'_If you do, this is synchronized with your partner instead._\n'
    )
    tracking = (
        f'{emojis.BP} **Command tracking**: {await functions.bool_to_text(user_settings.tracking_enabled)}\n'
        f'{emojis.BP} **Last time travel**: <t:{tt_timestamp}:f>\n'
        f'{emojis.DETAIL} _This is used to calculate your command count since last TT._\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S USER SETTINGS',
        description = (
            f'_Various user settings. If you are married, also check out `Partner settings`._\n'
        )
    )
    embed.add_field(name='MAIN', value=bot, inline=False)
    embed.add_field(name='YOUR EPIC RPG SETTINGS', value=epic_rpg_user, inline=False)
    embed.add_field(name='YOUR PARTNER\'S EPIC RPG SETTINGS', value=epic_rpg_partner, inline=False)
    embed.add_field(name='TRACKING', value=tracking, inline=False)
    return embed