# views.py
"""Contains global interaction views"""

from datetime import timedelta
import random
from typing import List, Optional, Union

import discord
from discord.ext import bridge, commands

from content import settings as settings_cmd
from database import clans, cooldowns, guilds, portals, reminders, users
from resources import components, functions, settings, strings

COMMANDS_SETTINGS = {
    'Alts': settings_cmd.command_settings_alts,
    'Guild channel': settings_cmd.command_settings_clan,
    'Helpers': settings_cmd.command_settings_helpers,
    'Multipliers': settings_cmd.command_settings_multipliers,
    'Partner': settings_cmd.command_settings_partner,
    'Portals': settings_cmd.command_settings_portals,
    'Ready list': settings_cmd.command_settings_ready,
    'Reminders (1/2)': settings_cmd.command_settings_reminders,
    'Reminders (2/2)': settings_cmd.command_settings_reminders_2,
    'Reminder messages': settings_cmd.command_settings_messages,
    'User': settings_cmd.command_settings_user,
}

COMMANDS_SERVER_SETTINGS = {
    'Main': settings_cmd.command_server_settings_main,
    'Auto flex (1/2)': settings_cmd.command_server_settings_auto_flex,
    'Auto flex (2/2)': settings_cmd.command_server_settings_auto_flex_2,
    'Event pings': settings_cmd.command_server_settings_event_pings,
}


