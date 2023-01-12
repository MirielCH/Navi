# modals.py

from datetime import datetime
import re
from typing import Literal

import discord
from discord.ui import InputText, Modal

from database import reminders
from resources import emojis, exceptions, strings


class SetEmbedColorModal(Modal):
    def __init__(self, view: discord.ui.View) -> None:
        super().__init__(title='Change ready list embed color')
        self.view = view
        self.add_item(
            InputText(
                label='New embed color:',
                placeholder="Enter hex code ...",
            )
        )

    async def callback(self, interaction: discord.Interaction):
        new_color = self.children[0].value
        color_match = re.match(r'^#?(?:[0-9a-fA-F]{3}){1,2}$', new_color)
        if not color_match:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('That is not a valid hex code.', ephemeral=True)
            return
        await self.view.user_settings.update(ready_embed_color=new_color.replace('#','').upper())
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings, self.view.clan_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


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
        new_threshold = self.children[0].value
        try:
            new_threshold = int(new_threshold)
        except ValueError:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('That is not a valid number.', ephemeral=True)
            return
        if not 1 <= new_threshold <= 95:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('The stealth threshold needs to be between 1 and 95.', ephemeral=True)
            return
        await self.view.clan_settings.update(stealth_threshold=new_threshold)
        try:
            reminder: reminders.Reminder = await reminders.get_clan_reminder(self.view.clan_settings.clan_name)
            if new_threshold <= self.view.clan_settings.stealth_current:
                new_message = reminder.message.replace('upgrade','raid')
            else:
                new_message = reminder.message.replace('raid','upgrade')
            await reminder.update(message=new_message)
        except exceptions.NoDataFoundError:
            pass
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.clan_settings)
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
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class SetPrefixModal(Modal):
    def __init__(self, view: discord.ui.View) -> None:
        super().__init__(title='Change prefix')
        self.view = view
        self.add_item(
            InputText(
                label='New prefix:',
                placeholder="Enter prefix ...",
            )
        )

    async def callback(self, interaction: discord.Interaction):
        new_prefix = self.children[0].value
        await self.view.guild_settings.update(prefix=new_prefix)
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.guild_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class SetMultiplierModal(Modal):
    def __init__(self, view: discord.ui.View, activity: str) -> None:
        super().__init__(title='Change command multiplier')
        self.view = view
        self.activity = activity
        self.add_item(
            InputText(
                label='New multiplier (0.01 - 2.00):',
                placeholder="Enter multiplier ...",
            )
        )

    async def callback(self, interaction: discord.Interaction):
        new_multiplier = self.children[0].value
        try:
            new_multiplier = float(new_multiplier)
        except ValueError:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('That is not a valid number.', ephemeral=True)
            return
        if not 0.01 <= new_multiplier <= 2.0:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('The multiplier needs to be between 0.01 and 2.00', ephemeral=True)
            return
        kwargs = {}
        if self.activity == 'all':
            for activity in strings.ACTIVITIES_WITH_CHANGEABLE_MULTIPLIER:
                kwargs[f'alert_{activity}_multiplier'] = new_multiplier
        else:
            kwargs[f'alert_{self.activity}_multiplier'] = new_multiplier
        await self.view.user_settings.update(**kwargs)
        embed = await self.view.embed_function(self.view.bot, self.view.ctx, self.view.user_settings)
        await interaction.response.edit_message(embed=embed, view=self.view)


class SetEventReductionModal(Modal):
    def __init__(self, view: discord.ui.View, activity: str, cd_type: Literal['slash', 'text']) -> None:
        titles = {
            'slash': 'Change slash event reduction',
            'text': 'Change text event reduction',
        }
        labels = {
            'slash': 'Event reduction in percent:',
            'text': 'Event reduction in percent:',
        }
        placeholders = {
            'slash': 'Enter event reduction...',
            'text': 'Enter event reduction...',
        }
        super().__init__(title=titles[cd_type])
        self.view = view
        self.activity = activity
        self.cd_type = cd_type
        self.add_item(
            InputText(
                label=labels[cd_type],
                placeholder=placeholders[cd_type],
            )
        )

    async def callback(self, interaction: discord.Interaction):
        new_value = self.children[0].value
        try:
            new_value = float(new_value)
        except ValueError:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('That is not a valid number.', ephemeral=True)
            return
        if not 0 <= new_value <= 100:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send('The reduction needs to be between 0 and 100 percent.', ephemeral=True)
            return
        if self.activity == 'all':
            for cooldown in self.view.all_cooldowns:
                if self.cd_type == 'slash':
                    await cooldown.update(event_reduction_slash=new_value)
                else:
                    await cooldown.update(event_reduction_mention=new_value)
        else:
            for cooldown in self.view.all_cooldowns:
                if cooldown.activity == self.activity:
                    if self.cd_type == 'slash':
                        await cooldown.update(event_reduction_slash=new_value)
                    else:
                        await cooldown.update(event_reduction_mention=new_value)
        embed = await self.view.embed_function(self.view.all_cooldowns)
        await interaction.response.edit_message(embed=embed, view=self.view)