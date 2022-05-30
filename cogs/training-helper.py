# training-helper.py

import re
from datetime import datetime

import discord
from discord.ext import commands

from database import errors, users
from database import settings as settings_db
from resources import emojis, exceptions, functions, settings


class TrainingHelperCog(commands.Cog):
    """Cog that contains the training helper detection"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_description = ''
            if embed.description: message_description = embed.description
            # Void area unseal times
            if 'help us unseal the next areas!' in message_description.lower():
                updated_settings = False
                for field in embed.fields:
                    if 'unsealed' in field.value.lower():
                        try:
                            area_no = int(field.name[-2:])
                            seal_timestring = re.search("__: (.+?)$", field.value).group(1).replace(' ','')
                            seal_time_left = await functions.parse_timestring_to_timedelta(seal_timestring.lower())
                            current_time = datetime.utcnow().replace(microsecond=0)
                            seal_time = current_time + seal_time_left
                            await settings_db.update_setting(f'a{area_no}_seal_time', seal_time)
                            updated_settings = True
                        except Exception as error:
                            if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                                await message.add_reaction(emojis.WARNING)
                            await errors.log_error(
                                f'Error when trying to read unseal time: {error}',
                                message
                            )
                            return
                if updated_settings: await message.add_reaction(emojis.NAVI)

        if not message.embeds:
            message_content = message.content
            # Training helper
            if '** is training in the' in message_content.lower() and not 'in the mine!' in message_content.lower():
                user_name = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    try:
                        user_name = re.search("^\*\*(.+?)\*\* ", message_content).group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in training helper message: {message_content}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in training helper message: {message_content}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.training_helper_enabled: return
                answer = await functions.get_training_answer(message_content.lower())
                await message.reply(answer)


# Initialization
def setup(bot):
    bot.add_cog(TrainingHelperCog(bot))