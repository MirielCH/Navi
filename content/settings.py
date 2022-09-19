# settings_clan.py
"""Contains clan settings commands"""

import re
from typing import List, Optional, Union

import discord
from discord.ext import commands

from content import settings as settings_cmd
from database import clans, reminders, users
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
    'track': 'tracking',
    'commandtrack': 'tracking',
    'commandtracking': 'tracking',
    'command-tracking': 'tracking',
    'command-track': 'tracking',
    'cmd-track': 'tracking',
    'cmd-tracking': 'tracking',
    'cmdtrack': 'tracking',
    'cmdtracking': 'tracking',
}

SETTINGS_USER_COLUMNS = {
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
            f'Click the button below or use {strings.SLASH_COMMANDS_NAVI["settings user"]}.'
        )
        field_tracking = (
            f'I track the amount of some EPIC RPG commands you use. Check '
            f'{strings.SLASH_COMMANDS_NAVI["stats"]} to see what commands are tracked.\n'
            f'**__No personal data is processed or stored in any way!__**\n'
            f'You can opt-out of command tracking in {strings.SLASH_COMMANDS_NAVI["stats"]} or in your user settings.\n\n'
        )
        field_privacy = (
            f'To read more about what data is processed and why, feel free to check the privacy policy found in '
            f'{strings.SLASH_COMMANDS_NAVI["help"]}.'
        )
        img_navi = discord.File(settings.IMG_NAVI, filename='navi.png')
        image_url = 'attachment://navi.png'
        embed = discord.Embed(
            title = f'Hey! {ctx.author.name}! Hello!'.upper(),
            description = (
                f'I am here to help you with your EPIC RPG commands!\n'
                f'Have a look at {strings.SLASH_COMMANDS_NAVI["help"]} for a list of my own commands.'
            ),
            color =  settings.EMBED_COLOR,
        )
        embed.add_field(name='SETTINGS', value=field_settings, inline=False)
        embed.add_field(name='COMMAND TRACKING', value=field_tracking, inline=False)
        embed.add_field(name='PRIVACY POLICY', value=field_privacy, inline=False)
        embed.set_thumbnail(url=image_url)
        view = views.OneButtonView(ctx, discord.ButtonStyle.blurple, 'pressed', '➜ Settings')
        interaction = await ctx.respond(embed=embed, file=img_navi, view=view)
        view.interaction = interaction
        await view.wait()
        if view.value == 'pressed':
            await functions.edit_interaction(interaction, view=None)
            await settings_cmd.command_settings_user(bot, ctx)


async def command_off(bot: discord.Bot, ctx: discord.ApplicationContext) -> None:
    """Off command"""
    user: users.User = await users.get_user(ctx.author.id)
    if not user.bot_enabled:
        await ctx.respond(f'**{ctx.author.name}**, I\'m already turned off.', ephemeral=True)
        return
    answer = (
        f'**{ctx.author.name}**, turning me off will disable me completely. This includes all helpers, the command '
        f'tracking and the reminders. It will also delete all of your active reminders.\n'
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
                f'Your guild is not registered with me yet. Use {strings.SLASH_COMMANDS_NEW["guild list"]} '
                f'to do that first.',
                ephemeral=True
            )
            return
    if switch_view is not None: switch_view.stop()
    view = views.SettingsClanView(ctx, bot, clan_settings, embed_settings_clan)
    embed = await embed_settings_clan(bot, clan_settings)
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


