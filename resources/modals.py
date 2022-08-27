# modals.py

from datetime import datetime
import re

import discord
from discord.ui import InputText, Modal

from resources import emojis, strings


class SetStealthThresholdModal(Modal):
    def __init__(self, view: discord.ui.View) -> None:
        super().__init__(title='Change guild stealth threshold')
        self.view = view
        self.add_item(
            InputText(
                label='New guild stealth threshold (1-95):',
                placeholder="Enter amount ...",
            )
        )

    async def callback(self, interaction: discord.Interaction):
        stealth_threshold = self.children[0].value
        try:
            stealth_threshold = int(stealth_threshold)
        except ValueError:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('That is not a valid number.', ephemeral=True)
            return
        if not 1 <= stealth_threshold <= 95:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('The stealth threshold needs to be between 1 and 95.', ephemeral=True)
            return
        await self.view.clan_settings.update(stealth_threshold=stealth_threshold)
        embed = await self.view.embed_function(self.view.bot, self.view.clan_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class SetLastTTModal(Modal):
    def __init__(self, view: discord.ui.View) -> None:
        super().__init__(title='Change last time travel')
        self.view = view
        self.add_item(
            InputText(
                label='Message ID or link of your last time travel:',
                placeholder="Enter message ID or link ..."
            )
        )

    async def callback(self, interaction: discord.Interaction):
        msg_error = (
            f'No valid message ID or URL found.\n\n'
            f'Use the ID or link of the message that announced your time travel '
            f'("**{interaction.user.name}** has traveled in time {emojis.TIME_TRAVEL}").\n'
            f'If you don\'t have access to that message anymore, choose another message that is as close '
            f'to your last time travel as possible.\n'
            f'Note that it does not matter if I can actually read the message, I only need the ID or link.'
        )
        message_id_link = self.children[0].value.lower()
        if 'discord.com/channels' in message_id_link:
            message_id_match = re.search(r"\/[0-9]+\/[0-9]+\/(.+?)$", message_id_link)
            if message_id_match:
                message_id = message_id_match.group(1)
            else:
                await interaction.response.edit_message(view=self.view)
                await interaction.followup.send(msg_error, ephemeral=True)
                return
        else:
            message_id = message_id_link
        try:
            message_id = int(message_id)
            snowflake_binary = f'{message_id:064b}'
            timestamp_binary = snowflake_binary[:42]
            timestamp_decimal = int(timestamp_binary, 2)
            timestamp = (timestamp_decimal + 1_420_070_400_000) / 1000
            tt_time = datetime.utcfromtimestamp(timestamp).replace(microsecond=0)
        except:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(msg_error, ephemeral=True)
            return
        await self.view.user_settings.update(last_tt=tt_time.isoformat(sep=' '))
        if self.view.user_settings.last_tt != tt_time:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(strings.MSG_ERROR, ephemeral=True)
            return
        embed = await self.view.embed_function(self.view.bot, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)