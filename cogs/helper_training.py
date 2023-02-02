# helper_training.py

import re
from datetime import datetime

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from database import settings as settings_db
from resources import emojis, exceptions, functions, settings, regex, views


class HelperTrainingCog(commands.Cog):
    """Cog that contains the training helper detection"""
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
            message_description = ''
            if embed.description: message_description = embed.description
            # Void area unseal times
            search_strings = [
                'help us unseal the next areas!', #English
                'ayudanos a abrir las siguientes áreas!', #Spanish
                'ajude-nos a abrir as seguintes áreas!', #Portuguese
            ]
            if any(search_string in message_description.lower() for search_string in search_strings):
                updated_settings = False
                for field in embed.fields:
                    search_strings = [
                        'unsealed', #English
                        'abierto', #Spanish
                        'aberto', #Portuguese, UNCONFIRMED
                    ]
                    if any(search_string in field.value.lower() for search_string in search_strings):
                        seal_timestring_match = re.search(r"__: (.+?)$", field.value)
                        if seal_timestring_match:
                            area_no = int(field.name[-2:])
                            seal_timestring = seal_timestring_match.group(1).replace(' ','')
                            seal_time_left = await functions.parse_timestring_to_timedelta(seal_timestring.lower())
                            current_time = datetime.utcnow().replace(microsecond=0)
                            seal_time = current_time + seal_time_left
                            await settings_db.update_setting(f'a{area_no}_seal_time', seal_time)
                            updated_settings = True
                        else:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Timestring not found for void areas message.', message)
                            return
                if updated_settings: await message.add_reaction(emojis.NAVI)

        if not message.embeds:
            message_content = message.content
            # Training helper
            search_strings_included = [
                '** is training in the', #English
                '** está entrenando', #Spanish
                '** está treinando', #Portuguese
            ]
            search_strings_not_included = [
                'in the mine!', #English
                'en la mina!', #Spanish
                'na mina!', #Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings_included)
                and all(search_string not in message_content.lower() for search_string in search_strings_not_included)):
                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for training helper message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.training_helper_enabled: return
                search_strings_void = [
                    'training in the void', #English
                    'vacío', #Spanish, UNCONFIRMED
                    'vazio', #Portuguese, UNCONFIRMED
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_void):
                    if user_settings.training_helper_button_mode:
                        answer, buttons = await functions.get_void_training_answer_buttons(message, user_settings)
                        if buttons:
                            answer = None if user_settings.dnd_mode_enabled else user.mention
                            view = views.TrainingAnswerView(buttons)
                            await message.reply(content=answer, view=view)
                        else:
                            if not user_settings.dnd_mode_enabled:
                                if user_settings.ping_after_message:
                                    answer = f'{user.mention}\n{answer}' if emojis.BP in answer else f'{user.mention} {answer}'
                                else:
                                    answer = f'{answer}\n{user.mention}' if emojis.BP in answer else f'{answer} {user.mention}'
                            await message.reply(answer)
                    else:
                        answer = await functions.get_void_training_answer_text(message, user_settings)
                        if not user_settings.dnd_mode_enabled:
                            if user_settings.ping_after_message:
                                answer = f'{user.mention}\n{answer}' if emojis.BP in answer else f'{user.mention} {answer}'
                            else:
                                answer = f'{answer}\n{user.mention}' if emojis.BP in answer else f'{answer} {user.mention}'
                        await message.reply(answer)
                else:
                    if user_settings.training_helper_button_mode:
                        answer = None if user_settings.dnd_mode_enabled else user.mention
                        buttons = await functions.get_training_answer_buttons(message)
                        view = views.TrainingAnswerView(buttons)
                        await message.reply(content=answer, view=view)
                    else:
                        answer = await functions.get_training_answer_text(message)
                        if not user_settings.dnd_mode_enabled:
                            if user_settings.ping_after_message:
                                answer = f'{answer} {user.mention}'
                            else:
                                answer = f'{user.mention} {answer}'
                        await message.reply(answer)


# Initialization
def setup(bot):
    bot.add_cog(HelperTrainingCog(bot))