async def command_settings_partner(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   new_partner: Optional[discord.User] = None,
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
    if new_partner is None:
        view = views.SettingsPartnerView(ctx, bot, user_settings, partner_settings, embed_settings_partner)
        embed = await embed_settings_partner(bot, ctx, user_settings, partner_settings)
        if interaction is None:
            interaction = await ctx.respond(embed=embed, view=view)
        else:
            await functions.edit_interaction(interaction, embed=embed, view=view)
        view.interaction = interaction
        await view.wait()
    else:
        try:
            new_partner_settings: users.User = await users.get_user(new_partner.id)
        except exceptions.FirstTimeUserError:
            await ctx.respond(
                f'**{new_partner.name}** is not registered with this bot yet. They need to do '
                f'{strings.SLASH_COMMANDS_NAVI["on"]} first.'
            )
            return
        if user_settings.partner_id is not None:
            view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            interaction = await ctx.respond(
                f'**{ctx.author.name}**, you already have a partner set.\n'
                f'Setting a new partner will remove your old partner. Do you want to continue?',
                view=view
            )
            view.interaction_message = interaction
            await view.wait()
            if view.value is None:
                await functions.edit_interaction(interaction, content=f'**{ctx.author.name}**, you didn\'t answer in time.',
                                                 view=None)
                return
            elif view.value == 'confirm':
                await functions.edit_interaction(interaction, view=None)
            else:
                await functions.edit_interaction(interaction, content='Aborted.', view=None)
                return
        view = views.ConfirmMarriageView(ctx, new_partner)
        interaction = await ctx.respond(
            f'{new_partner.mention}, **{ctx.author.name}** wants to set you as their partner.\n'
            f'Do you want to grind together until... idk, drama?',
            view=view
        )
        view.interaction = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(interaction,
                                             content=f'**{ctx.author.name}**, your lazy partner didn\'t answer in time.',
                                             view=None)
        elif view.value == 'confirm':
            if user_settings.partner_id is not None:
                try:
                    old_partner_settings = await users.get_user(user_settings.partner_id)
                    await old_partner_settings.update(partner_id=None)
                except exceptions.NoDataFoundError:
                    pass
            await user_settings.update(partner_id=new_partner.id, partner_donor_tier=new_partner_settings.user_donor_tier)
            await new_partner_settings.update(partner_id=ctx.author.id, partner_donor_tier=user_settings.user_donor_tier)
            if user_settings.partner_id == new_partner.id and new_partner_settings.partner_id == ctx.author.id:
                answer = (
                    f'{emojis.BP} **{ctx.author.name}**, {new_partner.name} is now set as your partner!\n'
                    f'{emojis.BP} **{new_partner.name}**, {ctx.author.name} is now set as your partner!\n'
                    f'{emojis.BP} **{ctx.author.name}**, {ctx.author.name} is now set as your partner\'s partner!\n'
                    f'{emojis.BP} **{new_partner.name}**, ... wait what?\n\n'
                    f'Anyway, you may now kiss the brides.'
                )
                view = views.OneButtonView(ctx, discord.ButtonStyle.blurple, 'pressed', '➜ Partner settings')
                interaction = await ctx.respond(answer, view=view)
                view.interaction = interaction
                await view.wait()
                if view.value == 'pressed':
                    await functions.edit_interaction(interaction, view=None)
                    await settings_cmd.command_settings_partner(bot, ctx)
                await functions.edit_interaction(interaction, view=None)
                return
            else:
                await ctx.send(strings.MSG_ERROR)
                return
        else:
            await functions.edit_interaction(interaction,
                                             content=(
                                                 f'**{new_partner.name}** prefers to be forever alone.\n'
                                                 f'Stood up at the altar, that\'s gotta hurt, rip.'
                                             ),
                                             view=None)
            return


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
    for helper in SETTINGS_HELPERS:
        possible_helpers = f'{possible_helpers}\n{emojis.BP} `{helper}`'
    possible_user = 'User settings:'
    for setting in SETTINGS_USER:
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
async def embed_settings_clan(bot: discord.Bot, clan_settings: clans.Clan) -> discord.Embed:
    """Guild settings embed"""
    reminder_enabled = await functions.bool_to_text(clan_settings.alert_enabled)
    if clan_settings.upgrade_quests_enabled:
        clan_upgrade_quests = f'{emojis.GREENTICK}`Allowed`'
    else:
        clan_upgrade_quests = f'{emojis.REDTICK}`Not allowed`'
    if clan_settings.channel_id is not None:
        clan_channel = await functions.get_discord_channel(bot, clan_settings.channel_id)
        clan_channel_name = clan_channel.name
    else:
        clan_channel_name = 'N/A'
    if clan_settings.quest_user_id is not None:
        quest_user = f'<@{clan_settings.quest_user_id}>'
    else:
        quest_user = '`None`'

    overview = (
        f'{emojis.BP} **Name**: `{clan_settings.clan_name}`\n'
        f'{emojis.BP} **Owner**: <@{clan_settings.leader_id}>\n'
    )
    reminder = (
        f'{emojis.BP} **Guild channel**: `{clan_channel_name}`\n'
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
    members = f'{members.strip()}\n\n➜ _Use {strings.SLASH_COMMANDS_NEW["guild list"]} to update guild members._'
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
    helpers = (
        f'{emojis.BP} **Context helper**: {await functions.bool_to_text(user_settings.context_helper_enabled)}\n'
        f'{emojis.DETAIL} _Shows some helpful slash commands depending on context (slash only)._\n'
        f'{emojis.BP} **Heal warning**: {await functions.bool_to_text(user_settings.heal_warning_enabled)}\n'
        f'{emojis.DETAIL} _Warns you when you are about to die._\n'
        f'{emojis.BP} **Pet catch helper**: {await functions.bool_to_text(user_settings.pet_helper_enabled)}\n'
        f'{emojis.DETAIL} _Tells you which commands to use when you encounter a pet._\n'
        f'{emojis.BP} **Ruby counter**: {await functions.bool_to_text(user_settings.ruby_counter_enabled)}\n'
        f'{emojis.DETAIL} _Keeps track of your rubies and helps with ruby training._\n'
        f'{emojis.BP} **Training helper**: {await functions.bool_to_text(user_settings.training_helper_enabled)}\n'
        f'{emojis.DETAIL} _Provides the answers for all training types except ruby training._\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S HELPER SETTINGS',
        description = '_Settings to toggle some helpful little features._'
    )
    embed.add_field(name='HELPERS', value=helpers, inline=False)
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
        for placeholder in re.finditer('\{(.+?)\}', strings.DEFAULT_MESSAGES[activity]):
            allowed_placeholders = (
                f'{allowed_placeholders}\n'
                f'{emojis.BP} {{{placeholder.group(1)}}}'
            )
        if allowed_placeholders == '':
            allowed_placeholders = f'_There are no placeholders available for this message._'
        embed.add_field(name='CURRENT MESSAGE', value=f'{emojis.BP} {alert.message}', inline=False)
        embed.add_field(name='SUPPORTED PLACEHOLDERS', value=allowed_placeholders.strip(), inline=False)
        embeds = [embed,]

    return embeds


async def embed_settings_partner(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                                 partner_settings: Optional[users.User] = None) -> discord.Embed:
    """Partner settings embed"""
    user_partner_channel = await functions.get_discord_channel(bot, user_settings.partner_channel_id)
    user_partner_channel_name = partner = partner_hardmode_status = '`N/A`'
    partner_partner_channel_name = user_partner_channel_name = '`N/A`'
    if user_partner_channel is not None:
        user_partner_channel_name = f'`{user_partner_channel.name}`)'
    if partner_settings is not None:
        partner = f'<@{user_settings.partner_id}>'
        partner_hardmode_status = await functions.bool_to_text(partner_settings.hardmode_mode_enabled)
        partner_partner_channel = await functions.get_discord_channel(bot, partner_settings.partner_channel_id)
        if partner_partner_channel is not None:
            partner_partner_channel_name = f'`{partner_partner_channel.name}`)'
    donor_tier = (
        f'{emojis.BP} **Partner donor tier**: `{strings.DONOR_TIERS[user_settings.partner_donor_tier]}`\n'
        f'{emojis.DETAIL} _You can only change this if you have no partner set._\n'
        f'{emojis.DETAIL} _If you do, this is synchronized with your partner instead._'
    )
    settings_user = (
        f'{emojis.BP} **Partner**: {partner}\n'
        f'{emojis.BP} **Partner alert channel**: {user_partner_channel_name}\n'
        f'{emojis.DETAIL} _Lootbox and hardmode alerts are sent to this channel._\n'
    )
    settings_partner = (
        f'{emojis.BP} **Hardmode mode**: {partner_hardmode_status}\n'
        f'{emojis.BP} **Partner alert channel**: {partner_partner_channel_name}\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S PARTNER SETTINGS',
        description = (
            f'_Settings for your partner. To add or change your partner, use '
            f'{strings.SLASH_COMMANDS_NAVI["settings partner"]} `partner: @partner`._\n'
        )
    )
    embed.add_field(name='EPIC RPG DONOR TIER', value=donor_tier, inline=False)
    embed.add_field(name='YOUR SETTINGS', value=settings_user, inline=False)
    embed.add_field(name='YOUR PARTNER\'S SETTINGS', value=settings_partner, inline=False)
    return embed


async def embed_settings_ready(bot: discord.Bot, ctx: discord.ApplicationContext, user_settings: users.User,
                               clan_settings: Optional[clans.Clan] = None) -> discord.Embed:
    """Ready settings embed"""
    async def bool_to_text(boolean: bool) -> str:
        return f'{emojis.GREENTICK}`Visible`' if boolean else f'{emojis.REDTICK}`Hidden`'

    if clan_settings is None:
        clan_alert_visible = '`N/A`'
    else:
        clan_alert_visible = await bool_to_text(clan_settings.alert_visible)
    message_style = 'Embed' if user_settings.ready_as_embed else 'Normal message'
    other_field_position = 'Top' if user_settings.ready_other_on_top else 'Bottom'
    command_reminders = (
        f'{emojis.BP} **Adventure**: {await bool_to_text(user_settings.alert_adventure.visible)}\n'
        f'{emojis.BP} **Arena**: {await bool_to_text(user_settings.alert_arena.visible)}\n'
        f'{emojis.BP} **Daily**: {await bool_to_text(user_settings.alert_daily.visible)}\n'
        f'{emojis.BP} **Duel**: {await bool_to_text(user_settings.alert_duel.visible)}\n'
        f'{emojis.BP} **Dungeon / Miniboss**: {await bool_to_text(user_settings.alert_dungeon_miniboss.visible)}\n'
        f'{emojis.BP} **Farm**: {await bool_to_text(user_settings.alert_farm.visible)}\n'
        f'{emojis.BP} **Guild**: {await bool_to_text(user_settings.alert_guild.visible)}\n'
        f'{emojis.BP} **Horse**: {await bool_to_text(user_settings.alert_horse_breed.visible)}\n'
    )
    command_reminders2 = (
        f'{emojis.BP} **Hunt**: {await bool_to_text(user_settings.alert_hunt.visible)}\n'
        f'{emojis.BP} **Lootbox**: {await bool_to_text(user_settings.alert_lootbox.visible)}\n'
        f'{emojis.BP} **Quest**: {await bool_to_text(user_settings.alert_quest.visible)}\n'
        f'{emojis.BP} **Training**: {await bool_to_text(user_settings.alert_training.visible)}\n'
        f'{emojis.BP} **Vote**: {await bool_to_text(user_settings.alert_vote.visible)}\n'
        f'{emojis.BP} **Weekly**: {await bool_to_text(user_settings.alert_weekly.visible)}\n'
        f'{emojis.BP} **Work**: {await bool_to_text(user_settings.alert_work.visible)}'
    )
    event_reminders = (
        f'{emojis.BP} **Big arena**: {await bool_to_text(user_settings.alert_big_arena.visible)}\n'
        f'{emojis.BP} **Horse race**: {await bool_to_text(user_settings.alert_horse_race.visible)}\n'
        f'{emojis.BP} **Lottery**: {await bool_to_text(user_settings.alert_lottery.visible)}\n'
        f'{emojis.BP} **Minin\'tboss**: {await bool_to_text(user_settings.alert_not_so_mini_boss.visible)}\n'
        f'{emojis.BP} **Pet tournament**: {await bool_to_text(user_settings.alert_pet_tournament.visible)}\n'
    )
    field_settings = (
        f'{emojis.BP} **Guild channel reminder**: {clan_alert_visible}\n'
        f'{emojis.BP} **{strings.SLASH_COMMANDS_NEW["cd"]} command**: '
        f'{await bool_to_text(user_settings.cmd_cd_visible)}\n'
        f'{emojis.BP} **Message style**: `{message_style}`\n'
        f'{emojis.BP} **Position of "other" commands**: `{other_field_position}`\n'
    )
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = f'{ctx.author.name.upper()}\'S READY LIST SETTINGS',
        description = (
            f'_Settings to toggle visibility of reminders in {strings.SLASH_COMMANDS_NAVI["ready"]}._\n'
            f'_Hiding a reminder removes it from the ready list but does **not** disable the reminder itself._'
        )
    )
    embed.add_field(name='COMMAND REMINDERS I', value=command_reminders, inline=False)
    embed.add_field(name='COMMAND REMINDERS II', value=command_reminders2, inline=False)
    embed.add_field(name='EVENT REMINDERS', value=event_reminders, inline=False)
    embed.add_field(name='OTHER SETTINGS', value=field_settings, inline=False)
    return embed


async def embed_settings_reminders(bot: discord.Bot, ctx: discord.ApplicationContext,
                                   user_settings: users.User) -> discord.Embed:
    """Reminder settings embed"""
    command_reminders = (
        f'{emojis.BP} **Adventure**: {await functions.bool_to_text(user_settings.alert_adventure.enabled)}\n'
        f'{emojis.BP} **Arena**: {await functions.bool_to_text(user_settings.alert_arena.enabled)}\n'
        f'{emojis.BP} **Daily**: {await functions.bool_to_text(user_settings.alert_daily.enabled)}\n'
        f'{emojis.BP} **Duel**: {await functions.bool_to_text(user_settings.alert_duel.enabled)}\n'
        f'{emojis.BP} **Dungeon / Miniboss**: {await functions.bool_to_text(user_settings.alert_dungeon_miniboss.enabled)}\n'
        f'{emojis.BP} **Farm**: {await functions.bool_to_text(user_settings.alert_farm.enabled)}\n'
        f'{emojis.BP} **Guild**: {await functions.bool_to_text(user_settings.alert_guild.enabled)}\n'
        f'{emojis.DETAIL} _For the guild channel reminder switch to `Guild settings`._\n'
        f'{emojis.BP} **Horse**: {await functions.bool_to_text(user_settings.alert_horse_breed.enabled)}\n'
    )
    command_reminders2 = (
        f'{emojis.BP} **Hunt**: {await functions.bool_to_text(user_settings.alert_hunt.enabled)}\n'
        f'{emojis.BP} **Lootbox**: {await functions.bool_to_text(user_settings.alert_lootbox.enabled)}\n'
        f'{emojis.BP} **Partner alert**: {await functions.bool_to_text(user_settings.alert_partner.enabled)}\n'
        f'{emojis.DETAIL} _Lootbox and hardmode alerts are sent to this channel._\n'
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
    embed.add_field(name='COMMAND REMINDERS I', value=command_reminders, inline=False)
    embed.add_field(name='COMMAND REMINDERS II', value=command_reminders2, inline=False)
    embed.add_field(name='EVENT REMINDERS', value=event_reminders, inline=False)
    return embed


async def embed_settings_user(bot: discord.Bot, ctx: discord.ApplicationContext,
                              user_settings: users.User) -> discord.Embed:
    """User settings embed"""
    ping_mode_setting = 'After' if user_settings.ping_after_message else 'Before'
    try:
        tt_timestamp = int(user_settings.last_tt.timestamp())
    except OSError as error: # Windows throws an error if datetime is set to 0 apparently
        tt_timestamp = 0

    bot = (
        f'{emojis.BP} **Bot**: {await functions.bool_to_text(user_settings.bot_enabled)}\n'
        f'{emojis.DETAIL} _You can toggle this by using {strings.SLASH_COMMANDS_NAVI["on"]} '
        f'and {strings.SLASH_COMMANDS_NAVI["off"]}._\n'
        f'{emojis.BP} **Reactions**: {await functions.bool_to_text(user_settings.reactions_enabled)}\n'
    )
    donor_tier = (
        f'{emojis.BP} **You**: `{strings.DONOR_TIERS[user_settings.user_donor_tier]}`\n'
        f'{emojis.BP} **Your partner**: `{strings.DONOR_TIERS[user_settings.partner_donor_tier]}`\n'
        f'{emojis.DETAIL} _You can only change this if you have no partner set._\n'
        f'{emojis.DETAIL} _If you do, this is synchronized with your partner instead._'
    )
    behaviour = (
        f'{emojis.BP} **DND mode**: {await functions.bool_to_text(user_settings.dnd_mode_enabled)}\n'
        f'{emojis.DETAIL} _If DND mode is enabled, Navi won\'t ping you._\n'
        f'{emojis.BP} **Hardmode mode**: {await functions.bool_to_text(user_settings.hardmode_mode_enabled)}\n'
        f'{emojis.DETAIL} _Tells your partner to hunt solo if he uses `together`._\n'
        f'{emojis.BP} **Hunt rotation**: {await functions.bool_to_text(user_settings.hunt_rotation_enabled)}\n'
        f'{emojis.DETAIL} _Rotates hunt reminders between `hunt` and `hunt together`._\n'
        f'{emojis.BP} **Slash mentions**: {await functions.bool_to_text(user_settings.slash_mentions_enabled)}\n'
        f'{emojis.DETAIL} _If you can\'t see slash mentions properly, update your Discord app._\n'
        f'{emojis.BP} **Ping mode**: `{ping_mode_setting}` reminder message\n'
    )
    tracking = (
        f'{emojis.BP} **Command tracking**: {await functions.bool_to_text(user_settings.tracking_enabled)}\n'
        f'{emojis.BP} **Last time travel**: <t:{tt_timestamp}:f> UTC\n'
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
    embed.add_field(name='EPIC RPG DONOR TIERS', value=donor_tier, inline=False)
    embed.add_field(name='REMINDER BEHAVIOUR', value=behaviour, inline=False)
    embed.add_field(name='TRACKING', value=tracking, inline=False)
    return embed