class ReadyView(discord.ui.View):
    """View with button to toggle the auto_ready feature.

    Also needs the message of the response with the view, so do AbortView.message = await message.reply('foo').

    Returns
    -------
    'follow' if auto_ready was enabled
    'unfollow' if auto_ready was disabled
    'timeout' on timeout.
    None if nothing happened yet.
    """
    def __init__(self, bot: bridge.AutoShardedBot, ctx: Union[commands.Context, discord.ApplicationContext], user: discord.User,
                 user_settings: users.User, user_mentioned: bool, embed_function: callable,
                 interaction_message: Optional[Union[discord.Message, discord.Interaction]] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.bot = bot
        self.ctx = ctx
        self.interaction_message = interaction_message
        self.user = user
        self.user_settings = user_settings
        self.user_mentioned = user_mentioned
        self.embed_function = embed_function
        self.active_alt_id = user.id
        if not user_mentioned and user_settings.alts:
            self.add_item(components.SwitchReadyAltSelect(self))
        if not user_settings.auto_ready_enabled:
            custom_id = 'follow'
            label = 'Follow me!'
        else:
            custom_id = 'unfollow'
            label = 'Stop following me!'
        self.add_item(components.ToggleAutoReadyButton(custom_id=custom_id, label=label))
        if isinstance(ctx, discord.ApplicationContext):
            self.add_item(components.CustomButton(discord.ButtonStyle.grey, 'show_settings', '➜ Settings'))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.disable_all_items()
        if isinstance(self.ctx, discord.ApplicationContext):
            await functions.edit_interaction(self.interaction_message, view=self)
        else:
            await self.interaction_message.edit(view=self)
        self.stop()


class ConfirmCancelView(discord.ui.View):
    """View with confirm and cancel button.

    Args: ctx, styles: Optional[List[discord.ButtonStyle]], labels: Optional[list[str]]

    Also needs the message with the view, so do view.message = await ctx.interaction.original_message().
    Without this message, buttons will not be disabled when the interaction times out.

    Returns 'confirm', 'cancel' or None (if timeout/error)
    """
    def __init__(self, ctx: bridge.BridgeContext,
                 styles: Optional[List[discord.ButtonStyle]] = [discord.ButtonStyle.grey, discord.ButtonStyle.grey],
                 labels: Optional[List[str]] = ['Yes','No'],
                 interaction_message: Optional[Union[discord.Message, discord.Interaction]] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.value = None
        self.user = ctx.author
        self.interaction_message = interaction_message
        self.add_item(components.CustomButton(style=styles[0], custom_id='confirm', label=labels[0]))
        self.add_item(components.CustomButton(style=styles[1], custom_id='cancel', label=labels[1]))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return False
        return True

    async def on_timeout(self):
        self.stop()

        
class ConfirmUserView(discord.ui.View):
    """View with yes and no buttons that asks a user to allow him to be added.

    Args: ctx, labels: Optional[list[str]]

    Also needs the message with the view, so do view.message = await ctx.interaction.original_message().
    Without this message, buttons will not be disabled when the interaction times out.

    Returns 'confirm', 'cancel' or None (if timeout/error)
    """
    def __init__(self, asked_user: discord.User, confirm_label: Optional[str] = 'Yes',
                 cancel_label: Optional[str] = 'No',
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.asked_user = asked_user
        self.interaction = interaction
        self.add_item(components.CustomButton(style=discord.ButtonStyle.green,
                                              custom_id='confirm',
                                              label=confirm_label))
        self.add_item(components.CustomButton(style=discord.ButtonStyle.grey,
                                              custom_id='cancel',
                                              label=cancel_label))
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.asked_user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        self.disable_all_items()
        await self.interaction.edit(view=self)
        self.stop()


class TrainingAnswerView(discord.ui.View):
    """View with training answers."""
    def __init__(self, buttons: dict):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        for row, row_buttons in buttons.items():
            for custom_id, button_data in row_buttons.items():
                label, emoji, correct_answer = button_data
                if correct_answer:
                    if custom_id == 'training_no':
                        style = discord.ButtonStyle.red
                    else:
                        style = discord.ButtonStyle.green
                    disabled = False
                else:
                    style = discord.ButtonStyle.grey
                    disabled = True
                self.add_item(components.TrainingButton(style=style, label=label, row=row, emoji=emoji, disabled=disabled))
        self.stop()


class SettingsAltsView(discord.ui.View):
    """View with a all components to manage alt settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        if len(user_settings.alts) < 24:
            self.add_item(components.AddAltSelect(self, row=0))
        if user_settings.alts:
            self.add_item(components.RemoveAltSelect(self, row=1))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS, row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()
        

class SettingsClanView(discord.ui.View):
    """View with a all components to manage clan settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    clan_settings: Clan object with the settings of the clan.
    embed_function: Functino that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - clan_settings: Clan object with the settings of the clan

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, clan_settings: clans.Clan,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.clan_settings = clan_settings
        self.add_item(components.ManageClanSettingsSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsHelpersView(discord.ui.View):
    """View with a all components to manage helper settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        toggled_settings = {
            'Context helper': 'context_helper_enabled',
            'Heal warning': 'heal_warning_enabled',
            'Pet catch helper': 'pet_helper_enabled',
            'Ruby counter': 'ruby_counter_enabled',
            'Time potion warning': 'time_potion_warning_enabled',
            'Training helper': 'training_helper_enabled',
            'Megarace helper': 'megarace_helper_enabled',
            'Pumpkin bat helper': 'halloween_helper_enabled',
        }
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings, 'Toggle helpers'))
        self.add_item(components.SetFarmHelperModeSelect(self))
        self.add_item(components.ManageHelperSettingsSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsPortalsView(discord.ui.View):
    """View with a all components to manage portal settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: user object with the settings of the user.
    user_portals: Dict[channel_id: discord.TextChannel object]
    embed_function: Functino that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - ctx: Context
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 user_portals: List[portals.Portal], embed_function: callable,
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.user_portals = user_portals
        self.add_item(components.ManagePortalsSelect(self))
        self.add_item(components.ManagePortalSettingsSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsReadyView(discord.ui.View):
    """View with a all components to manage ready settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    clan_settings: Clan object with the settings of the clan.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 clan_settings: clans.Clan, embed_function: callable,
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.clan_settings = clan_settings
        self.embed_function = embed_function
        toggled_settings_other = {
            '/cd': 'cmd_cd_visible',
            '/inventory': 'cmd_inventory_visible',
            '/ready': 'cmd_ready_visible',
            '/slashboard': 'cmd_slashboard_visible',
        }
        self.add_item(components.ManageReadySettingsSelect(self))
        self.add_item(components.ToggleReadySettingsSelect(self, toggled_settings_other, 'Toggle other commands',
                                                           'toggle_other_commands'))
        self.add_item(components.SwitchToReadyRemindersSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsReadyRemindersView(discord.ui.View):
    """View with a all components to manage ready setting reminders.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    clan_settings: Clan object with the settings of the clan.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 clan_settings: clans.Clan, embed_function: callable,
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.clan_settings = clan_settings
        self.embed_function = embed_function
        toggled_settings_commands = {
            'Adventure': 'alert_adventure',
            'Arena': 'alert_arena',
            'Card hand': 'alert_card_hand',
            'Daily': 'alert_daily',
            'Duel': 'alert_duel',
            'Dungeon / Miniboss': 'alert_dungeon_miniboss',
            'EPIC items': 'alert_epic',
            'Farm': 'alert_farm',
            'Guild': 'alert_guild',
            'Horse': 'alert_horse_breed',
            'Hunt': 'alert_hunt',
            'Hunt partner': 'alert_hunt_partner',
            'Lootbox': 'alert_lootbox',
            'Quest': 'alert_quest',
            'Pets claim': 'alert_pets',
            'Training': 'alert_training',
            'Vote': 'alert_vote',
            'Weekly': 'alert_weekly',
            'Work': 'alert_work',

        }
        toggled_settings_events = {
            'Big arena': 'alert_big_arena',
            'Horse race': 'alert_horse_race',
            'Lottery': 'alert_lottery',
            'Minin\'tboss': 'alert_not_so_mini_boss',
            'Pet tournament': 'alert_pet_tournament',
        }
        toggled_settings_seasonal = {
            'Advent calendar': 'alert_advent',
            'Boo': 'alert_boo',
            'Cel dailyquest': 'alert_cel_dailyquest',
            'Cel multiply': 'alert_cel_multiply',
            'Cel sacrifice': 'alert_cel_sacrifice',
            'Chimney': 'alert_chimney',
            'ETERNAL presents': 'alert_eternal_present',
            'Love share': 'alert_love_share',
            'Megarace': 'alert_megarace',
            'Minirace': 'alert_minirace',
        }
        self.add_item(components.ToggleReadySettingsSelect(self, toggled_settings_commands, 'Toggle command reminders',
                                                           'toggle_command_reminders'))
        self.add_item(components.ToggleReadySettingsSelect(self, toggled_settings_events, 'Toggle event reminders',
                                                           'toggle_event_reminders'))
        if toggled_settings_commands:
            self.add_item(components.ToggleReadySettingsSelect(self, toggled_settings_seasonal, 'Toggle seasonal reminders',
                                                               'toggle_seasonal_reminders'))
        self.add_item(components.ManageReadyReminderChannelsSelect(self))

    @discord.ui.button(label="< Back", style=discord.ButtonStyle.grey, row=4)
    async def confirm_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        view = SettingsReadyView(self.ctx, self.bot, self.user_settings, self.clan_settings,
                                 settings_cmd.embed_settings_ready)
        embed = await settings_cmd.embed_settings_ready(self.bot, self.ctx, self.user_settings, self.clan_settings)
        await interaction.response.edit_message(embed=embed, view=view)
        view.interaction = interaction
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsMultipliersView(discord.ui.View):
    """View with a all components to manage reminder multiplier settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        self.add_item(components.ManageMultiplierSettingsSelect(self))
        select_disabled: bool = False
        if user_settings.multiplier_management_enabled and user_settings.current_area != 20:
            select_disabled = True
        self.add_item(components.ManageManagedMultipliersSelect(self, disabled=select_disabled))
        self.add_item(components.ManageManualMultipliersSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsRemindersView(discord.ui.View):
    """View with a all components to manage reminder settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        toggled_settings_commands_1 = {
            'Adventure': 'alert_adventure',
            'Arena': 'alert_arena',
            'Boost items': 'alert_boosts',
            'Card hand': 'alert_card_hand',
            'Daily': 'alert_daily',
            'Duel': 'alert_duel',
            'Dungeon / Miniboss': 'alert_dungeon_miniboss',
            'EPIC items': 'alert_epic',
            'EPIC shop restocks': 'alert_epic_shop',
            'Eternity sealing': 'alert_eternity_sealing',
            'Farm': 'alert_farm',
            'Guild': 'alert_guild',
            'Horse': 'alert_horse_breed',
        }
        toggled_settings_commands_2 = {
            'Hunt': 'alert_hunt',
            'Hunt partner': 'alert_hunt_partner',
            'Lootbox': 'alert_lootbox',
            'Maintenance': 'alert_maintenance',
            'Partner alert': 'alert_partner',
            'Pets': 'alert_pets',
            'Quest': 'alert_quest',
            'Training': 'alert_training',
            'Vote': 'alert_vote',
            'Weekly': 'alert_weekly',
            'Work': 'alert_work',
        }

        self.add_item(components.ManageReminderBehaviourSelect(self))
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_commands_1, 'Toggle reminders (I)',
                                                          'toggle_command_reminders_1'))
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_commands_2, 'Toggle reminders (II)',
                                                          'toggle_command_reminders_2'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()

        
class SettingsReminders2View(discord.ui.View):
    """View with a all components to manage reminder settings (page 2).
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        toggled_settings_events = {
            'Big arena': 'alert_big_arena',
            'Horse race': 'alert_horse_race',
            'Lottery': 'alert_lottery',
            'Minin\'tboss': 'alert_not_so_mini_boss',
            'Pet tournament': 'alert_pet_tournament',
        }
        toggled_settings_seasonal = {
            'Advent calendar': 'alert_advent',
            'Boo': 'alert_boo',
            'Cel dailyquest': 'alert_cel_dailyquest',
            'Cel multiply': 'alert_cel_multiply',
            'Cel sacrifice': 'alert_cel_sacrifice',
            'Chimney': 'alert_chimney',
            'ETERNAL presents': 'alert_eternal_present',
            'Love share': 'alert_love_share',
            'Megarace': 'alert_megarace',
            'Minirace': 'alert_minirace',
        }
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_events, 'Toggle event reminders',
                                                          'toggle_event_reminders'))
        if toggled_settings_seasonal:
            self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_seasonal, 'Toggle seasonal reminders',
                                                              'toggle_seasonal_reminders'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsUserView(discord.ui.View):
    """View with a all components to manage user settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        self.add_item(components.ManageUserSettingsSelect(self))
        self.add_item(components.SetDonorTierSelect(self, 'Change your donor tier', 'user'))
        partner_select_disabled = True if user_settings.partner_id is not None else False
        self.add_item(components.SetDonorTierSelect(self, 'Change partner donor tier', 'partner', partner_select_disabled))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsMessagesView(discord.ui.View):
    """View with a all components to change message reminders.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns a list of embeds to see specific messages. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user
    - activity: str, If this is None, the view doesn't show the buttons to change a message

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 embed_function: callable, activity: Optional[str] = 'all',
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        self.activity = activity
        if activity == 'all':
            self.add_item(components.SetReminderMessageButton(style=discord.ButtonStyle.red, custom_id='reset_all',
                                                              label='Reset all messages'))
        else:
            self.add_item(components.SetReminderMessageButton(style=discord.ButtonStyle.blurple, custom_id='set_message',
                                                              label='Change'))
            self.add_item(components.SetReminderMessageButton(style=discord.ButtonStyle.red, custom_id='reset_message',
                                                              label='Reset'))
        placeholder = 'Choose activity (1)' if len (strings.ACTIVITIES) > 24 else 'Choose activity'
        self.add_item(components.ReminderMessageSelect(self, strings.ACTIVITIES[:24], placeholder,
                                                       'select_message_activity_1', row=2))
        if len(strings.ACTIVITIES) > 24:
            self.add_item(components.ReminderMessageSelect(self, strings.ACTIVITIES[24:], 'Choose activity (2)',
                                                           'select_message_activity_2', row=3))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS, row=4))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class SettingsPartnerView(discord.ui.View):
    """View with a all components to manage partner settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user
    - partner_settings: User object with the settings of the partner

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, user_settings: users.User,
                 partner_settings: users.User, embed_function: callable,
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.partner_settings = partner_settings
        self.embed_function = embed_function
        self.add_item(components.AddPartnerSelect(self, "Change partner", row=0))
        self.add_item(components.ManagePartnerSettingsSelect(self, row=1))
        self.add_item(components.SetPartnerAlertThreshold(self, row=2))
        partner_select_disabled = True if user_settings.partner_id is not None else False
        self.add_item(components.SetDonorTierSelect(self, 'Change partner donor tier', 'partner', partner_select_disabled, row=3))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS, row=4))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class OneButtonView(discord.ui.View):
    """View with one button that returns the custom id of that button.

    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Returns
    -------
    None while active
    custom id of the button when pressed
    'timeout' on timeout.
    """
    def __init__(self, ctx: bridge.BridgeContext, style: discord.ButtonStyle,
                 custom_id: str, label: str, emoji: Optional[discord.PartialEmoji] = None,
                 interaction_message: Optional[Union[discord.Message, discord.Interaction]] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.interaction_message = interaction_message
        self.ctx = ctx
        self.user = ctx.author
        self.add_item(components.CustomButton(style=style, custom_id=custom_id, label=label, emoji=emoji))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.disable_all_items()
        await self.interaction_message.edit(view=self)
        self.stop()


class RemindersListView(discord.ui.View):
    """View with a select that deletes custom reminders.

    Also needs the message of the response with the view, so do view.interaction = await ctx.respond('foo').

    Returns
    -------
    None
    """
    def __init__(self, bot: bridge.AutoShardedBot, ctx: Union[commands.Context, discord.ApplicationContext], user: discord.User,
                 user_settings: users.User, user_mentioned: bool, custom_reminders: List[reminders.Reminder],
                 embed_function: callable, show_timestamps: Optional[bool] = False,
                 interaction_message: Optional[Union[discord.Message, discord.Interaction]] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.bot = bot
        self.ctx = ctx
        self.custom_reminders = custom_reminders
        self.embed_function = embed_function
        self.interaction_message = interaction_message
        self.user = user
        self.user_settings = user_settings
        self.user_mentioned = user_mentioned
        self.show_timestamps = show_timestamps
        self.active_alt_id = user.id
        if not user_mentioned and user_settings.alts:
            self.add_item(components.SwitchRemindersListAltSelect(self))
        self.add_item(components.ToggleTimestampsButton('Show end time'))
        if custom_reminders:
            self.add_item(components.DeleteCustomRemindersButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.disable_all_items()
        if isinstance(self.ctx, discord.ApplicationContext):
            await functions.edit_interaction(self.interaction_message, view=self)
        else:
            await self.interaction_message.edit(view=self)
        self.stop()


class StatsView(discord.ui.View):
    """View with a button to toggle command tracking.

    Also needs the message of the response with the view, so do AbortView.message = await message.reply('foo').

    Returns
    -------
    'track' if tracking was enabled
    'untrack' if tracking was disabled
    'timeout' on timeout.
    None if nothing happened yet.
    """
    def __init__(self, bot: bridge.AutoShardedBot, ctx: Union[commands.Context, discord.ApplicationContext],
                 user_settings: users.User, user_mentioned: bool, time_left: timedelta, embed_function: callable,
                 interaction_message: Optional[Union[discord.Message, discord.Interaction]] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.bot = bot
        self.ctx = ctx
        self.interaction_message = interaction_message
        self.user = ctx.author
        self.user_settings = user_settings
        self.user_mentioned = user_mentioned
        self.time_left = time_left
        self.embed_function = embed_function
        self.active_alt_id = ctx.author.id
        if not user_settings.tracking_enabled:
            style = discord.ButtonStyle.green
            custom_id = 'track'
            label = 'Track me!'
        else:
            style = discord.ButtonStyle.grey
            custom_id = 'untrack'
            label = 'Stop tracking me!'
        if not user_mentioned and user_settings.alts:
            self.add_item(components.SwitchStatsAltSelect(self))
        self.add_item(components.ToggleTrackingButton(style=style, custom_id=custom_id, label=label))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.disable_all_items()
        if isinstance(self.ctx, discord.ApplicationContext):
            await functions.edit_interaction(self.interaction_message, view=self)
        else:
            await self.interaction_message.edit(view=self)
        self.stop()


class SettingsServerAutoFlexView(discord.ui.View):
    """View with a all components to manage auto-flex server settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    guild_settings: Guild object with the settings of the guild/server.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - ctx: context
    - guild_settings: ClanGuild object with the settings of the guild/server

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, guild_settings: guilds.Guild,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.guild_settings = guild_settings
        toggled_auto_flex_alerts_1 = {
            'Brew electronical potion': 'auto_flex_brew_electronical_enabled',
            'Artifact crafting': 'auto_flex_artifacts_enabled',
            'Cards from drop': 'auto_flex_card_drop_enabled',
            'Card goldening': 'auto_flex_card_golden_enabled',
            'Cards from card slots': 'auto_flex_card_slots_enabled',
            'EPIC berries from hunt or adventure': 'auto_flex_epic_berry_enabled',
            'EPIC berries from work commands': 'auto_flex_work_epicberry_enabled',
            'ETERNAL lootbox from hunt / adventure': 'auto_flex_lb_eternal_enabled',
            'GODLY lootbox from hunt / adventure': 'auto_flex_lb_godly_enabled',
            'HYPER logs from work commands': 'auto_flex_work_hyperlog_enabled',
            'OMEGA lootbox from hunt / adventure': 'auto_flex_lb_omega_enabled',
        }
        toggled_auto_flex_alerts_2 = {
            'Lost lootboxes in area 18': 'auto_flex_lb_a18_enabled',
            'Party popper from any lootbox': 'auto_flex_lb_party_popper_enabled',
            'SUPER fish from work commands': 'auto_flex_work_superfish_enabled',
            'TIME capsule from GODLY/VOID lootbox': 'auto_flex_lb_godly_tt_enabled',
            'ULTIMATE logs from work commands': 'auto_flex_work_ultimatelog_enabled',
            'ULTRA log from EDGY lootbox': 'auto_flex_lb_edgy_ultra_enabled',
            'ULTRA log from OMEGA lootbox': 'auto_flex_lb_omega_ultra_enabled',
            'ULTRA logs from work commands': 'auto_flex_work_ultralog_enabled',
            'VOID lootbox from hunt / adventure': 'auto_flex_lb_void_enabled',
            'Watermelons from work commands': 'auto_flex_work_watermelon_enabled',
            'Get ULTRA-EDGY in enchant event': 'auto_flex_event_enchant_enabled',
            'Get 20 levels in farm event': 'auto_flex_event_farm_enabled',
        }

        self.add_item(components.ManageServerSettingsAutoFlexSelect(self))
        self.add_item(components.ToggleServerSettingsSelect(self, toggled_auto_flex_alerts_1,
                                                            'Toggle auto flex alerts (I)',
                                                            'toggle_auto_flex_alerts_1'))
        self.add_item(components.ToggleServerSettingsSelect(self, toggled_auto_flex_alerts_2,
                                                            'Toggle auto flex alerts (II)',
                                                            'toggle_auto_flex_alerts_2'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SERVER_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()

        
class SettingsServerAutoFlex2View(discord.ui.View):
    """View with a all components to manage auto-flex 2/2 server settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    guild_settings: Guild object with the settings of the guild/server.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - ctx: context
    - guild_settings: ClanGuild object with the settings of the guild/server

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, guild_settings: guilds.Guild,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.guild_settings = guild_settings
        toggled_auto_flex_alerts_3 = {
            'Kill mysterious man in heal event': 'auto_flex_event_heal_enabled',
            'Evolve OMEGA lootbox in lootbox event': 'auto_flex_event_lb_enabled',
            'Successfully fly in void training event': 'auto_flex_event_training_enabled',
            'Forge GODLY cookie': 'auto_flex_forge_cookie_enabled',
            'Lose coin in coinflip': 'auto_flex_event_coinflip_enabled',
            'Catch pet with EPIC skill in training': 'auto_flex_pets_catch_epic_enabled',
            'Catch pet with timetraveler skill in training': 'auto_flex_pets_catch_tt_enabled',
            'Get rare drops from pets': 'auto_flex_pets_claim_omega_enabled',
            'Ascension': 'auto_flex_pr_ascension_enabled',
            'Time travel milestones': 'auto_flex_time_travel_enabled',
        }
        toggled_auto_flex_alerts_seasonal = {
            'Get stuck in xmas chimney': 'auto_flex_xmas_chimney_enabled',
            'Drop EPIC snowballs': 'auto_flex_xmas_snowball_enabled',
            'Drop ETERNAL presents': 'auto_flex_xmas_eternal_enabled',
            'Drop GODLY presents': 'auto_flex_xmas_godly_enabled',
            'Drop VOID presents': 'auto_flex_xmas_void_enabled',
            'Drop sleepy potion or suspicious broom in hal boo': 'auto_flex_hal_boo_enabled',
        }

        self.add_item(components.ToggleServerSettingsSelect(self, toggled_auto_flex_alerts_3,
                                                            'Toggle auto flex alerts (III)',
                                                            'toggle_auto_flex_alerts_3'))
        self.add_item(components.ToggleServerSettingsSelect(self, toggled_auto_flex_alerts_seasonal,
                                                            'Toggle auto flex alerts (seasonal)',
                                                            'toggle_auto_flex_alerts_seasonal'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SERVER_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()

        
class SettingsServerEventPingsView(discord.ui.View):
    """View with a all components to manage event ping server settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    guild_settings: Guild object with the settings of the guild/server.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - ctx: context
    - guild_settings: ClanGuild object with the settings of the guild/server

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, guild_settings: guilds.Guild,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.guild_settings = guild_settings
        toggled_events = {
            'Arena': 'event_arena',
            'Coin rain': 'event_coin',
            'Epic tree': 'event_log',
            'Legendary boss': 'event_legendary_boss',
            'Lootbox summoning': 'event_lootbox',
            'Megalodon': 'event_fish',
            'Miniboss': 'event_miniboss',
            'Rare hunt monster': 'event_rare_hunt_monster',
        }

        self.add_item(components.ToggleEventPingsSelect(self, toggled_events,
                                                             'Toggle event pings',
                                                             'toggle_event_pings'))
        self.add_item(components.ManageEventPingMessagesSelect(self,))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SERVER_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()

        
class SettingsServerMainView(discord.ui.View):
    """View with a all components to manage server auto-flex settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    guild_settings: Guild object with the settings of the guild/server.
    embed_function: Function that returns the settings embed. The view expects the following arguments:
    - bot: Bot
    - ctx: context
    - guild_settings: ClanGuild object with the settings of the guild/server

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, guild_settings: guilds.Guild,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.embed_function = embed_function
        self.interaction = interaction
        self.user = ctx.author
        self.guild_settings = guild_settings

        self.add_item(components.ManageServerSettingsMainSelect(self))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SERVER_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class DevEventReductionsView(discord.ui.View):
    """View with a all components to manage cooldown settings.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    bot: Bot.
    user_settings: User object with the settings of the user.
    embed_function: Function that returns the settings embed. The function expects the following arguments:
    - bot: Bot
    - user_settings: User object with the settings of the user

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, all_cooldowns: List[cooldowns.Cooldown],
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.bot = bot
        self.ctx = ctx
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.all_cooldowns = all_cooldowns
        self.embed_function = embed_function
        self.add_item(components.ManageEventReductionsSelect(self, all_cooldowns, 'slash'))
        self.add_item(components.ManageEventReductionsSelect(self, all_cooldowns, 'text'))
        self.add_item(components.CopyEventReductionsButton(discord.ButtonStyle.grey, 'copy_slash_text',
                                                           'Copy slash > text'))
        self.add_item(components.CopyEventReductionsButton(discord.ButtonStyle.grey, 'copy_text_slash',
                                                           'Copy text > slash'))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()


class DevSeasonalEventView(discord.ui.View):
    """View with a all components to manage the seasonal event.
    Also needs the interaction of the response with the view, so do view.interaction = await ctx.respond('foo').

    Arguments
    ---------
    ctx: Context.
    bot: Bot.
    embed_function: Function that returns the settings embed. The function expects no arguments.

    Returns
    -------
    None

    """
    def __init__(self, ctx: bridge.BridgeContext, bot: bridge.AutoShardedBot, active_event: str,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        seasonal_events = ['none',] + strings.SEASONAL_EVENTS
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.active_event = active_event
        self.user = ctx.author
        self.embed_function = embed_function
        self.add_item(components.SetSeasonalEventSelect(seasonal_events, active_event,
                                                 'Set seasonal event ...'))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(random.choice(strings.MSG_INTERACTION_ERRORS), ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit(view=None)
        self.stop()