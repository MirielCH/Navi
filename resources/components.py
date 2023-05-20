# components.py
"""Contains global interaction components"""

import asyncio
import re
from typing import Dict, List, Literal, Optional

import discord

from content import settings as settings_cmd
from database import cooldowns, portals, reminders, users
from resources import emojis, exceptions, functions, modals, strings, views


class ToggleAutoReadyButton(discord.ui.Button):
    """Button to toggle the auto-ready feature"""
    def __init__(self, custom_id: str, label: str, disabled: bool = False, emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=discord.ButtonStyle.grey, custom_id=custom_id, label=label, emoji=emoji,
                         disabled=disabled)

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.custom_id == 'follow':
            enabled = True
            response = (
                f'Done. I will now show you your ready commands after every created reminder.'
            )
        else:
            enabled = False
            response = 'Done. I will now stop showing your ready commands automatically.'
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
    """Simple Button. Writes its custom id to the view value, stops the view and does an invisible response."""
    def __init__(self, style: discord.ButtonStyle, custom_id: str, label: Optional[str],
                 emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.custom_id
        self.view.stop()
        try:
            await interaction.response.send_message()
        except Exception:
            pass


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
            emoji = emojis.ENABLED if setting_enabled else emojis.DISABLED
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
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)

class ToggleServerSettingsSelect(discord.ui.Select):
    """Toggle select that shows and toggles the status of server settings."""
    def __init__(self, view: discord.ui.View, toggled_settings: Dict[str, str], placeholder: str,
                 custom_id: Optional[str] = 'toggle_server_settings', row: Optional[int] = None):
        self.toggled_settings = toggled_settings
        options = []
        options.append(discord.SelectOption(label='Enable all', value='enable_all', emoji=None))
        options.append(discord.SelectOption(label='Disable all', value='disable_all', emoji=None))
        for label, setting in toggled_settings.items():
            setting_enabled = getattr(view.guild_settings, setting)
            if isinstance(setting_enabled, users.UserAlert):
                setting_enabled = getattr(setting_enabled, 'enabled')
            emoji = emojis.ENABLED if setting_enabled else emojis.DISABLED
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
            setting_value = getattr(self.view.guild_settings, select_value)
            if isinstance(setting_value, users.UserAlert):
                setting_value = getattr(setting_value, 'enabled')
            if not select_value.endswith('_enabled'):
                select_value = f'{select_value}_enabled'
            kwargs[select_value] = not setting_value
        await self.view.guild_settings.update(**kwargs)
        for child in self.view.children.copy():
            if child.custom_id == self.custom_id:
                self.view.remove_item(child)
                self.view.add_item(ToggleServerSettingsSelect(self.view, self.toggled_settings,
                                                            self.placeholder, self.custom_id))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.guild_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class ToggleReadySettingsSelect(discord.ui.Select):
    """Toggle select that shows and toggles the status of ready settings."""
    def __init__(self, view: discord.ui.View, toggled_settings: Dict[str, str], placeholder: str,
                 custom_id: Optional[str] = 'toggle_ready_settings', row: Optional[int] = None):
        self.toggled_settings = toggled_settings
        options = []
        options.append(discord.SelectOption(label='Show all', value='enable_all', emoji=None))
        options.append(discord.SelectOption(label='Hide all', value='disable_all', emoji=None))
        for label, setting in toggled_settings.items():
            setting_enabled = getattr(view.user_settings, setting)
            if isinstance(setting_enabled, users.UserAlert):
                setting_enabled = getattr(setting_enabled, 'visible')
            emoji = emojis.ENABLED if setting_enabled else emojis.DISABLED
            options.append(discord.SelectOption(label=label, value=setting, emoji=emoji))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row,
                         custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        kwargs = {}
        if select_value in ('enable_all','disable_all'):
            enabled = True if select_value == 'enable_all' else False
            for setting in self.toggled_settings.values():
                if not setting.endswith('_visible'):
                    setting = f'{setting}_visible'
                kwargs[setting] = enabled
        else:
            setting_value = getattr(self.view.user_settings, select_value)
            if isinstance(setting_value, users.UserAlert):
                setting_value = getattr(setting_value, 'visible')
            if not select_value.endswith('_visible'):
                select_value = f'{select_value}_visible'
            kwargs[select_value] = not setting_value
        await self.view.user_settings.update(**kwargs)
        for child in self.view.children.copy():
            if child.custom_id == self.custom_id:
                self.view.remove_item(child)
                self.view.add_item(ToggleReadySettingsSelect(self.view, self.toggled_settings,
                                                             self.placeholder, self.custom_id))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, self.view.clan_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class ManageClanSettingsSelect(discord.ui.Select):
    """Select to change guild settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        reminder_emoji = emojis.ENABLED if view.clan_settings.alert_enabled else emojis.DISABLED
        quest_emoji = emojis.ENABLED if view.clan_settings.upgrade_quests_enabled else emojis.DISABLED
        options.append(discord.SelectOption(label=f'Reminder',
                                            value='toggle_reminder', emoji=reminder_emoji))
        options.append(discord.SelectOption(label=f'Quests below stealth threshold',
                                            value='toggle_quest', emoji=quest_emoji))
        options.append(discord.SelectOption(label='Change stealth threshold',
                                            value='set_threshold'))
        options.append(discord.SelectOption(label='Add this channel as guild channel',
                                            value='set_channel', emoji=emojis.ADD))
        options.append(discord.SelectOption(label='Remove guild channel',
                                            value='reset_channel', emoji=emojis.REMOVE))
        if (view.clan_settings.quest_user_id is not None
            and view.clan_settings.quest_user_id == view.ctx.author.id):
            options.append(discord.SelectOption(label='Remove guild quest',
                                                value='remove_clan_quest', emoji=emojis.REMOVE))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_clan_settings')

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.clan_settings.leader_id:
            await interaction.response.send_message(
                f'**{interaction.user.name}**, you are not registered as the guild owner. Only the guild owner can '
                f'change these settings.\n'
                f'If you _are_ the guild owner, run {strings.SLASH_COMMANDS["guild list"]} to update '
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
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to set `{interaction.channel.name}` as the alert channel '
                f'for the guild `{self.view.clan_settings.clan_name}`?',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.clan_settings.update(channel_id=interaction.channel.id)
                await confirm_interaction.edit_original_response(content='Channel updated.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'reset_channel':
            if self.view.clan_settings.channel_id is None:
                await interaction.response.send_message(
                    f'You don\'t have a guild channel set already.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset the guild alert channel '
                f'for the guild `{self.view.clan_settings.clan_name}`?\n\n'
                f'Note that this will also disable the reminder if enabled.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.clan_settings.update(channel_id=None, alert_enabled=False)
                await confirm_interaction.edit_original_response(content='Channel reset.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'remove_clan_quest':
            await self.view.clan_settings.update(quest_user_id=None)
        for child in self.view.children.copy():
            if isinstance(child, ManageClanSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageClanSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.clan_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class ManageReadySettingsSelect(discord.ui.Select):
    """Select to change ready settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        frequency = 'hunt only' if view.user_settings.ready_after_all_commands else 'all commands'
        message_style = 'normal message' if view.user_settings.ready_as_embed else 'embed'
        up_next_reminder_emoji = emojis.ENABLED if view.user_settings.ready_up_next_visible else emojis.DISABLED
        up_next_style = 'static time' if view.user_settings.ready_up_next_as_timestamp else 'timestamp'
        if view.user_settings.ready_pets_claim_after_every_pet:
            pets_claim_type = 'when all pets are back'
        else:
            pets_claim_type = 'after every pet'
        if view.user_settings.ready_up_next_show_hidden_reminders:
            up_next_hidden_emoji = emojis.ENABLED
        else:
            up_next_hidden_emoji = emojis.DISABLED
        auto_ready_emoji = emojis.ENABLED if view.user_settings.auto_ready_enabled else emojis.DISABLED
        other_position = 'on bottom' if view.user_settings.ready_other_on_top else 'on top'
        options.append(discord.SelectOption(label=f'Auto-ready',
                                            value='toggle_auto_ready', emoji=auto_ready_emoji))
        options.append(discord.SelectOption(label=f'Show ready commands after {frequency}',
                                            value='toggle_frequency', emoji=None))
        options.append(discord.SelectOption(label=f'Show ready commands as {message_style}',
                                            value='toggle_message_style', emoji=None))
        options.append(discord.SelectOption(label='Change embed color',
                                            value='change_embed_color', emoji=None))
        options.append(discord.SelectOption(label=f'"Up next" reminder',
                                            value='toggle_up_next', emoji=up_next_reminder_emoji))
        options.append(discord.SelectOption(label=f'Show "up next" reminder with {up_next_style}',
                                            value='toggle_up_next_timestamp'))
        options.append(discord.SelectOption(label=f'Hidden reminders in "up next"',
                                            value='toggle_up_next_hidden_reminders', emoji=up_next_hidden_emoji))
        options.append(discord.SelectOption(label=f'Show "/pets claim" {pets_claim_type}',
                                                value='toggle_pets_claim'))
        if view.clan_settings is not None:
            clan_reminder_action = 'Hide' if view.clan_settings.alert_visible else 'Show'
            options.append(discord.SelectOption(label=f'{clan_reminder_action} guild channel reminder',
                                                value='toggle_alert'))
        options.append(discord.SelectOption(label=f'Show "other commands" {other_position}',
                                            value='toggle_other_position', emoji=None))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_ready_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_auto_ready':
            await self.view.user_settings.update(auto_ready_enabled=not self.view.user_settings.auto_ready_enabled)
        elif select_value == 'toggle_alert':
            await self.view.clan_settings.update(alert_visible=not self.view.clan_settings.alert_visible)
        elif select_value == 'toggle_frequency':
            await self.view.user_settings.update(
                ready_after_all_commands=not self.view.user_settings.ready_after_all_commands
            )
        elif select_value == 'toggle_message_style':
            await self.view.user_settings.update(ready_as_embed=not self.view.user_settings.ready_as_embed)
        elif select_value == 'change_embed_color':
            modal = modals.SetEmbedColorModal(self.view)
            await interaction.response.send_modal(modal)
            return
        elif select_value == 'toggle_up_next':
            await self.view.user_settings.update(
                ready_up_next_visible=not self.view.user_settings.ready_up_next_visible
            )
        elif select_value == 'toggle_up_next_timestamp':
            await self.view.user_settings.update(
                ready_up_next_as_timestamp=not self.view.user_settings.ready_up_next_as_timestamp
            )
        elif select_value == 'toggle_up_next_hidden_reminders':
            await self.view.user_settings.update(
                ready_up_next_show_hidden_reminders=not self.view.user_settings.ready_up_next_show_hidden_reminders
            )
        elif select_value == 'toggle_other_position':
            await self.view.user_settings.update(ready_other_on_top=not self.view.user_settings.ready_other_on_top)
        elif select_value == 'toggle_pets_claim':
            await self.view.user_settings.update(
                ready_pets_claim_after_every_pet=not self.view.user_settings.ready_pets_claim_after_every_pet
            )
        for child in self.view.children.copy():
            if isinstance(child, ManageReadySettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageReadySettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings,
                                               self.view.clan_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class SwitchReadyAltSelect(discord.ui.Select):
    """Select to switch between alts in /ready"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        emoji = emojis.BP if view.user.id == view.active_alt_id else None
        options = [discord.SelectOption(label=view.user.name, value=str(view.user.id), emoji=emoji),]
        for alt_id in view.user_settings.alts:
            alt = view.bot.get_user(alt_id)
            label = str(alt_id) if alt is None else alt.name
            emoji = emojis.BP if alt_id == view.active_alt_id else None
            options.append(discord.SelectOption(label=label, value=str(alt_id), emoji=emoji))
        super().__init__(placeholder='➜ Switch alt', min_values=1, max_values=1,
                         options=options, row=row,
                         custom_id='switch_alt')

    async def callback(self, interaction: discord.Interaction):
        alt_id = int(self.values[0])
        self.view.active_alt_id = alt_id
        alt = await functions.get_discord_user(self.view.bot, alt_id)
        embed, content = await self.view.embed_function(self.view.bot, alt, False)
        if self.view.user_settings.ready_as_embed:
            content = None
        else:
            embed = None
        for child in self.view.children.copy():
            if isinstance(child, SwitchReadyAltSelect):
                self.view.remove_item(child)
                self.view.add_item(SwitchReadyAltSelect(self.view))
        if interaction.response.is_done():
            await interaction.message.edit(content=content, embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(content=content, embed=embed, view=self.view)

            
class SwitchStatsAltSelect(discord.ui.Select):
    """Select to switch between alts in /stats"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        emoji = emojis.BP if view.user.id == view.active_alt_id else None
        options = [discord.SelectOption(label=view.user.name, value=str(view.user.id), emoji=emoji),]
        for alt_id in view.user_settings.alts:
            alt = view.bot.get_user(alt_id)
            label = str(alt_id) if alt is None else alt.name
            emoji = emojis.BP if alt_id == view.active_alt_id else None
            options.append(discord.SelectOption(label=label, value=str(alt_id), emoji=emoji))
        super().__init__(placeholder='➜ Switch alt', min_values=1, max_values=1,
                         options=options, row=row,
                         custom_id='switch_alt')

    async def callback(self, interaction: discord.Interaction):
        alt_id = int(self.values[0])
        self.view.active_alt_id = alt_id
        alt = await functions.get_discord_user(self.view.bot, alt_id)
        embed = await self.view.embed_function(self.view.bot, alt, self.view.time_left)
        for child in self.view.children.copy():
            if isinstance(child, SwitchStatsAltSelect):
                self.view.remove_item(child)
                self.view.add_item(SwitchReadyAltSelect(self.view))
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)

            
class SwitchRemindersListAltSelect(discord.ui.Select):
    """Select to switch between alts in /list"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        emoji = emojis.BP if view.user.id == view.active_alt_id else None
        options = [discord.SelectOption(label=view.user.name, value=str(view.user.id), emoji=emoji),]
        for alt_id in view.user_settings.alts:
            alt = view.bot.get_user(alt_id)
            label = str(alt_id) if alt is None else alt.name
            emoji = emojis.BP if alt_id == view.active_alt_id else None
            options.append(discord.SelectOption(label=label, value=str(alt_id), emoji=emoji))
        super().__init__(placeholder='➜ Switch alt', min_values=1, max_values=1,
                         options=options, row=row,
                         custom_id='switch_alt')

    async def callback(self, interaction: discord.Interaction):
        alt_id = int(self.values[0])
        self.view.active_alt_id = alt_id
        alt = await functions.get_discord_user(self.view.bot, alt_id)
        embed = await self.view.embed_function(self.view.bot, alt, self.view.show_timestamps)
        for child in self.view.children.copy():
            if isinstance(child, SwitchRemindersListAltSelect):
                self.view.remove_item(child)
                self.view.add_item(SwitchRemindersListAltSelect(self.view))
            if isinstance(child, DeleteCustomReminderSelect) and alt != self.view.user:
                self.view.remove_item(child)
            if isinstance(child, DeleteCustomRemindersButton) and alt != self.view.user:
                self.view.remove_item(child)
        if alt == self.view.user and self.view.custom_reminders: 
            self.view.add_item(DeleteCustomRemindersButton())
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
        await self.commands_settings[select_value](self.view.bot, self.view.ctx, switch_view = self.view)


class ManageUserSettingsSelect(discord.ui.Select):
    """Select to change user settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        reactions_emoji = emojis.ENABLED if view.user_settings.reactions_enabled else emojis.DISABLED
        auto_flex_emoji = emojis.ENABLED if view.user_settings.auto_flex_enabled else emojis.DISABLED
        tracking_emoji = emojis.ENABLED if view.user_settings.tracking_enabled else emojis.DISABLED
        options.append(discord.SelectOption(label=f'Reactions', emoji=reactions_emoji,
                                            value='toggle_reactions'))
        options.append(discord.SelectOption(label=f'Auto flex alerts', emoji=auto_flex_emoji,
                                            value='toggle_auto_flex'))
        options.append(discord.SelectOption(label=f'Command tracking', emoji=tracking_emoji,
                                            value='toggle_tracking'))
        options.append(discord.SelectOption(label=f'Change last time travel time',
                                            value='set_last_tt', emoji=None))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_user_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_reactions':
            await self.view.user_settings.update(reactions_enabled=not self.view.user_settings.reactions_enabled)
        elif select_value == 'toggle_auto_flex':
            await self.view.user_settings.update(auto_flex_enabled=not self.view.user_settings.auto_flex_enabled)
        elif select_value == 'toggle_tracking':
            await self.view.user_settings.update(tracking_enabled=not self.view.user_settings.tracking_enabled)
        elif select_value == 'set_last_tt':
            modal = modals.SetLastTTModal(self.view)
            await interaction.response.send_modal(modal)
            return
        for child in self.view.children.copy():
            if isinstance(child, ManageUserSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageUserSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class ManageReminderBehaviourSelect(discord.ui.Select):
    """Select to change reminder behaviour settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        dnd_emoji = emojis.ENABLED if view.user_settings.dnd_mode_enabled else emojis.DISABLED
        hunt_emoji = emojis.ENABLED if view.user_settings.hunt_rotation_enabled else emojis.DISABLED
        mentions_emoji = emojis.ENABLED if view.user_settings.slash_mentions_enabled else emojis.DISABLED
        #christmas_area_emoji = emojis.ENABLED if view.user_settings.christmas_area_enabled else emojis.DISABLED
        options.append(discord.SelectOption(label='DND mode', emoji=dnd_emoji,
                                            value='toggle_dnd'))
        options.append(discord.SelectOption(label='Hunt rotation', emoji=hunt_emoji,
                                            value='toggle_hunt'))
        options.append(discord.SelectOption(label='Slash command reminders', emoji=mentions_emoji,
                                            value='toggle_mentions'))
        options.append(discord.SelectOption(label='Add this channel as reminder channel', emoji=emojis.ADD,
                                            value='set_channel'))
        options.append(discord.SelectOption(label='Remove reminder channel', emoji=emojis.REMOVE,
                                            value='reset_channel'))
        #options.append(discord.SelectOption(label=f'{christmas_area_action} christmas area mode',
        #                                    value='toggle_christmas_area'))
        super().__init__(placeholder='Manage reminder behaviour', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_reminder_behaviour')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_dnd':
            await self.view.user_settings.update(dnd_mode_enabled=not self.view.user_settings.dnd_mode_enabled)
        elif select_value == 'toggle_hunt':
            await self.view.user_settings.update(hunt_rotation_enabled=not self.view.user_settings.hunt_rotation_enabled)
        elif select_value == 'toggle_mentions':
            await self.view.user_settings.update(slash_mentions_enabled=not self.view.user_settings.slash_mentions_enabled)
        elif select_value == 'set_channel':
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to set `{interaction.channel.name}` as the reminder '
                f'channel?\n'
                f'If a reminder channel is set, all reminders will be sent to that channel\n',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.user_settings.update(reminder_channel_id=interaction.channel.id)
                await confirm_interaction.edit_original_response(content='Channel updated.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'reset_channel':
            if self.view.user_settings.reminder_channel_id is None:
                await interaction.response.send_message(
                    f'You don\'t have a reminder channel set already.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset your reminder channel?\n\n'
                f'If you do this, reminders will be sent to where you create them.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.user_settings.update(reminder_channel_id=None)
                await confirm_interaction.edit_original_response(content='Channel reset.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        for child in self.view.children.copy():
            if isinstance(child, ManageReminderBehaviourSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageReminderBehaviourSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class RemoveAltSelect(discord.ui.Select):
    """Select to change alt settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        for alt_id in view.user_settings.alts:
            alt = view.bot.get_user(alt_id)
            label = str(alt_id) if alt is None else alt.name
            options.append(discord.SelectOption(label=label, value=str(alt_id), emoji=emojis.REMOVE))
        super().__init__(placeholder='Remove alts', min_values=1, max_values=1,
                         options=options, row=row,
                         custom_id='remove_alts')

    async def callback(self, interaction: discord.Interaction):
        alt_id = int(self.values[0])
        confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
        confirm_interaction = await interaction.response.send_message(
            f'**{interaction.user.name}**, do you want to remove <@{alt_id}> as your alt?',
            view=confirm_view,
            ephemeral=True
        )
        confirm_view.interaction_message = confirm_interaction
        await confirm_view.wait()
        if confirm_view.value == 'confirm':
            await self.view.user_settings.remove_alt(alt_id)
            await confirm_interaction.edit_original_response(content='Alt removed.', view=None)
        else:
            await confirm_interaction.edit_original_response(content='Aborted', view=None)
        for child in self.view.children.copy():
            if isinstance(child, RemoveAltSelect):
                self.view.remove_item(child)
                if self.view.user_settings.alts:
                    self.view.add_item(ManagePartnerSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)

            
class ManagePartnerSettingsSelect(discord.ui.Select):
    """Select to change partner settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        options.append(discord.SelectOption(label='Add this channel as partner channel',
                                            value='set_channel', emoji=emojis.ADD))
        options.append(discord.SelectOption(label='Remove partner channel',
                                            value='reset_channel', emoji=emojis.REMOVE))
        options.append(discord.SelectOption(label='Remove partner',
                                            value='reset_partner', emoji=emojis.REMOVE))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_partner_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'set_channel':
            if self.view.user_settings.partner_id is None:
                await interaction.response.send_message(
                    f'You need to set a partner first.\n'
                    f'To set a partner use {await functions.get_navi_slash_command(self.view.bot, "settings partner")} '
                    f'`partner: @partner`.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to set `{interaction.channel.name}` as the partner alert '
                f'channel?\n'
                f'The partner alert channel is where you will be sent lootbox alerts from your '
                f'partner. You can toggle partner alerts in `Reminder settings`.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.user_settings.update(partner_channel_id=interaction.channel.id)
                await confirm_interaction.edit_original_response(
                    content=(
                        f'Channel updated.\n'
                        f'To receive partner alerts, make sure the partner alert is enabled in `Reminder settings`.'
                    ),
                    view=None
                )
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'reset_channel':
            if self.view.user_settings.partner_channel_id is None:
                await interaction.response.send_message(
                    f'You don\'t have a partner alert channel set already.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset your partner alert channel?\n\n'
                f'If you do this, partner alerts will not work even if turned on.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.user_settings.update(partner_channel_id=None)
                await confirm_interaction.edit_original_response(content='Channel reset.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'reset_partner':
            if self.view.user_settings.partner_id is None:
                await interaction.response.send_message(
                    f'You don\'t have a partner set already.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset your partner?\n\n'
                f'This will also reset your partner\'s partner (which is you, heh) and set the '
                f'partner donor tiers back to `Non-donator`.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.user_settings.update(partner_id=None, partner_donor_tier=0)
                await self.view.partner_settings.update(partner_id=None, partner_donor_tier=0)
                self.view.partner_settings = None
                await confirm_interaction.edit_original_response(content='Partner reset.', view=None)
                for child in self.view.children.copy():
                    if isinstance(child, SetDonorTierSelect):
                        child.disabled = False
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        for child in self.view.children.copy():
            if isinstance(child, ManagePartnerSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManagePartnerSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, self.view.partner_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class SetDonorTierSelect(discord.ui.Select):
    """Select to set a donor tier"""
    def __init__(self, view: discord.ui.View, placeholder: str, donor_type: Optional[str] = 'user',
                 disabled: Optional[bool] = False, row: Optional[int] = None):
        self.donor_type = donor_type
        options = []
        for index, donor_tier in enumerate(strings.DONOR_TIERS):
            options.append(discord.SelectOption(label=donor_tier, value=str(index),
                                                emoji=strings.DONOR_TIERS_EMOJIS[donor_tier]))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, disabled=disabled,
                         row=row, custom_id=f'set_{donor_type}_donor_tier')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if self.donor_type == 'user':
            await self.view.user_settings.update(user_donor_tier=int(select_value))
        elif self.donor_type == 'partner':
            await self.view.user_settings.update(partner_donor_tier=int(select_value))
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)

        
class AddAltSelect(discord.ui.Select):
    """Select to add a new alt"""
    def __init__(self, view: discord.ui.View,
                 disabled: Optional[bool] = False, row: Optional[int] = None):
        super().__init__(select_type=discord.ComponentType.user_select, min_values=1, max_values=1, disabled=disabled,
                         row=row, custom_id='add_alt', placeholder='Add alts')

    async def callback(self, interaction: discord.Interaction):

        async def update_message() -> None:
            for child in self.view.children.copy():
                if isinstance(child, AddAltSelect):
                    self.view.remove_item(child)
                if isinstance(child, RemoveAltSelect):
                    self.view.remove_item(child)
                    
            embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
            if interaction.response.is_done():
                await interaction.message.edit(embed=embed, view=self.view)
            else:
                await interaction.response.edit_message(embed=embed, view=self.view)
            
            await asyncio.sleep(0.1)
            if len(self.view.user_settings.alts) < 24:
                self.view.add_item(AddAltSelect(self.view, row=0))
            if self.view.user_settings.alts:
                self.view.add_item(RemoveAltSelect(self.view, row=1))
            await interaction.message.edit(view=self.view)

        new_alt = self.values[0]
        if new_alt == interaction.user:
            await interaction.response.send_message(
                f'You want to add **yourself** as an alt? Are you **that** lonely?',
                ephemeral=True
            )
            await update_message()
            return
        if new_alt.id in self.view.user_settings.alts:
            await interaction.response.send_message(f'**{new_alt.name}** is already set as an alt.', ephemeral=True)
            await update_message()
            return
        if new_alt.bot:
            await interaction.response.send_message(
                f'Sorry, bots are not allowed to be alts, they are too smol.',
                ephemeral=True
            )
            await update_message()
            return
        if len(self.view.user_settings.alts) >= 24:
            await interaction.response.send_message(
                f'Your already has 24 alts and no space left. They need to remove one first.',
                ephemeral=True
            )
            await update_message()
            return
        try:
            new_alt_settings = await users.get_user(new_alt.id)
        except exceptions.FirstTimeUserError:
            await interaction.response.send_message(
                f'**{new_alt.name}** is not registered with Navi yet. They need to do '
                f'{await functions.get_navi_slash_command(self.view.bot, "on")} first.',
                ephemeral=True
            )
            await update_message()
            return
        if len(new_alt_settings.alts) >= 24:
            await interaction.response.send_message(
                f'**{new_alt.name}** already has 24 alts and no space left. They need to remove one first.',
                ephemeral=True
            )
            await update_message()
            return
        view = views.ConfirmUserView(new_alt, 'Sure', 'Ugh, no')
        interaction = await interaction.response.send_message(
            f'{new_alt.mention}, **{interaction.user.name}** wants to set you as their alt. '
            f'Do you want to allow that?\n\n'
            f'_Alts have the following benefits:_\n'
            f'{emojis.BP} _Alts are allowed to ping each other in reminders_\n'
            f'{emojis.BP} _You can quickly switch to alts in '
            f'{await functions.get_navi_slash_command(self.view.bot, "ready")}, '
            f'{await functions.get_navi_slash_command(self.view.bot, "list")}'
            f'and {await functions.get_navi_slash_command(self.view.bot, "stats")}._',
            view=view
        )
        view.interaction = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(
                interaction,
                content=f'**{interaction.user.name}**, the user didn\'t answer in time.',
                view=None
            )
        elif view.value == 'confirm':
            await self.view.user_settings.add_alt(new_alt.id)
            await functions.edit_interaction(
                interaction,
                content=f'**{interaction.user.name}** and **{new_alt.name}** are now alts of each other.',
                view=None
            )
        else:
            await functions.edit_interaction(
                interaction,
                content=(
                    f'**{new_alt.name}** doesn\'t want to be an alt. Oh no.\n'
                    f'Guess they don\'t like you. Oh well. Happens.'
                ),
                view=None
            )
        await update_message()

            
class AddPartnerSelect(discord.ui.Select):
    """Select to add a new partner"""
    def __init__(self, view: discord.ui.View, placeholder: str,
                 disabled: Optional[bool] = False, row: Optional[int] = None):
        super().__init__(select_type=discord.ComponentType.user_select, min_values=1, max_values=1, disabled=disabled,
                         row=row, custom_id='choose_user', placeholder=placeholder)

    async def callback(self, interaction: discord.Interaction):

        async def update_message() -> None:
            for child in self.view.children.copy():
                if isinstance(child, AddPartnerSelect):
                    self.view.remove_item(child)    
            embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings,
                                               self.view.partner_settings)
            if interaction.response.is_done():
                await interaction.message.edit(embed=embed, view=self.view)
            else:
                await interaction.response.edit_message(embed=embed, view=self.view)
            await asyncio.sleep(0.1)
            self.view.add_item(AddPartnerSelect(self.view, "Change partner", row=0))
            await interaction.message.edit(embed=embed, view=self.view)
        
        new_partner = self.values[0]
        if new_partner == interaction.user:
            await interaction.response.send_message('Marrying yourself? Now that\'s just sad.', ephemeral=True)
            await update_message()
            return
        try:
            new_partner_settings: users.User = await users.get_user(new_partner.id)
        except exceptions.FirstTimeUserError:
            await interaction.response.send_message(
                f'**{new_partner.name}** is not registered with Navi yet. They need to do '
                f'{await functions.get_navi_slash_command(self.view.bot, "on")} first.',
                ephemeral=True
            )
            await update_message()
            return
        if self.view.user_settings.partner_id is not None:
            view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            replace_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, you already have a partner set.\n'
                f'Setting a new partner will remove your old partner. Do you want to continue?',
                view=view,
                ephemeral=True
            )
            view.interaction_message = replace_interaction
            await view.wait()
            if view.value is None:
                await functions.edit_interaction(
                    replace_interaction,
                    content=f'**{interaction.user.name}**, you didn\'t answer in time.',
                    view=None
                )
                await update_message()
                return
            elif view.value == 'confirm':
                await functions.edit_interaction(replace_interaction, view=None)
            else:
                await functions.edit_interaction(replace_interaction, content='Aborted.', view=None)
                await update_message()
                return
        view = views.ConfirmUserView(new_partner, 'I do!', 'Forever alone')
        partner_answer = (
            f'{new_partner.mention}, **{interaction.user.name}** wants to set you as their partner.\n'
            f'Do you want to grind together until... idk, drama?'
        )
        if interaction.response.is_done():
            partner_interaction = await interaction.followup.send(partner_answer, view=view)
        else:
            partner_interaction = await interaction.response.send_message(partner_answer, view=view)
        view.interaction = partner_interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(
                partner_interaction,
                content=f'**{interaction.user.name}**, your lazy partner didn\'t answer in time.',
                view=None
            )
            await update_message()
            return
        elif view.value == 'confirm':
            if self.view.user_settings.partner_id is not None:
                try:
                    old_partner_settings = await users.get_user(self.view.user_settings.partner_id)
                    await old_partner_settings.update(partner_id=None)
                except exceptions.NoDataFoundError:
                    pass
            await self.view.user_settings.update(partner_id=new_partner.id, partner_donor_tier=new_partner_settings.user_donor_tier)
            await new_partner_settings.update(
                partner_id=interaction.user.id, partner_donor_tier=self.view.user_settings.user_donor_tier
            )
            if self.view.user_settings.partner_id == new_partner.id and new_partner_settings.partner_id == interaction.user.id:
                answer = (
                    f'{emojis.BP} **{interaction.user.name}**, {new_partner.name} is now set as your partner!\n'
                    f'{emojis.BP} **{new_partner.name}**, {interaction.user.name} is now set as your partner!\n'
                    f'{emojis.BP} **{interaction.user.name}**, {interaction.user.name} is now set as your partner\'s partner!\n'
                    f'{emojis.BP} **{new_partner.name}**, ... wait what?\n\n'
                    f'Anyway, you may now kiss the brides.'
                )
                await functions.edit_interaction(partner_interaction, view=None)
                await interaction.followup.send(answer)
            else:
                await interaction.followup.send(strings.MSG_ERROR)
                await update_message()
                return
        else:
            await functions.edit_interaction(
                partner_interaction,
                content=(
                    f'**{new_partner.name}** prefers to be forever alone.\n'
                    f'Stood up at the altar, that\'s gotta hurt, rip.'
                ),
                view=None
            )
            return
        self.view.partner_settings = new_partner_settings
        await update_message()


class ReminderMessageSelect(discord.ui.Select):
    """Select to select reminder messages by activity"""
    def __init__(self, view: discord.ui.View, activities: List[str], placeholder: str, custom_id: str,
                 row: Optional[int] = None):
        options = []
        options.append(discord.SelectOption(label='All', value='all', emoji=None))
        for activity in activities:
            options.append(discord.SelectOption(label=activity.replace('-',' ').capitalize(), value=activity, emoji=None))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row,
                         custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        self.view.activity = select_value
        all_custom_ids = []
        for child in self.view.children:
            all_custom_ids.append(child.custom_id)
        if select_value == 'all':
            if 'set_message' in all_custom_ids or 'reset_message' in all_custom_ids:
                for child in self.view.children.copy():
                    if child.custom_id in ('set_message', 'reset_message'):
                        self.view.remove_item(child)
            if 'reset_all' not in all_custom_ids:
                self.view.add_item(SetReminderMessageButton(style=discord.ButtonStyle.red, custom_id='reset_all',
                                                            label='Reset all messages', row=1))
        else:
            if 'reset_all' in all_custom_ids:
                for child in self.view.children.copy():
                    if child.custom_id == 'reset_all':
                        self.view.remove_item(child)
            if 'set_message' not in all_custom_ids:
                self.view.add_item(SetReminderMessageButton(style=discord.ButtonStyle.blurple, custom_id='set_message',
                                                            label='Change', row=1))
            if 'reset_message' not in all_custom_ids:
                self.view.add_item(SetReminderMessageButton(style=discord.ButtonStyle.red, custom_id='reset_message',
                                                            label='Reset', row=1))
        embeds = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, select_value)
        await interaction.response.edit_message(embeds=embeds, view=self.view)


class SetReminderMessageButton(discord.ui.Button):
    """Button to edit reminder messages"""
    def __init__(self, style: discord.ButtonStyle, custom_id: str, label: str, disabled: Optional[bool] = False,
                 emoji: Optional[discord.PartialEmoji] = None, row: Optional[int] = 1):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji,
                         disabled=disabled, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        def check(m: discord.Message) -> bool:
            return m.author == interaction.user and m.channel == interaction.channel

        if self.custom_id == 'reset_all':
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, this will reset **all** messages to the default one. '
                f'Are you sure?',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                kwargs = {}
                for activity in strings.ACTIVITIES:
                    activity_column = strings.ACTIVITIES_COLUMNS[activity]
                    kwargs[f'{activity_column}_message'] = strings.DEFAULT_MESSAGES[activity]
                await self.view.user_settings.update(**kwargs)
                await interaction.edit_original_response(
                    content=(
                        f'Changed all messages back to their default message.\n\n'
                        f'Note that running reminders do not update automatically.'
                    ),
                    view=None
                )
                embeds = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, self.view.activity)
                await interaction.message.edit(embeds=embeds, view=self.view)
                return
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif self.custom_id == 'set_message':
            await interaction.response.send_message(
                f'**{interaction.user.name}**, please send the new reminder message to this channel (or `abort` to abort):',
            )
            try:
                answer = await self.view.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                await interaction.edit_original_response(content=f'**{interaction.user.name}**, you didn\'t answer in time.')
                return
            for found_id in re.findall(r'<@(\d{16,20})>', answer.content.lower()):
                if int(found_id) not in self.view.user_settings.alts:
                    await interaction.delete_original_response(delay=5)
                    followup_message = await interaction.followup.send(
                        content=(
                            f'Aborted. You are only allowed to ping yourself and your alts set in '
                            f'{await functions.get_navi_slash_command(self.view.bot, "settings alts")} in reminders.'
                        ),
                    )
                    await followup_message.delete(delay=5)
                    return
            new_message = answer.content
            if new_message.lower() in ('abort','cancel','stop'):
                await interaction.delete_original_response(delay=3)
                followup_message = await interaction.followup.send('Aborted.')
                await followup_message.delete(delay=3)
                return
            if len(new_message) > 1024:
                await interaction.delete_original_response(delay=5)
                followup_message = await interaction.followup.send(
                    'This is a command to set a new message, not to write a novel :thinking:',
                )
                await followup_message.delete(delay=5)
                return
            for placeholder in re.finditer('\{(.+?)\}', new_message):
                placeholder_str = placeholder.group(1)
                if placeholder_str not in strings.DEFAULT_MESSAGES[self.view.activity]:
                    allowed_placeholders = ''
                    for placeholder in re.finditer('\{(.+?)\}', strings.DEFAULT_MESSAGES[self.view.activity]):
                        allowed_placeholders = (
                            f'{allowed_placeholders}\n'
                            f'{emojis.BP} {{{placeholder.group(1)}}}'
                        )
                    if allowed_placeholders == '':
                        allowed_placeholders = f'There are no placeholders available for this message.'
                    else:
                        allowed_placeholders = (
                            f'Available placeholders for this message:\n'
                            f'{allowed_placeholders.strip()}'
                        )
                    await interaction.delete_original_response(delay=3)
                    followup_message = await interaction.followup.send(
                        f'Invalid placeholder found.\n\n'
                        f'{allowed_placeholders}',
                        ephemeral=True
                    )
                    await followup_message.delete(delay=3)
                    return
            await interaction.delete_original_response(delay=3)
            followup_message = await interaction.followup.send(
                f'Message updated!\n\n'
                f'Note that running reminders do not update automatically.'
            )
            await followup_message.delete(delay=3)
        elif self.custom_id == 'reset_message':
            new_message = strings.DEFAULT_MESSAGES[self.view.activity]
        kwargs = {}
        activity_column = strings.ACTIVITIES_COLUMNS[self.view.activity]
        kwargs[f'{activity_column}_message'] = new_message
        await self.view.user_settings.update(**kwargs)
        embeds = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, self.view.activity)
        if interaction.response.is_done():
            await interaction.message.edit(embeds=embeds, view=self.view)
        else:
            await interaction.response.edit_message(embeds=embeds, view=self.view)


class DeleteCustomRemindersButton(discord.ui.Button):
    """Button to activate the select to delete custom reminders"""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.grey, custom_id='active_select', label='Delete custom reminders',
                         emoji=None, row=2)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.remove_item(self)
        self.view.add_item(DeleteCustomReminderSelect(self.view, self.view.custom_reminders))
        embed = await self.view.embed_function(self.view.bot, self.view.user, self.view.show_timestamps)
        await interaction.response.edit_message(embed=embed, view=self.view)


class ToggleTimestampsButton(discord.ui.Button):
    """Button to toggle reminder list between timestamps and timestrings"""
    def __init__(self, label: str):
        super().__init__(style=discord.ButtonStyle.grey, custom_id='toggle_timestamps', label=label,
                         emoji=None, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.show_timestamps = not self.view.show_timestamps
        if self.view.show_timestamps:
            self.label = 'Show time left'
        else:
            self.label = 'Show end time'
        embed = await self.view.embed_function(self.view.bot, self.view.user, self.view.show_timestamps)
        await interaction.response.edit_message(embed=embed, view=self.view)


class DeleteCustomReminderSelect(discord.ui.Select):
    """Select to delete custom reminders"""
    def __init__(self, view: discord.ui.View, custom_reminders: List[reminders.Reminder], row: Optional[int] = 2):
        self.custom_reminders = custom_reminders

        options = []
        for reminder in custom_reminders:
            label = f'{reminder.custom_id} - {reminder.message[:92]}'
            options.append(discord.SelectOption(label=label, value=str(reminder.custom_id), emoji=None))
        super().__init__(placeholder='Delete custom reminders', min_values=1, max_values=1, options=options,
                         row=row, custom_id=f'delete_reminders')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        for reminder in self.custom_reminders.copy():
            if reminder.custom_id == int(select_value):
                await reminder.delete()
                self.custom_reminders.remove(reminder)
                for custom_reminder in self.view.custom_reminders:
                    if custom_reminder.custom_id == reminder.custom_id:
                        self.view.custom_reminder.remove(custom_reminder)
                        break
        embed = await self.view.embed_function(self.view.bot, self.view.user, self.view.show_timestamps)
        self.view.remove_item(self)
        if self.custom_reminders:
            self.view.add_item(DeleteCustomReminderSelect(self.view, self.view.custom_reminders))
        await interaction.response.edit_message(embed=embed, view=self.view)


class ToggleTrackingButton(discord.ui.Button):
    """Button to toggle the auto-ready feature"""
    def __init__(self, style: Optional[discord.ButtonStyle], custom_id: str, label: str,
                 disabled: bool = False, emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji,
                         disabled=disabled, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        enabled = True if self.custom_id == 'track' else False
        await self.view.user_settings.update(tracking_enabled=enabled)
        self.view.value = self.custom_id
        await self.view.user_settings.refresh()
        if self.view.user_settings.tracking_enabled:
            self.style = discord.ButtonStyle.grey
            self.label = 'Stop tracking me!'
            self.custom_id = 'untrack'
        else:
            self.style = discord.ButtonStyle.green
            self.label = 'Track me!'
            self.custom_id = 'track'
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self.view)
        else:
            await self.view.message.edit(view=self.view)


class ManageHelperSettingsSelect(discord.ui.Select):
    """Select to change helper settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        tr_helper_mode = 'text' if view.user_settings.training_helper_button_mode else 'buttons'
        pet_helper_mode = 'commands' if view.user_settings.pet_helper_icon_mode else 'icons'
        ruby_counter_mode = 'text' if view.user_settings.ruby_counter_button_mode else 'buttons'
        ping_mode_setting = 'before' if view.user_settings.ping_after_message else 'after'
        options.append(discord.SelectOption(label=f'Change pet catch helper to {pet_helper_mode}',
                                            value='toggle_pet_helper_mode'))
        options.append(discord.SelectOption(label=f'Change ruby counter to {ruby_counter_mode}',
                                            value='toggle_ruby_counter_mode'))
        options.append(discord.SelectOption(label=f'Change training helper to {tr_helper_mode}',
                                            value='toggle_tr_helper_mode'))
        options.append(discord.SelectOption(label=f'Ping {ping_mode_setting} helper message',
                                            value='toggle_ping_mode'))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_user_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_tr_helper_mode':
            await self.view.user_settings.update(
                training_helper_button_mode=not self.view.user_settings.training_helper_button_mode
            )
        elif select_value == 'toggle_pet_helper_mode':
            await self.view.user_settings.update(
                pet_helper_icon_mode=not self.view.user_settings.pet_helper_icon_mode
            )
        elif select_value == 'toggle_ruby_counter_mode':
            await self.view.user_settings.update(
                ruby_counter_button_mode=not self.view.user_settings.ruby_counter_button_mode
            )
        elif select_value == 'toggle_ping_mode':
            await self.view.user_settings.update(
                ping_after_message=not self.view.user_settings.ping_after_message
            )
        for child in self.view.children.copy():
            if isinstance(child, ManageHelperSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageHelperSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class SetFarmHelperModeSelect(discord.ui.Select):
    """Select to change farm helper mode"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        for value, label in strings.FARM_HELPER_MODES.items():
            emoji = emojis.ENABLED if view.user_settings.farm_helper_mode == value else None
            options.append(discord.SelectOption(label=label, value=str(value), emoji=emoji))
        super().__init__(placeholder='Change farm helper mode', min_values=1, max_values=1, options=options, row=row,
                         custom_id='set_farm_helper_mode')

    async def callback(self, interaction: discord.Interaction):
        await self.view.user_settings.update(farm_helper_mode=int(self.values[0]))
        try:
            reminder = await reminders.get_user_reminder(self.view.user_settings.user_id, 'farm')
            user_command = await functions.get_farm_command(self.view.user_settings)
            reminder_message = self.view.user_settings.alert_farm.message.replace('{command}', user_command)
            await reminder.update(message=reminder_message)
        except exceptions.NoDataFoundError:
            pass
        for child in self.view.children.copy():
            if isinstance(child, SetFarmHelperModeSelect):
                self.view.remove_item(child)
                self.view.add_item(SetFarmHelperModeSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class ManageServerSettingsSelect(discord.ui.Select):
    """Select to change server settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        auto_flex_emoji = emojis.ENABLED if view.guild_settings.auto_flex_enabled else emojis.DISABLED
        reminder_action = 'Disable' if view.guild_settings.auto_flex_enabled else 'Enable'
        options.append(discord.SelectOption(label='Change prefix',
                                            value='set_prefix', emoji=None))
        options.append(discord.SelectOption(label=f'{reminder_action} auto flex alerts',
                                            value='toggle_auto_flex', emoji=auto_flex_emoji))
        options.append(discord.SelectOption(label='Set this channel as auto flex channel',
                                            value='set_channel', emoji=emojis.ADD))
        options.append(discord.SelectOption(label='Reset auto flex channel',
                                            value='reset_channel', emoji=emojis.REMOVE))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_server_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_auto_flex':
            if not self.view.guild_settings.auto_flex_enabled and self.view.guild_settings.auto_flex_channel_id is None:
                await interaction.response.send_message('You need to set an auto flex channel first.', ephemeral=True)
                return
            await self.view.guild_settings.update(auto_flex_enabled=not self.view.guild_settings.auto_flex_enabled)
        elif select_value == 'set_prefix':
            modal = modals.SetPrefixModal(self.view)
            await interaction.response.send_modal(modal)
            return
        elif select_value == 'set_channel':
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to set `{interaction.channel.name}` as the auto flex channel?',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.guild_settings.update(auto_flex_channel_id=interaction.channel.id)
                await confirm_interaction.edit_original_response(content='Channel updated.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        elif select_value == 'reset_channel':
            if self.view.guild_settings.auto_flex_channel_id is None:
                await interaction.response.send_message(
                    f'You don\'t have an auto flex channel set already.',
                    ephemeral=True
                )
                return
            confirm_view = views.ConfirmCancelView(self.view.ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
            confirm_interaction = await interaction.response.send_message(
                f'**{interaction.user.name}**, do you want to reset the auto flex channel?\n\n'
                f'Note that this will also disable the auto flex alerts if enabled.',
                view=confirm_view,
                ephemeral=True
            )
            confirm_view.interaction_message = confirm_interaction
            await confirm_view.wait()
            if confirm_view.value == 'confirm':
                await self.view.guild_settings.update(auto_flex_channel_id=None, auto_flex_enabled=False)
                await confirm_interaction.edit_original_response(content='Channel reset.', view=None)
            else:
                await confirm_interaction.edit_original_response(content='Aborted', view=None)
                return
        for child in self.view.children.copy():
            if isinstance(child, ManageServerSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManageServerSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.guild_settings)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class ManageMultipliersSelect(discord.ui.Select):
    """Select to change multipliers"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        options.append(discord.SelectOption(label=f'All',
                                            value='all'))
        for activity in strings.ACTIVITIES_WITH_CHANGEABLE_MULTIPLIER:
            options.append(discord.SelectOption(label=activity.capitalize(),
                                                value=activity))
        super().__init__(placeholder='Change multipliers', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_multipliers')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        modal = modals.SetMultiplierModal(self.view, select_value)
        await interaction.response.send_modal(modal)


class ManageEventReductionsSelect(discord.ui.Select):
    """Select to manage cooldowns"""
    def __init__(self, view: discord.ui.View, all_cooldowns: List[cooldowns.Cooldown],
                 cd_type: Literal['slash', 'text'], row: Optional[int] = None):
        self.all_cooldowns = all_cooldowns
        self.cd_type = cd_type
        options = []
        options.append(discord.SelectOption(label=f'All',
                                            value='all'))
        for cooldown in all_cooldowns:
            options.append(discord.SelectOption(label=cooldown.activity.capitalize(),
                                                value=cooldown.activity))
            cooldown.update()
        placeholders = {
            'slash': 'Change slash event reductions',
            'text': 'Change text event reductions',
        }
        super().__init__(placeholder=placeholders[cd_type], min_values=1, max_values=1, options=options, row=row,
                         custom_id=f'manage_{cd_type}')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        modal = modals.SetEventReductionModal(self.view, select_value, self.cd_type)
        await interaction.response.send_modal(modal)


class CopyEventReductionsButton(discord.ui.Button):
    """Button to toggle the auto-ready feature"""
    def __init__(self, style: Optional[discord.ButtonStyle], custom_id: str, label: str,
                 disabled: bool = False, emoji: Optional[discord.PartialEmoji] = None):
        super().__init__(style=style, custom_id=custom_id, label=label, emoji=emoji,
                         disabled=disabled)

    async def callback(self, interaction: discord.Interaction) -> None:
        for cooldown in self.view.all_cooldowns:
            if self.custom_id == 'copy_slash_text':
                await cooldown.update(event_reduction_mention=cooldown.event_reduction_slash)
            else:
                await cooldown.update(event_reduction_slash=cooldown.event_reduction_mention)
        embed = await self.view.embed_function(self.view.all_cooldowns)
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            await self.view.message.edit(embed=embed, view=self.view)


class ManagePortalsSelect(discord.ui.Select):
    """Select to change portal settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        if len(view.user_portals) < 20:
            options.append(discord.SelectOption(label=f'Add portal', emoji=emojis.ADD,
                                                value='add_portal'))
        for index, portal in enumerate(view.user_portals):
            options.append(discord.SelectOption(label=f'Remove portal {index + 1} ({portal.channel_id})',
                                                emoji=emojis.REMOVE,
                                                value=f'remove_{portal.channel_id}'))
        super().__init__(placeholder='Manage portals', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_portals')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'add_portal':
            modal = modals.AddPortalModal(self.view, ManagePortalsSelect)
            await interaction.response.send_modal(modal)
        else:
            channel_id = int(select_value.replace('remove_', ''))
            portal = await portals.get_portal(self.view.user_settings.user_id, channel_id)
            await portal.delete()
            self.view.user_portals.remove(portal)
        for child in self.view.children.copy():
            if isinstance(child, ManagePortalsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManagePortalsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings,
                                               self.view.user_portals)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)


class SwitchToReadyRemindersSelect(discord.ui.Select):
    """Select to switch to ready reminder settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        options.append(discord.SelectOption(label='Manage visible commands and command channels',
                                            value='switch_to_ready_reminders'))
        super().__init__(placeholder='Manage visible commands and command channels', min_values=1, max_values=1,
                         options=options, row=row, custom_id='switch_to_ready_reminders')

    async def callback(self, interaction: discord.Interaction):
        view = views.SettingsReadyRemindersView(self.view.ctx, self.view.bot, self.view.user_settings,
                                                self.view.clan_settings, settings_cmd.embed_settings_ready_reminders)
        embed = await settings_cmd.embed_settings_ready_reminders(self.view.bot, self.view.ctx, self.view.user_settings,
                                                                  self.view.clan_settings)
        await interaction.response.edit_message(embed=embed, view=view)
        view.interaction = interaction
        self.view.stop()


class ManageReadyReminderChannelsSelect(discord.ui.Select):
    """Select to manage ready reminder channel settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        options.append(discord.SelectOption(label=f'Add arena channel', emoji=emojis.ADD,
                                            value='add_channel_arena'))
        options.append(discord.SelectOption(label=f'Add duel channel', emoji=emojis.ADD,
                                            value='add_channel_duel'))
        options.append(discord.SelectOption(label=f'Add dungeon channel', emoji=emojis.ADD,
                                            value='add_channel_dungeon'))
        options.append(discord.SelectOption(label=f'Add horse breed channel', emoji=emojis.ADD,
                                            value='add_channel_horse'))
        options.append(discord.SelectOption(label=f'Remove arena channel', emoji=emojis.REMOVE,
                                            value='remove_channel_arena'))
        options.append(discord.SelectOption(label=f'Remove duel channel', emoji=emojis.REMOVE,
                                            value='remove_channel_duel'))
        options.append(discord.SelectOption(label=f'Remove dungeon channel', emoji=emojis.REMOVE,
                                            value='remove_channel_dungeon'))
        options.append(discord.SelectOption(label=f'Remove horse breed channel', emoji=emojis.REMOVE,
                                            value='remove_channel_horse'))
        super().__init__(placeholder='Manage command channels', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_command_channels')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'remove_channel_arena':
            await self.view.user_settings.update(ready_channel_arena=None)
        elif select_value == 'remove_channel_duel':
            await self.view.user_settings.update(ready_channel_duel=None)
        elif select_value == 'remove_channel_dungeon':
            await self.view.user_settings.update(ready_channel_dungeon=None)
        elif select_value == 'remove_channel_horse':
            await self.view.user_settings.update(ready_channel_horse=None)
        else:
            modal = modals.AddCommandChannelModal(self.view, select_value.replace('add_channel_',''))
            await interaction.response.send_modal(modal)
            return
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings,
                                               self.view.clan_settings)
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self.view)
        else:
            await self.view.message.edit(embed=embed, view=self.view)


class ManagePortalSettingsSelect(discord.ui.Select):
    """Select to change portal settings"""
    def __init__(self, view: discord.ui.View, row: Optional[int] = None):
        options = []
        message_style = 'normal message' if view.user_settings.portals_as_embed else 'embed'
        spacing_emoji = emojis.ENABLED if view.user_settings.portals_spacing_enabled else emojis.DISABLED
        options.append(discord.SelectOption(label=f'Show portal list as {message_style}',
                                            value='toggle_message_style', emoji=None))
        options.append(discord.SelectOption(label=f'Mobile spacing', emoji=spacing_emoji,
                                            value='toggle_mobile_spacing'))
        super().__init__(placeholder='Change settings', min_values=1, max_values=1, options=options, row=row,
                         custom_id='manage_portal_settings')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        if select_value == 'toggle_mobile_spacing':
            await self.view.user_settings.update(
                portals_spacing_enabled=not self.view.user_settings.portals_spacing_enabled
            )
        elif select_value == 'toggle_message_style':
            await self.view.user_settings.update(portals_as_embed=not self.view.user_settings.portals_as_embed)
        for child in self.view.children.copy():
            if isinstance(child, ManagePortalSettingsSelect):
                self.view.remove_item(child)
                self.view.add_item(ManagePortalSettingsSelect(self.view))
                break
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings,
                                               self.view.user_portals)
        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.response.edit_message(embed=embed, view=self.view)