# helper_pets.py

import re

import discord
from discord.ext import commands

from cache import messages
from database import errors, users
from resources import emojis, exceptions, functions, settings, regex


class HelperPetsCog(commands.Cog):
    """Cog that contains the pets detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_field_name = message_field_value = message_author = ''
            if embed.fields:
                message_field_name = str(embed.fields[0].name)
                message_field_value = str(embed.fields[0].value)
                message_author = str(embed.author.name)

            # Pet catch
            search_strings_name = [
                'suddenly', #English
                'de repente', #Spanish, Portuguese
            ]
            search_strings_value = [
                'happiness', #English
                'felicidad', #Spanish, Portuguese
            ]
            if (any(search_string in message_field_name.lower() for search_string in search_strings_name)
                and any(search_string in message_field_value.lower() for search_string in search_strings_value)):

                async def design_pet_catch_field(feeds: int, pats: int, user_settings: users.User) -> str:
                    """Returns an embed field with the commands and the catch chance"""
                    hunger_remaining_min = hunger - (feeds * 22)
                    if hunger_remaining_min < 0: hunger_remaining_min = 0
                    hunger_remaining_max = hunger - (feeds * 18)
                    if hunger_remaining_max < 0: hunger_remaining_max = 0
                    happiness_remaining_min = happiness + (pats * 8)
                    if happiness_remaining_min < 0: happiness_remaining_min = 0
                    happiness_remaining_max = happiness + (pats * 12)
                    if happiness_remaining_max < 0: happiness_remaining_max = 0
                    difference_best = happiness_remaining_max - hunger_remaining_min
                    difference_worst = happiness_remaining_min - hunger_remaining_max
                    chance_min = 100 / 85 * difference_worst
                    chance_max = 100 / 85 * difference_best
                    if chance_min > 100: chance_min = 100
                    if chance_max > 100: chance_max = 100
                    if chance_min != chance_max:
                        chance = f'Catch chance: {chance_min:.2f} - {chance_max:.2f}%'
                    else:
                        chance = f'Catch chance: {chance_max:.2f}%'
                    commands = ''
                    for x in range(0,pats):
                        commands = f'{commands} pat'
                    for x in range(0,feeds):
                        commands = f'{commands} feed'
                    commands = commands.upper().strip()
                    hunger_emoji = emojis.PET_HUNGER_EASTER if 'bunny' in message_author else emojis.PET_HUNGER
                    actions = f'{emojis.PET_HAPPINESS} {pats} pats, {hunger_emoji} {feeds} feeds'
                    if pats + feeds < 6:
                        actions = f'{actions}, {emojis.PET_RANDOM} tame'
                    field_value = actions if user_settings.pet_helper_icon_mode else commands

                    return [field_value, chance]

                user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    search_patterns = [
                        r"APPROACHING \*\*(.+?)\*\*", #English
                        r"ACERCANDO A \*\*(.+?)\*\*", #Spanish
                        r"APROXIMANDO DE \*\*(.+?)\*\*", #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_field_name)
                    if not user_name_match:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, message_author)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                        user_name=user_name)
                        )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in pet catch message for pet helper.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.pet_helper_enabled: return
                search_patterns_happiness = [
                    r'happiness\**: (.+?)\n', #English
                    r'felicidade?\**: (.+?)\n', #Spanish, Portuguese
                ]
                search_patterns_hunger = [
                    r'hunger\**: (.+?)$', #English
                    r'hambre\**: (.+?)$', #Spanish
                    r'fome\**: (.+?)$', #Portuguese
                ]
                happiness_match = await functions.get_match_from_patterns(search_patterns_happiness,
                                                                            message_field_value.lower())
                if happiness_match:
                    happiness = int(happiness_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Happiness not found in pet catch message for pet helper.', message)
                    return
                hunger_match = await functions.get_match_from_patterns(search_patterns_hunger,
                                                                        message_field_value.lower())
                if hunger_match:
                    hunger = int(hunger_match.group(1))
                else:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Hunger not found in pet catch message for pet helper.', message)
                    return
                # Low risk
                feeds, hunger_rest = divmod(hunger, 18)
                if hunger_rest >= 9:
                    feeds += 1
                    hunger_rest = 0
                happiness_missing = (hunger_rest + 85) - happiness
                pats, happiness_rest = divmod(happiness_missing, 8)
                if happiness_rest > 0: pats += 1
                if feeds + pats > 6: pats = 6 - feeds
                command_amount_low_risk = feeds + pats
                commands_low_risk, chance_low_risk = await design_pet_catch_field(feeds, pats, user_settings)
                # High risk
                feeds, hunger_rest = divmod(hunger, 22)
                if hunger_rest >= 9:
                    feeds += 1
                    hunger_rest = 0
                happiness_missing = (hunger_rest + 85) - happiness
                pats, happiness_rest = divmod(happiness_missing, 12)
                if happiness_rest > 0: pats += 1
                if feeds + pats > 6: pats = 6 - feeds - 1
                if pats < 0: pats = 0
                command_amount_high_risk = feeds + pats
                if command_amount_high_risk == command_amount_low_risk: pats -= 1
                commands_high_risk, chance_high_risk = await design_pet_catch_field(feeds, pats, user_settings)
                high_skill_name = 'HIGHER CHANCE AT SKILL' if command_amount_low_risk < 6 else 'CHANCE AT SKILL'
                embed_low_risk = discord.Embed(
                    title = 'LOWEST RISK',
                    description = commands_low_risk,
                )
                embed_low_risk.set_footer(text=chance_low_risk)
                embed_high_risk = discord.Embed(
                    title = high_skill_name,
                    description = commands_high_risk,
                )
                embed_high_risk.set_footer(text=chance_high_risk)
                content = user.mention if not user_settings.dnd_mode_enabled else None
                await message.reply(content=content, embeds=[embed_low_risk, embed_high_risk])


# Initialization
def setup(bot):
    bot.add_cog(HelperPetsCog(bot))