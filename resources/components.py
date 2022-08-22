# components.py
"""Contains global interaction components"""

from typing import Optional

import discord


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


class ToggleSelect(discord.ui.Select):
    """Toggle select that shows and toggles the status of booleans. Also adds "Enable all" and "Disable all" on top."""
    def __init__(self, topics: dict, active_topic: str, placeholder: str, row: Optional[int] = None):
        self.topics = topics
        options = []
        for topic in topics.keys():
            label = topic
            emoji = '🔹' if topic == active_topic else None
            options.append(discord.SelectOption(label=label, value=label, emoji=emoji))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, row=row,
                         custom_id='select_topic')

    async def callback(self, interaction: discord.Interaction):
        select_value = self.values[0]
        self.view.active_topic = select_value
        for child in self.view.children:
            if child.custom_id == 'select_topic':
                options = []
                for topic in self.topics.keys():
                    label = topic
                    emoji = '🔹' if topic == self.view.active_topic else None
                    options.append(discord.SelectOption(label=label, value=label, emoji=emoji))
                child.options = options
                break
        embed = await self.view.topics[select_value]()
        await interaction.response.edit_message(embed=embed, view=self.view)