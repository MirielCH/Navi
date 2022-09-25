# dev.py
"""Internal dev commands"""

import importlib
import sys

import discord
from discord.commands import SlashCommandGroup, Option
from discord.ext import commands

from database import cooldowns
from resources import emojis, exceptions, functions, settings, strings, views


EVENT_REDUCTION_TYPES = [
    'Mention',
    'Slash',
]


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

    test = SlashCommandGroup(
        "test",
        "Test commands",
        guild_ids=settings.DEV_GUILDS,
        default_member_permissions=discord.Permissions(administrator=True)
    )

    # Commands
    @dev.command()
    @commands.is_owner()
    async def reload(
        self,
        ctx: discord.ApplicationContext,
        modules: Option(str, 'Cogs or modules to reload'),
    ) -> None:
        """Reloads cogs or modules"""
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

    @dev.command(name='event-reduction')
    async def event_reduction(
        self,
        ctx: discord.ApplicationContext,
        command_type: Option(str, 'Reduction type', choices=EVENT_REDUCTION_TYPES),
        activities: Option(str, 'Activities to update', default=''),
        event_reduction: Option(float, 'Event reduction in percent', min_value=0, max_value=99, default=None),
    ) -> None:
        """Changes the event reduction for activities"""
        if ctx.author.id not in settings.DEV_IDS:
            await ctx.respond('Looks like you\'re not allowed to use this command, sorry.', ephemeral=True)
            return
        activities = activities.split()
        if not activities and event_reduction is None:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = f'Current event reductions for {command_type.lower()} commands:'
            for cooldown in all_cooldowns:
                event_reduction = getattr(cooldown, f'event_reduction_{command_type.lower()}')
                actual_cooldown = cooldown.actual_cooldown_mention() if command_type == 'Mention' else cooldown.actual_cooldown_slash()
                cooldown_message = (
                    f'{emojis.BP} {cooldown.activity}: {event_reduction}% '
                    f'({actual_cooldown:,}s)'
                )
                answer = f'{answer}\n**{cooldown_message}**' if event_reduction > 0 else f'{answer}\n{cooldown_message}'
            await ctx.respond(answer)
            return
        if not activities or event_reduction is None:
            await ctx.respond(
                f'You need to set both activity _and_ event_reduction. If you want to see the current reductions, '
                f'leave both options empty.',
                ephemeral=True
            )
            return
        for index, activity in enumerate(activities):
            if activity in strings.ACTIVITIES_ALIASES: activities[index] = strings.ACTIVITIES_ALIASES[activity]

        if 'all' in activities:
            activities += strings.ACTIVITIES_WITH_COOLDOWN
            activities.remove('all')
        updated_activities = []
        ignored_activities = []
        for activity in activities:
            if activity in strings.ACTIVITIES_WITH_COOLDOWN:
                updated_activities.append(activity)
            else:
                ignored_activities.append(activity)
        all_cooldowns = await cooldowns.get_all_cooldowns()
        answer = ''
        if updated_activities:
            answer = f'Updated event reductions for {command_type.lower()} commands as follows:'
            for activity in updated_activities:
                cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
                kwarg = {
                    f'event_reduction_{command_type.lower()}': event_reduction,
                }
                await cooldown.update(**kwarg)
                answer = f'{answer}\n{emojis.BP} `{cooldown.activity}` to **{event_reduction}%**'
        if ignored_activities:
            answer = f'{answer}\n\nDidn\'t find the following activities:'
            for ignored_activity in ignored_activities:
                answer = f'{answer}\n{emojis.BP} `{ignored_activity}`'
        await ctx.respond(answer)

    @dev.command(name='base-cooldown')
    @commands.is_owner()
    async def base_cooldown(
        self,
        ctx: discord.ApplicationContext,
        activity: Option(str, 'Activity to update', choices=strings.ACTIVITIES_WITH_COOLDOWN, default=None),
        base_cooldown: Option(int, 'Base cooldown in seconds', min_value=1, max_value=604_200, default=None),
    ) -> None:
        """Changes the base cooldown for activities"""
        if activity is None and base_cooldown is None:
            all_cooldowns = await cooldowns.get_all_cooldowns()
            answer = 'Current base cooldowns:'
            for cooldown in all_cooldowns:
                answer = f'{answer}\n{emojis.BP} {cooldown.activity}: {cooldown.base_cooldown}s'
            await ctx.respond(answer)
            return
        if activity is None or base_cooldown is None:
            await ctx.resond(
                'You need to set both options. If you want to see the current cooldowns, leave both options empty.',
                ephemeral=True
            )
            return
        cooldown: cooldowns.Cooldown = await cooldowns.get_cooldown(activity)
        await cooldown.update(cooldown=base_cooldown)
        if cooldown.base_cooldown == base_cooldown:
            answer =  f'Changed base cooldown for activity `{cooldown.activity}` to **{cooldown.base_cooldown}s**.'
        await ctx.respond(answer)

    @dev.command(name='post-message')
    @commands.is_owner()
    async def post_message(
        self,
        ctx: discord.ApplicationContext,
        message_id: Option(str, 'Message ID of the message IN THIS CHANNEL with the content'),
        channel_id: Option(str, 'Channel ID of the channel where the message is sent to'),
        embed_title: Option(str, 'Title of the embed', max_length=256),
    ) -> None:
        """Sends the content of a message to a channel in an embed"""
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
    @commands.is_owner()
    async def migrate(self, ctx: discord.ApplicationContext):
        """Migrate user database"""
        await ctx.defer()
        from database import reminders, users
        all_users = await users.get_all_users()
        user_count = 0
        for user in all_users:
            if user.ping_after_message:
                alert_adventure_message = f'{user.alert_adventure.message} {{name}}'
                alert_arena_message = f'{user.alert_arena.message} {{name}}'
                alert_big_arena_message = f'{user.alert_big_arena.message} {{name}}'
                alert_daily_message = f'{user.alert_daily.message} {{name}}'
                alert_duel_message = f'{user.alert_duel.message} {{name}}'
                alert_dungeon_miniboss_message = f'{user.alert_dungeon_miniboss.message} {{name}}'
                alert_farm_message = f'{user.alert_farm.message} {{name}}'
                alert_guild_message = f'{user.alert_guild.message} {{name}}'
                alert_horse_breed_message = f'{user.alert_horse_breed.message} {{name}}'
                alert_horse_race_message = f'{user.alert_horse_race.message} {{name}}'
                alert_hunt_message = f'{user.alert_hunt.message} {{name}}'
                alert_lootbox_message = f'{user.alert_lootbox.message} {{name}}'
                alert_lottery_message = f'{user.alert_lottery.message} {{name}}'
                alert_not_so_mini_boss_message = f'{user.alert_not_so_mini_boss.message} {{name}}'
                alert_partner_message = f'{user.alert_partner.message.replace("{user}", "{partner}")} {{name}}'
                alert_pet_tournament_message = f'{user.alert_pet_tournament.message} {{name}}'
                alert_pets_message = f'{user.alert_pets.message} {{name}}'
                alert_quest_message = f'{user.alert_quest.message} {{name}}'
                alert_training_message = f'{user.alert_training.message} {{name}}'
                alert_vote_message = f'{user.alert_vote.message} {{name}}'
                alert_weekly_message = f'{user.alert_weekly.message} {{name}}'
                alert_work_message = f'{user.alert_work.message} {{name}}'
            else:
                alert_adventure_message = f'{{name}} {user.alert_adventure.message}'
                alert_arena_message = f'{{name}} {user.alert_arena.message}'
                alert_big_arena_message = f'{{name}} {user.alert_big_arena.message}'
                alert_daily_message = f'{{name}} {user.alert_daily.message}'
                alert_duel_message = f'{{name}} {user.alert_duel.message}'
                alert_dungeon_miniboss_message = f'{{name}} {user.alert_dungeon_miniboss.message}'
                alert_farm_message = f'{{name}} {user.alert_farm.message}'
                alert_guild_message = f'{{name}} {user.alert_guild.message}'
                alert_horse_breed_message = f'{{name}} {user.alert_horse_breed.message}'
                alert_horse_race_message = f'{{name}} {user.alert_horse_race.message}'
                alert_hunt_message = f'{{name}} {user.alert_hunt.message}'
                alert_lootbox_message = f'{{name}} {user.alert_lootbox.message}'
                alert_lottery_message = f'{{name}} {user.alert_lottery.message}'
                alert_not_so_mini_boss_message = f'{{name}} {user.alert_not_so_mini_boss.message}'
                alert_partner_message = f'{{name}} {user.alert_partner.message.replace("{user}", "{partner}")}'
                alert_pet_tournament_message = f'{{name}} {user.alert_pet_tournament.message}'
                alert_pets_message = f'{{name}} {user.alert_pets.message}'
                alert_quest_message = f'{{name}} {user.alert_quest.message}'
                alert_training_message = f'{{name}} {user.alert_training.message}'
                alert_vote_message = f'{{name}} {user.alert_vote.message}'
                alert_weekly_message = f'{{name}} {user.alert_weekly.message}'
                alert_work_message = f'{{name}} {user.alert_work.message}'
            await user.update(
                alert_adventure_message = alert_adventure_message,
                alert_arena_message = alert_arena_message,
                alert_big_arena_message = alert_big_arena_message,
                alert_daily_message = alert_daily_message,
                alert_duel_message = alert_duel_message,
                alert_dungeon_miniboss_message = alert_dungeon_miniboss_message,
                alert_farm_message = alert_farm_message,
                alert_guild_message = alert_guild_message,
                alert_horse_breed_message = alert_horse_breed_message,
                alert_horse_race_message = alert_horse_race_message,
                alert_hunt_message = alert_hunt_message,
                alert_lootbox_message = alert_lootbox_message,
                alert_lottery_message = alert_lottery_message,
                alert_not_so_mini_boss_message = alert_not_so_mini_boss_message,
                alert_partner_message = alert_partner_message,
                alert_pet_tournament_message = alert_pet_tournament_message,
                alert_pets_message = alert_pets_message,
                alert_quest_message = alert_quest_message,
                alert_training_message = alert_training_message,
                alert_vote_message = alert_vote_message,
                alert_weekly_message = alert_weekly_message,
                alert_work_message = alert_work_message
            )
            user_count += 1
            try:
                all_reminders = await reminders.get_active_user_reminders(user.user_id)
            except exceptions.NoDataFoundError:
                continue
            for reminder in all_reminders:
                if user.ping_after_message:
                    await reminder.update(message=f'{reminder.message} {{name}}')
                else:
                    await reminder.update(message=f'{{name}} {reminder.message}')
        await ctx.respond(f'Migrated {user_count} users.')


    @dev.command()
    @commands.is_owner()
    async def shutdown(self, ctx: discord.ApplicationContext):
        """Shuts down the bot"""
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


def setup(bot):
    bot.add_cog(DevCog(bot))