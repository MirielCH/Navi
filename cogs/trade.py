# trade.py

import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from resources import emojis, exceptions, functions, regex, settings, strings, views


class TradeCog(commands.Cog):
    """Cog that contains all commands related to trading with the exception of the ruby helper"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        for row in message_after.components:
            for component in row.children:
                if component.disabled:
                    return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return

        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_description = message_field = message_author = ''
            if embed.description: message_description = str(embed.description)
            if embed.fields: message_field = str(embed.fields[0].value)
            if embed.author:
                message_author = str(embed.author.name)
                icon_url = embed.author.icon_url

            # Tracks daily trades done
            search_strings = [
                'our trade is done then', #English
                'nuestro intercambio está hecho entonces', #Spanish
                'nossa troca é feita então', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_name = user_command_message = None
                trade_from, trade_to = message_field.split('\n')[:2]
                user_name_match = re.search(r"\*\*(.+?)\*\*:", trade_from)
                user_name = user_name_match.group(1)
                if user_name in strings.EPIC_NPC_NAMES: return
                trade_from_data_match = re.search(r'<:(.+?):\d+> x([\d,]+)$', trade_from.strip().lower())
                trade_from_item = trade_from_data_match.group(1)
                trade_from_amount = int(trade_from_data_match.group(2).replace(',',''))
                trade_to_data_match = re.search(r'<:(.+?):\d+> x([\d,]+)$', trade_to.strip().lower())
                trade_to_item = trade_to_data_match.group(1)
                trade_to_amount = int(trade_to_data_match.group(2).replace(',',''))
                trade_daily_found = False
                traded_amount = min(trade_from_amount, trade_to_amount)
                if (trade_from_item == 'woodenlog' and trade_to_item == 'normiefish'
                    and trade_to_amount / trade_from_amount == 4):
                    trade_daily_found = True
                if (trade_from_item == 'woodenlog' and trade_to_item == 'apple'
                    and trade_to_amount / trade_from_amount == 2):
                    trade_daily_found = True
                if (trade_from_item == 'woodenlog' and trade_to_item == 'ruby'
                    and trade_from_amount / trade_to_amount == 25):
                    trade_daily_found = True
                    traded_amount = trade_to_amount
                if (trade_from_item == 'normiefish' and trade_to_item == 'woodenlog'
                    and trade_to_amount / trade_from_amount == 12):
                    trade_daily_found = True
                if (trade_from_item == 'apple' and trade_to_item == 'woodenlog'
                    and trade_to_amount / trade_from_amount == 50):
                    trade_daily_found = True
                if (trade_from_item == 'ruby' and trade_to_item == 'woodenlog'
                    and trade_to_amount / trade_from_amount == 1_000):
                    trade_daily_found = True
                if not trade_daily_found: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRADE_DAILY,
                                                    user_name=user_name)
                    )
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.top_hat_unlocked: return
                await user_settings.update(trade_daily_done=user_settings.trade_daily_done + traded_amount)
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

            # Updates daily trades total and done from trade list
            search_strings = [
                'are you looking to trade your items?', #English
                'estás buscando intercambiar tus items?', #Spanish
                'pretende trocar os seus itens?', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r", \*\*(.+?)\*\*!", message_description.split('\n')[0])
                    user_name = user_name_match.group(1)
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRADE,
                                                    user_name=user_name)
                    )
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled: return
                if not 'tophat' in message_description.lower():
                    if user_settings.top_hat_unlocked:
                        await user_settings.update(top_hat_unlocked=False)
                    return
                else:
                    if not user_settings.top_hat_unlocked:
                        await user_settings.update(top_hat_unlocked=True)
                trade_daily_data = re.search(r'\*\*([\d,]+)/([\d,]+)\*\*', message_description.lower())
                trade_daily_done = int(trade_daily_data.group(1).replace(',',''))
                trade_daily_total = int(trade_daily_data.group(2).replace(',',''))
                await user_settings.update(trade_daily_done=trade_daily_done, trade_daily_total=trade_daily_total)
                if user_settings.reactions_enabled: await message.add_reaction(emojis.NAVI)

# Initialization
def setup(bot):
    bot.add_cog(TradeCog(bot))