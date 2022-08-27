# views.py
"""Contains global interaction views"""

from typing import Dict, Optional

import discord

from content import settings as settings_cmd
from database import clans, users
from resources import components, functions, settings, strings

COMMANDS_SETTINGS = {
    'Guild settings': settings_cmd.command_settings_clan,
    'Helper settings': settings_cmd.command_settings_helpers,
    'Reminder settings': settings_cmd.command_settings_reminders,
    'User settings': settings_cmd.command_settings_user,
}

class AutoReadyView(discord.ui.View):
    """View with button to toggle the auto_ready feature.

    Also needs the message of the response with the view, so do AbortView.message = await message.reply('foo').

    Returns
    -------
    'follow' if auto_ready was enabled
    'unfollow' if auto_ready was disabled
    'timeout' on timeout.
    None if nothing happened yet.
    """
    def __init__(self, user: discord.User, user_settings: users.User,
                 message: Optional[discord.Message] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.message = message
        self.user = user
        self.user_settings = user_settings
        if not user_settings.auto_ready_enabled:
            custom_id = 'follow'
            label = 'Follow me!'
        else:
            custom_id = 'unfollow'
            label = 'Stop following me!'
        self.add_item(components.AutoReadyButton(custom_id=custom_id, label=label))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(strings.MSG_INTERACTION_ERROR, ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
        self.stop()


class ConfirmCancelView(discord.ui.View):
    """View with confirm and cancel button.

    Args: ctx, labels: Optional[list[str]]

    Also needs the message with the view, so do view.message = await ctx.interaction.original_message().
    Without this message, buttons will not be disabled when the interaction times out.

    Returns 'confirm', 'cancel' or None (if timeout/error)
    """
    def __init__(self, ctx: discord.ApplicationCommand, labels: Optional[list[str]] = ['Yes','No'],
                 interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.value = None
        self.user = ctx.author
        self.interaction = interaction
        self.label_confirm = labels[0]
        self.label_cancel = labels[1]
        self.add_item(components.CustomButton(style=discord.ButtonStyle.blurple,
                                              custom_id='confirm',
                                              label=self.label_confirm))
        self.add_item(components.CustomButton(style=discord.ButtonStyle.blurple,
                                              custom_id='cancel',
                                              label=self.label_cancel))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return False
        return True

    async def on_timeout(self):
        self.value = None
        if self.interaction is not None:
            try:
                await functions.edit_interaction(self.interaction, view=None)
            except discord.errors.NotFound:
                pass
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
                else:
                    style = discord.ButtonStyle.grey
                self.add_item(components.DisabledButton(style=style, label=label, row=row, emoji=emoji))
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
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, clan_settings: clans.Clan,
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
            await interaction.response.send_message(strings.MSG_INTERACTION_ERROR, ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_message(view=None)
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
    - user_settings: Clan object with the settings of the clan

    Returns
    -------
    None

    """
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, user_settings: users.User,
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
            'Training helper': 'training_helper_enabled',
        }
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings, 'Toggle helpers'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(strings.MSG_INTERACTION_ERROR, ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_message(view=None)
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
    - user_settings: Clan object with the settings of the clan

    Returns
    -------
    None

    """
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, user_settings: users.User,
                 embed_function: callable, interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=settings.INTERACTION_TIMEOUT)
        self.ctx = ctx
        self.bot = bot
        self.value = None
        self.interaction = interaction
        self.user = ctx.author
        self.user_settings = user_settings
        self.embed_function = embed_function
        toggled_settings_commands = {
            'Adventure': 'alert_adventure',
            'Arena': 'alert_arena',
            'Daily': 'alert_daily',
            'Duel': 'alert_duel',
            'Dungeon / Miniboss': 'alert_dungeon_miniboss',
            'Farm': 'alert_farm',
            'Guild': 'alert_guild',
            'Horse': 'alert_horse_breed',
            'Hunt': 'alert_hunt',
            'Lootbox': 'alert_lootbox',
            'Partner alert': 'alert_partner',
            'Pets': 'alert_pets',
            'Quest': 'alert_quest',
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
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_commands, 'Toggle command reminders',
                                                          'toggle_command_reminders'))
        self.add_item(components.ToggleUserSettingsSelect(self, toggled_settings_events, 'Toggle event reminders',
                                                          'toggle_event_reminders'))
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(strings.MSG_INTERACTION_ERROR, ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_message(view=None)
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
    - user_settings: Clan object with the settings of the clan

    Returns
    -------
    None

    """
    def __init__(self, ctx: discord.ApplicationContext, bot: discord.Bot, user_settings: users.User,
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
        self.add_item(components.SwitchSettingsSelect(self, COMMANDS_SETTINGS))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(strings.MSG_INTERACTION_ERROR, ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.interaction.edit_original_message(view=None)
        self.stop()