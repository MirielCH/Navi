# dev.py
"""Internal dev commands"""

from datetime import datetime
import importlib
import os
import re
import sqlite3
import sys
from typing import List

import discord
from discord.commands import SlashCommandGroup, Option
from discord.ext import commands
from humanfriendly import format_timespan

from database import cooldowns
from resources import emojis, exceptions, functions, logs, settings, views


EVENT_REDUCTION_TYPES = [
    'Text commands',
    'Slash commands',
]

MSG_NOT_DEV = 'You are not allowed to use this command.'

class DevCog(commands.Cog):
    """Cog class containing internal dev commands"""
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    dev = SlashCommandGroup(
        "dev",
        "Development commands",
        guild_ids=settings.DEV_GUILDS,
        default_member_permissions=discord.Permissions(administrator=True)
    )

    # Commands
    @dev.command()
    async def reload(
        self,
        ctx: discord.ApplicationContext,
        modules: Option(str, 'Cogs or modules to reload'),
    ) -> None:
        """Reloads cogs or modules"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        modules = modules.split(' ')
        actions = []
        for module in modules:
            name_found = False
            cog_name = f'cogs.{module}' if not 'cogs.' in module else module
            try:
                cog_status = self.bot.reload_extension(cog_name)
            except:
                cog_status = 'Error'
            if cog_status is None:
                actions.append(f'+ Extension \'{cog_name}\' reloaded.')
                name_found = True
            if not name_found:
                for module_name in sys.modules.copy():
                    if module == module_name:
                        module = sys.modules.get(module_name)
                        if module is not None:
                            importlib.reload(module)
                            actions.append(f'+ Module \'{module_name}\' reloaded.')
                            name_found = True
            if not name_found:
                actions.append(f'- No loaded cog or module with the name \'{module}\' found.')

        message = ''
        for action in actions:
            message = f'{message}\n{action}'
        await ctx.respond(f'```diff\n{message}\n```')

    @dev.command(name='emoji-check')
    async def emoji_check(
        self,
        ctx: discord.ApplicationContext,
    ) -> None:
        """Checks the availabilty of all emojis in emojis.py"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        all_emojis = {}
        for attribute_name in dir(emojis):
            attribute_value = getattr(emojis, attribute_name)
            if isinstance(attribute_value, str):
                if attribute_value.startswith('<'):
                    all_emojis[attribute_name] = attribute_value
        missing_emojis = {}
        invalid_emojis = {}
        for attribute_name, emoji_string in all_emojis.items():
            emoji_id_match = re.search(r'<a?:.+:(\d+)>', emoji_string)
            if not emoji_id_match:
                invalid_emojis[attribute_name] = emoji_string
                continue
            emoji = self.bot.get_emoji(int(emoji_id_match.group(1)))
            if emoji is None:
                missing_emojis[attribute_name] = emoji_string
        if not missing_emojis and not invalid_emojis:
            description = '_All emojis in `emojis.py` are valid and available._'
        else:
            description = (
                '- _Invalid emojis have an error in their definition in `emojis.py`._\n'
                '- _Missing emojis are valid but not found on Discord. Upload them to a server Navi can see and set '
                'the correct IDs in `emojis.py`._\n'
            )
        if invalid_emojis:    
            description = f'{description}\n\n**Invalid emojis**'
            for attribute_name, emoji_string in invalid_emojis.items():
                description = f'{description}\n- {emoji_string} `{attribute_name}`'
        if missing_emojis:
            description = f'{description}\n\n**Missing emojis**'
            for attribute_name, emoji_string in missing_emojis.items():
                description = f'{description}\n- {emoji_string} `{attribute_name}`'
        if len(description) >= 4096:
            description = f'{description[:4080]}\n- ... too many errors, what are you even doing?'
        embed = discord.Embed(
            title = 'Emoji check',
            description = description,
        )
        await ctx.respond(embed=embed)


    @dev.command(name='event-reductions')
    async def dev_event_reductions(self, ctx: discord.ApplicationContext) -> None:
        """Change event reductions"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        all_cooldowns = list(await cooldowns.get_all_cooldowns())
        view = views.DevEventReductionsView(ctx, self.bot, all_cooldowns, embed_dev_event_reductions)
        embed = await embed_dev_event_reductions(all_cooldowns)
        interaction = await ctx.respond(embed=embed, view=view)
        view.interaction = interaction

    @dev.command(name='backup')
    async def dev_dump(self, ctx: discord.ApplicationContext) -> None:
        """Manually backups the database to navi_db_backup.db"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            f'This will back up the database to `navi_db_backup.db`. You can continue using Navi while doing this.\n'
            f'**If the target file exists, it will be overwritten!**\n\n'
            f'Proceed?',
            view=view,
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        elif view.value != 'confirm':
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Backup aborted.')
        else:    
            start_time = datetime.utcnow()
            interaction = await ctx.respond('Starting backup...')
            backup_db_file = os.path.join(settings.BOT_DIR, 'database/navi_db_backup.db')
            navi_backup_db = sqlite3.connect(backup_db_file)
            settings.NAVI_DB.backup(navi_backup_db)
            navi_backup_db.close()
            time_taken = datetime.utcnow() - start_time
            await functions.edit_interaction(interaction, content=f'Backup finished after {format_timespan(time_taken)}')

    @dev.command(name='post-message')
    async def post_message(
        self,
        ctx: discord.ApplicationContext,
        message_id: Option(str, 'Message ID of the message IN THIS CHANNEL with the content'),
        channel_id: Option(str, 'Channel ID of the channel where the message is sent to'),
        embed_title: Option(str, 'Title of the embed', max_length=256),
    ) -> None:
        """Sends the content of a message to a channel in an embed"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        await self.bot.wait_until_ready()
        try:
            message_id = int(message_id)
        except ValueError:
            await ctx.respond('The message ID is not a valid number.', ephemeral=True)
            return
        try:
            channel_id = int(channel_id)
        except ValueError:
            await ctx.respond('The channel ID is not a valid number.', ephemeral=True)
            return
        try:
            message = await ctx.channel.fetch_message(message_id)
        except:
            await ctx.respond(
                f'No message with that message ID found.\n'
                f'Note that the message needs to be in **this** channel!',
                ephemeral=True
            )
            return
        try:
            channel = await self.bot.fetch_channel(channel_id)
        except:
            await ctx.respond('No channel with that channel ID found.', ephemeral=True)
            return
        embed = discord.Embed(
            title = embed_title,
            description = message.content
        )
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.blurple, discord.ButtonStyle.grey])
        interaction = await ctx.respond(
            f'I will send the following embed to the channel `{channel.name}`. Proceed?',
            view=view,
            embed=embed
        )
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await ctx.followup.send(f'**{ctx.author.name}**, you didn\'t answer in time.')
        elif view.value == 'confirm':
            await channel.send(embed=embed)
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Message sent.')
        else:
            await functions.edit_interaction(interaction, view=None)
            await ctx.followup.send('Sending aborted.')

    @dev.command()
    async def support(self, ctx: discord.ApplicationContext):
        """Link to the dev support server"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        await ctx.respond(
            f'Got some issues or questions running Navi? Feel free to join the Navi dev support server:\n'
            f'https://discord.gg/Kz2Vz2K4gy'
        )

    @dev.command()
    async def shutdown(self, ctx: discord.ApplicationContext):
        """Shuts down the bot"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        view = views.ConfirmCancelView(ctx, styles=[discord.ButtonStyle.red, discord.ButtonStyle.grey])
        interaction = await ctx.respond(f'**{ctx.author.name}**, are you **SURE**?', view=view)
        view.interaction_message = interaction
        await view.wait()
        if view.value is None:
            await functions.edit_interaction(interaction, content=f'**{ctx.author.name}**, you didn\'t answer in time.',
                                             view=None)
        elif view.value == 'confirm':
            await functions.edit_interaction(interaction, content='Shutting down.', view=None)
            await self.bot.close()
        else:
            await functions.edit_interaction(interaction, content='Shutdown aborted.', view=None)

    @dev.command()
    async def cache(self, ctx: discord.ApplicationContext):
        """Shows cache size"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        from cache import messages
        cache_size = sys.getsizeof(messages._MESSAGE_CACHE)
        channel_count = len(messages._MESSAGE_CACHE)
        message_count = 0
        for channel_messages in messages._MESSAGE_CACHE.values():
            message_count += len(channel_messages)
            cache_size += sys.getsizeof(channel_messages)
            for message in channel_messages:
                cache_size += sys.getsizeof(message)
        await ctx.respond(
            f'Cache size: {cache_size / 1024:,.2f} KB\n'
            f'Channel count: {channel_count:,}\n'
            f'Message count: {message_count:,}\n'
        )

    @dev.command(name='server-list')
    async def server_list(self, ctx: discord.ApplicationContext):
        """Lists the servers the bot is in by name"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        description = ''
        guilds = sorted(self.bot.guilds, key=lambda guild: guild.name)
        for guild in guilds:
            if len(description) > 4000:
                description = f'{description}\n{emojis.BP} ... and more'
                break
            else:
                description = f'{description}\n{emojis.BP} {guild.name}'

        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = 'SERVER LIST',
            description = description.strip(),
        )
        await ctx.respond(embed=embed)

    @dev.command()
    async def consolidate(self, ctx: discord.ApplicationContext):
        """Miriel test command. Consolidates tracking records older than 28 days manually"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond(MSG_NOT_DEV, ephemeral=True)
            return
        await ctx.defer()
        from datetime import datetime
        import asyncio
        from humanfriendly import format_timespan
        from database import tracking, users
        start_time = datetime.utcnow().replace(microsecond=0)
        log_entry_count = 0
        try:
            old_log_entries = await tracking.get_old_log_entries(28)
        except exceptions.NoDataFoundError:
            await ctx.respond('Nothing to do.')
            return
        entries = {}
        for log_entry in old_log_entries:
            date_time = log_entry.date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            key = (log_entry.user_id, log_entry.guild_id, log_entry.command, date_time)
            amount = entries.get(key, 0)
            entries[key] = amount + 1
            log_entry_count += 1
        for key, amount in entries.items():
            user_id, guild_id, command, date_time = key
            summary_log_entry = await tracking.insert_log_summary(user_id, guild_id, command, date_time, amount)
            date_time_min = date_time.replace(hour=0, minute=0, second=0, microsecond=0)
            date_time_max = date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            await tracking.delete_log_entries(user_id, guild_id, command, date_time_min, date_time_max)
            await asyncio.sleep(0.01)
        cur = settings.NAVI_DB.cursor()
        cur.execute('VACUUM')
        end_time = datetime.utcnow().replace(microsecond=0)
        time_passed = end_time - start_time
        logs.logger.info(f'Consolidated {log_entry_count:,} log entries in {format_timespan(time_passed)} manually.')
        await ctx.respond(f'Consolidated {log_entry_count:,} log entries in {format_timespan(time_passed)}.')


