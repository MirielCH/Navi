# event_pings.py

import discord
from discord.ext import bridge, commands

from database import guilds
from resources import functions, settings


class EventPingsCog(commands.Cog):
    """Cog that contains the event ping detection commands"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_after.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message_before.pinned != message_after.pinned: return
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
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
            field_0_name = field_0_value = ''
            if embed.fields:
                field_0_name = embed.fields[0].name
                field_0_value = embed.fields[0].value

            search_strings_name = {
                'type `join`': 'arena', #Arena, English
                'para entrar a la arena': 'arena', #Arena, Spanish
                'para entrar na arena': 'arena', #Arena, Portuguese
                'raining coins': 'coin', #Coin rain, English
                'están lloviendo coins': 'coin', #Coin rain, Spanish
                'está chuvendo coins': 'coin', #Coin rain, Portuguese
                'megalodon has spawned': 'fish', #Megalodon, English
                'un megalodón spawneó': 'fish', #Megalodon, Spanish
                'um megalodon spawnou': 'fish', #Megalodon, Portuguese
                'legendary boss': 'legendary_boss', #Legendary boss, English
                'boss legendario': 'legendary_boss', #Legendary boss, Spanish (assumption)
                'boss lendário': 'legendary_boss', #Legendary boss, Portuguese (assumption)
                'epic tree': 'log', #Epic tree, English
                'árbol épico': 'log', #Epic tree, Spanish
                'árvore épica': 'log', #Epic tree, Portuguese
                'lootbox summoning': 'lootbox', #Lootbox summoning, English
                'invocación de lootbox': 'lootbox', #Lootbox summoning, Spanish
                'convocação da lootbox': 'lootbox', #Lootbox summoning, Portuguese
                'type `fight`': 'miniboss', #Miniboss, English
                'para ayudar y boostear': 'miniboss', #Miniboss, Spanish
                'para ajudar e boostar': 'miniboss', #Miniboss, Portuguese
                'golden wolf': 'rare_hunt_monster', #Rare hunt monster, mob 1
                'ruby zombie': 'rare_hunt_monster', #Rare hunt monster, mob 2
                'diamond unicorn': 'rare_hunt_monster', #Rare hunt monster, mob 3
                'emerald mermaid': 'rare_hunt_monster', #Rare hunt monster, mob 4
                'sapphire killer robot': 'rare_hunt_monster', #Rare hunt monster, mob 5
                
            }
            search_strings_value = (
                'arena cookies', #Arena, English & Spanish
                'cookies de arena', #Arena, Portuguese
                'collect some coins', #Coin rain, English
                'recolectar algunos coins', #Coin rain, Spanish
                'coletar algumos coins', #Coin rain, Portuguese
                'collect some fish', #Megalodon, English
                'recolectar algunos normie fish', #Megalodon, Spanish
                'coletar alguns normie fish', #Megalodon, Portuguese
                'collect some wooden logs', #Epic tree, English
                'recolectar algunos wooden logs', #Epic tree, Spanish
                'coletar alguns wooden logs', #Epic tree, Portuguese
                'join the summoning', #Lootbox summoning, English
                'unirte a la invocación', #Lootbox summoning, Spanish
                'participar da convocação', #Lootbox summoning, Portuguese
                'time to fight', #Legendary boss
                'epicrpgsword', #Miniboss
                'get that pickaxe', #Rare hunt monster
            )
            if (any(search_string in field_0_name.lower() for search_string in search_strings_name.keys())
                and any(search_string in field_0_value.lower() for search_string in search_strings_value)):
                for string, event_name in search_strings_name.items():
                    if string in field_0_name.lower():
                        event = event_name
                        break
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                event_settings = getattr(guild_settings, f'event_{event}', None)
                if event_settings is None: return
                if not event_settings.enabled: return
                allowed_mentions = discord.AllowedMentions(everyone=True, roles=True)
                await message.reply(event_settings.message, allowed_mentions=allowed_mentions)


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(EventPingsCog(bot))