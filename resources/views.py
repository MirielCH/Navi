# views.py
"""Contains global interaction views"""

from typing import Optional

import discord

from database import users
from resources import components, settings, strings


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