def setup(bot):
    bot.add_cog(DevCog(bot))


# --- Embeds ---
async def embed_dev_event_reductions(all_cooldowns: List[cooldowns.Cooldown]) -> discord.Embed:
    """Event reductions embed"""
    reductions_slash = reductions_text = ''
    for cooldown in all_cooldowns:
        if cooldown.event_reduction_slash > 0:
            event_reduction_slash = f'**`{cooldown.event_reduction_slash}`**%'
        else:
            event_reduction_slash = f'`{cooldown.event_reduction_slash}`%'
        reductions_slash = f'{reductions_slash}\n{emojis.BP} {cooldown.activity}: {event_reduction_slash}'
        if cooldown.event_reduction_mention > 0:
            event_reduction_text = f'**`{cooldown.event_reduction_mention}`**%'
        else:
            event_reduction_text = f'`{cooldown.event_reduction_mention}`%'
        reductions_text = f'{reductions_text}\n{emojis.BP} {cooldown.activity}: {event_reduction_text}'
    embed = discord.Embed(
        color = settings.EMBED_COLOR,
        title = 'EVENT REDUCTION SETTINGS',
    )
    embed.add_field(name='SLASH COMMANDS', value=reductions_slash, inline=False)
    embed.add_field(name='TEXT & MENTION COMMANDS', value=reductions_text, inline=False)
    return embed