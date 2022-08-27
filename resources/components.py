# components.py
"""Contains global interaction components"""

from select import select
from typing import Dict, Optional

import discord

from database import users
from resources import emojis, functions, modals, strings, views


class AutoReadyButton(discord.ui.Button):
    """Recalculation button for the crafting calculator"""
    def __init__(self, custom_id: str, label: str, disabled: bool = False, emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=discord.ButtonStyle.grey, custom_id=custom_id, label=label, emoji=emoji,
                         disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.custom_id == 'follow':
            enabled = True
            response = 'Done. I will now show you your ready commands after every command.'
        else:
            enabled = False
            response = 'Done. I will now stop showing your ready commands after every command.'
        await self.view.user_settings.update(auto_ready_enabled=enabled)
        self.view.value = self.custom_id
        await self.view.user_settings.refresh()
        if self.view.user_settings.auto_ready_enabled:
            self.label = 'Stop following me!'
            self.custom_id = 'unfollow'
        else:
            self.label = 'Follow me!'
            self.custom_id = 'follow'
        await self.view.message.edit(view=self.view)
        if not interaction.response.is_done():
            await interaction.response.send_message(response, ephemeral=True)
        else:
            await interaction.followup.send(response, ephemeral=True)


class CustomButton(discord.ui.Button):
    """Custom Button. Writes its custom id to the view value and stops the view."""
    def __init__(self, style: discord.ButtonStyle, custom_id: str, label: Optional[str],
                 emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.custom_id
        self.view.stop()


class DisabledButton(discord.ui.Button):
    """Disabled button with no callback"""
    def __init__(self, style: discord.ButtonStyle, label: str, row: int, emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, label=label, emoji=emoji, disabled=True, row=row)


class ToggleUserSettingsSelect(discord.ui.Select):
    """Toggle select that shows and toggles the status of user settings (except alerts)."""
    def __init__(self, view: discord.ui.View, toggled_settings: Dict[str, str], placeholder: str,
                 custom_id: Optional[str] = 'toggle_user_settings', row: Optional[int] = None):
        self.toggled_settings = toggled_settings
        options = []
        options.append(discord.SelectOption(label='Enable all', value='enable_all', emoji=None))
        options.append(discord.SelectOption(label='Disable all', value='disable_all', emoji=None))
        for label, setting in toggled_settings.items():
            setting_enabled = getattr(view.user_settings, setting)
            if isinstance(setting_enabled, users.UserAlert):
                setting_enabled = getattr(setting_enabled, 'enabled')
            emoji = emojis.GREENTICK if setting_enabled else emojis.REDTICK
            options.append(discord.SelectOption(label=label, value=setting, emoji=emoji))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row,
                         custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        kwargs = {}
        if select_value in ('enable_all','disable_all'):
            enabled = True if select_value == 'enable_all' else False
            for setting in self.toggled_settings.values():
                if not setting.endswith('_enabled'):
                    setting = f'{setting}_enabled'
                kwargs[setting] = enabled
        else:
            setting_value = getattr(self.view.user_settings, select_value)
            if isinstance(setting_value, users.UserAlert):
                setting_value = getattr(setting_value, 'enabled')
            if not select_value.endswith('_enabled'):
                select_value = f'{select_value}_enabled'
            kwargs[select_value] = not setting_value
        await self.view.user_settings.update(**kwargs)
        for child in self.view.children.copy():
            if child.custom_id == self.custom_id:
                self.view.remove_item(child)
                self.view.add_item(ToggleUserSettingsSelect(self.view, self.toggled_settings,
                                                            self.placeholder, self.custom_id))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class ManageClanSettingsSelect(discord.ui.Select):
    """Select to change guild settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        reminder_emoji = emojis.GREENTICK if view.clan_settings.alert_enabled else emojis.REDTICK
        quest_emoji = emojis.GREENTICK if view.clan_settings.upgrade_quests_enabled else emojis.REDTICK
        options.append(discord.SelectOption(label=f'Toggle reminder',
                                            value='toggle_reminder', emoji=reminder_emoji))
        options.append(discord.SelectOption(label=f'Toggle quests below stealth threshold',
                                            value='toggle_quest', emoji=quest_emoji))
        options.append(discord.SelectOption(label='Change stealth threshold',
                                            value='set_threshold', emoji=None))
        options.append(discord.SelectOption(label='Set current channel as guild channel',
                                            value='set_channel', emoji=None))
        options.append(discord.SelectOption(label='Reset guild channel',
                                            value='reset_channel', emoji=None))
        super().__init__(placeholder='Change guild settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_clan_settings')

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.clan_settings.leader_id:
            await interaction.response.send_message(
                f'**{interaction.user.name}**, you are not registered as the guild owner. Only the guild owner can '
                f'change these settings.\n'
                f'If you _are_ the guild owner, run {strings.SLASH_COMMANDS_NEW["guild list"]} to update '
                f'your guild in my database.\n',
                ephemeral=True
            )
            return
        select_value = self.values[0]
        if select_value == 'toggle_reminder':
            if not self.view.clan_settings.alert_enabled and self.view.clan_settings.channel_id is None:
                await interaction.response.send_message('You need to set a guild channel first.', ephemeral=True)
                return
            await self.view.clan_settings.update(alert_enabled=not self.view.clan_settings.alert_enabled)
        elif select_value == 'toggle_quest':
            await self.view.clan_settings.update(upgrade_quests_enabled=not self.view.clan_settings.upgrade_quests_enabled)
        elif select_value == 'set_threshold':
            modal = modals.SetStealthThresholdModal(self.view)
            await interaction.response.send_modal(modal)
            return
        elif select_value == 'set_channel':
            confirm_view = views.ConfirmCancelView(self.view.ctx)
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to set `{interaction.channel.name}` as the alert channel '
                f'for the guild `{self.view.clan_settings.clan_name}`?',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.clan_settings.update(channel_id=interaction.channel.id)
                await confirm_interaction.edit_original_message(content='Channel updated.', view=None)
            else:
                await confirm_interaction.edit_original_message(content='Aborted', view=None)
                return
        elif select_value == 'reset_channel':
            confirm_view = views.ConfirmCancelView(self.view.ctx)
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset the guild alert channel '
                f'for the guild `{self.view.clan_settings.clan_name}`?\n\n'
                f'Note that this will also disable the reminder if enabled.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.clan_settings.update(channel_id=None)
                await self.view.clan_settings.update(alert_enabled=False)
                await confirm_interaction.edit_original_message(content='Channel reset.', view=None)
            else:
                await confirm_interaction.edit_original_message(content='Aborted', view=None)
                return
        for child in self.view.children.copy():
            if isinstance(child, ManageClanSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageClanSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.clan_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class SwitchSettingsSelect(discord.ui.Select):
    """Select to switch between settings embeds"""
    def __init__(self, view: discord.ui.View, commands_settings: Dict[str, callable], row: Optional[int] = None):
        self.commands_settings = commands_settings
        options = []
        for label in commands_settings.keys():
            options.append(discord.SelectOption(label=label, value=label, emoji=None))
        super().__init__(placeholder='➜ Switch to other settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='switch_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        await interaction.response.edit_message()
        self.view.stop()
        await self.commands_settings[select_value](self.view.bot, self.view.ctx, switch_view = self.view)


class ManageUserSettingsSelect(discord.ui.Select):
    """Select to change user settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        reactions_emoji = emojis.GREENTICK if view.user_settings.reactions_enabled else emojis.REDTICK
        dnd_emoji = emojis.GREENTICK if view.user_settings.dnd_mode_enabled else emojis.REDTICK
        hardmode_emoji = emojis.GREENTICK if view.user_settings.hardmode_mode_enabled else emojis.REDTICK
        hunt_emoji = emojis.GREENTICK if view.user_settings.hunt_rotation_enabled else emojis.REDTICK
        mentions_emoji = emojis.GREENTICK if view.user_settings.slash_mentions_enabled else emojis.REDTICK
        tracking_emoji = emojis.GREENTICK if view.user_settings.tracking_enabled else emojis.REDTICK
        ping_mode = 'before' if view.user_settings.ping_after_message else 'after'
        options.append(discord.SelectOption(label=f'Toggle reactions',
                                            value='toggle_reactions', emoji=reactions_emoji))
        options.append(discord.SelectOption(label=f'Toggle DND mode',
                                            value='toggle_dnd', emoji=dnd_emoji))
        options.append(discord.SelectOption(label=f'Toggle hardmode mode',
                                            value='toggle_hardmode', emoji=hardmode_emoji))
        options.append(discord.SelectOption(label=f'Toggle hunt rotation',
                                            value='toggle_hunt', emoji=hunt_emoji))
        options.append(discord.SelectOption(label=f'Toggle slash mentions',
                                            value='toggle_mentions', emoji=mentions_emoji))
        options.append(discord.SelectOption(label=f'Toggle command tracking',
                                            value='toggle_tracking', emoji=tracking_emoji))
        options.append(discord.SelectOption(label=f'Ping me {ping_mode} reminder',
                                            value='toggle_ping', emoji=None))
        options.append(discord.SelectOption(label=f'Change last time travel time',
                                            value='set_last_tt', emoji=None))
        super().__init__(placeholder='Change user settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_user_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_reactions':
            await self.view.user_settings.update(reactions_enabled=not self.view.user_settings.reactions_enabled)
        elif select_value == 'toggle_dnd':
            await self.view.user_settings.update(dnd_mode_enabled=not self.view.user_settings.dnd_mode_enabled)
        elif select_value == 'toggle_hardmode':
            await self.view.user_settings.update(hardmode_mode_enabled=not self.view.user_settings.hardmode_mode_enabled)
        elif select_value == 'toggle_hunt':
            await self.view.user_settings.update(hunt_rotation_enabled=not self.view.user_settings.hunt_rotation_enabled)
        elif select_value == 'toggle_mentions':
            await self.view.user_settings.update(slash_mentions_enabled=not self.view.user_settings.slash_mentions_enabled)
        elif select_value == 'toggle_tracking':
            await self.view.user_settings.update(tracking_enabled=not self.view.user_settings.tracking_enabled)
        elif select_value == 'toggle_ping':
            await self.view.user_settings.update(ping_after_message=not self.view.user_settings.ping_after_message)
        elif select_value == 'set_last_tt':
            modal = modals.SetLastTTModal(self.view)
            await interaction.response.send_modal(modal)
            return
        for child in self.view.children.copy():
            if isinstance(child, ManageUserSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageUserSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)