# pet-helper.py

import re

import discord
from discord.ext import commands

from database import errors, users
from resources import emojis, exceptions, functions, settings


class PetHelperCog(commands.Cog):
    """Cog that contains the pets detection commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id != settings.EPIC_RPG_ID: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            message_field_name = message_field_value = message_author = ''
            if embed.fields:
                message_field_name = str(embed.fields[0].name)
                message_field_value = str(embed.fields[0].value)
                message_author = str(embed.author.name)

            # Pet catch
            if ('happiness' in message_field_value.lower() and 'hunger' in message_field_value.lower()
                and 'suddenly' in message_field_name.lower()):

                async def design_pet_catch_field(feeds: int, pats: int, slash: bool) -> str:
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
                        chance = f'_Catch chance: {chance_min:.2f} - {chance_max:.2f}%_'
                    else:
                        chance = f'_Catch chance: {chance_max:.2f}%_'
                    commands = ''
                    for x in range(0,feeds):
                        commands = f'{commands} feed'
                    for x in range(0,pats):
                        commands = f'{commands} pat'
                    commands = f'`{commands.upper().strip()}`'
                    hunger_emoji = emojis.PET_HUNGER_EASTER if 'bunny' in message_author else emojis.PET_HUNGER
                    actions = f'{emojis.PET_HAPPINESS} {pats} pats, {hunger_emoji} {feeds} feeds'
                    if pats + feeds < 6:
                        actions = f'{actions}, {emojis.PET_RANDOM} tame'
                    field_value = actions if slash else commands
                    field_value = f'{field_value}\n{chance}'

                    return field_value

                user_name = None
                user = await functions.get_interaction_user(message)
                slash_command = True if user is not None else False
                if user is None:
                    try:
                        user_name_search = re.search("APPROACHING \*\*(.+?)\*\*", message_field_name)
                        if user_name_search is None:
                            user_name_search = re.search("^(.+?)'s bunny", message_author)
                        user_name = user_name_search.group(1)
                        user_name = await functions.encode_text(user_name)
                    except Exception as error:
                        if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                            await message.add_reaction(emojis.WARNING)
                        await errors.log_error(
                            f'User not found in pet catch message for pet helper: {message.embeds[0].fields}',
                            message
                        )
                        return
                    user = await functions.get_guild_member_by_name(message.guild, user_name)
                if user is None:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'User not found in pet catch message for pet helper: {message.embeds[0].fields}',
                        message
                    )
                    return
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.pet_helper_enabled: return
                try:
                    happiness_search = re.search("Happiness\*\*: (.+?)\\n", message_field_value)
                    if happiness_search is None:
                        happiness_search = re.search("Happiness: (.+?)\\n", message_field_value)
                    happiness = happiness_search.group(1)
                    happiness = int(happiness)
                    hunger_search = re.search("Hunger\*\*: (.+?)$", message_field_value)
                    if hunger_search is None:
                        hunger_search = re.search("Hunger: (.+?)$", message_field_value)
                    hunger = hunger_search.group(1)
                    hunger = int(hunger)
                except Exception as error:
                    if settings.DEBUG_MODE or message.guild.id in settings.DEV_GUILDS:
                        await message.add_reaction(emojis.WARNING)
                    await errors.log_error(
                        f'Happiness or hunger not found in pet catch message for pet helper: {message.embeds[0].fields}',
                        message
                    )
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
                field_low_risk = await design_pet_catch_field(feeds, pats, slash_command)
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
                field_high_risk = await design_pet_catch_field(feeds, pats, slash_command)
                embed = discord.Embed()
                high_skill_name = 'HIGHER CHANCE AT SKILL' if command_amount_low_risk < 6 else 'CHANCE AT SKILL'
                embed.add_field(name='LOWEST RISK', value=field_low_risk, inline=False)
                embed.add_field(name=high_skill_name, value=field_high_risk, inline=False)
                await message.reply(embed=embed)


# Initialization
def setup(bot):
    bot.add_cog(PetHelperCog(bot))