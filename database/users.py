# users.py
"""Provides access to the table "users" in the database"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil
import sqlite3
from typing import Any, NamedTuple, Tuple

from discord import utils

from database import alts as alts_db
from database import errors, reminders
from resources import exceptions, settings, strings


# Containers
class UserAlert(NamedTuple):
    """Object that summarizes all user settings for a specific alert"""
    enabled: bool
    message: str
    multiplier: float
    visible: bool

class UserInventory(NamedTuple):
    """Object that summarizes all tracked inventory items for a user"""
    bread: int
    carrot: int
    potato: int
    present_eternal: int
    ruby: int
    seed_bread: int
    seed_carrot: int
    seed_potato: int

@dataclass()
class User():
    """Object that represents a record from table "user"."""
    alert_advent: UserAlert
    alert_adventure: UserAlert
    alert_arena: UserAlert
    alert_big_arena: UserAlert
    alert_boo: UserAlert
    alert_boosts: UserAlert
    alert_card_hand: UserAlert
    alert_cel_dailyquest: UserAlert
    alert_cel_multiply: UserAlert
    alert_cel_sacrifice: UserAlert
    alert_chimney: UserAlert
    alert_daily: UserAlert
    alert_duel: UserAlert
    alert_dungeon_miniboss: UserAlert
    alert_epic: UserAlert
    alert_epic_shop: UserAlert
    alert_eternal_present: UserAlert
    alert_eternity_sealing: UserAlert
    alert_farm: UserAlert
    alert_guild: UserAlert
    alert_horse_breed: UserAlert
    alert_horse_race: UserAlert
    alert_hunt: UserAlert
    alert_hunt_partner: UserAlert
    alert_lootbox: UserAlert
    alert_lottery: UserAlert
    alert_love_share: UserAlert
    alert_maintenance: UserAlert
    alert_megarace: UserAlert
    alert_minirace: UserAlert
    alert_not_so_mini_boss: UserAlert
    alert_partner: UserAlert
    alert_pet_tournament: UserAlert
    alert_pets: UserAlert
    alert_quest: UserAlert
    alert_training: UserAlert
    alert_vote: UserAlert
    alert_weekly: UserAlert
    alert_work: UserAlert
    alts: Tuple[int]
    ascended: bool
    area_20_cooldowns_enabled: bool
    auto_flex_enabled: bool
    auto_flex_ping_enabled: bool
    auto_flex_tip_read: bool
    auto_healing_active: bool
    auto_ready_enabled: bool
    bot_enabled: bool
    chocolate_box_unlocked: bool
    clan_name: str
    christmas_area_enabled: bool
    cmd_cd_visible: bool
    cmd_inventory_visible: bool
    cmd_ready_visible: bool
    cmd_slashboard_visible: bool
    context_helper_enabled: bool
    current_area: int
    dnd_mode_enabled: bool
    eternal_boosts_tier: int
    farm_helper_mode: int
    guild_quest_prompt_active: bool
    halloween_helper_enabled: bool
    hardmode_mode_enabled: bool
    heal_warning_enabled: bool
    hunt_end_time: datetime
    hunt_reminders_combined: bool
    inventory: UserInventory
    last_adventure_mode: str
    last_farm_seed: str
    last_hunt_mode: str
    last_lootbox: str
    last_quest_command: str
    last_training_command: str
    last_tt: datetime
    last_work_command: str
    megarace_helper_enabled: bool
    multiplier_management_enabled: bool
    partner_alert_threshold: int
    partner_channel_id: int
    partner_chocolate_box_unlocked: bool
    partner_donor_tier: int
    partner_hunt_end_time: datetime
    partner_id: int
    partner_name: str
    partner_pocket_watch_multiplier: float
    pet_helper_enabled: bool
    pet_helper_icon_mode: bool
    pet_tip_read: bool
    ping_after_message: bool
    portals_as_embed: bool
    portals_spacing_enabled: bool
    potion_dragon_breath_active: bool
    potion_flask_active: bool
    reactions_enabled: bool
    ready_after_all_commands: bool
    ready_as_embed: bool
    ready_channel_arena: int
    ready_channel_duel: int
    ready_channel_dungeon: int
    ready_channel_horse: int
    ready_embed_color: str
    ready_eternity_visible: bool
    ready_pets_claim_active: bool
    ready_pets_claim_after_every_pet: bool
    ready_other_on_top: bool
    ready_ping_user: bool
    ready_trade_daily_completed_visible: bool
    ready_trade_daily_visible: bool
    ready_up_next_as_timestamp: bool
    ready_up_next_show_hidden_reminders: bool
    ready_up_next_visible: bool
    reminder_channel_id: int
    round_card_active: bool
    ruby_counter_button_mode: bool
    ruby_counter_enabled: bool
    slash_mentions_enabled: bool
    time_potion_warning_enabled: bool
    time_travel_count: int
    top_hat_unlocked: bool
    tracking_enabled: bool
    trade_daily_done: int
    trade_daily_total: int
    training_helper_button_mode: bool
    training_helper_enabled: bool
    user_donor_tier: int
    user_id: int
    user_pocket_watch_multiplier: float

    def __str__(self) -> str:
        """Returns all attributes of the User object separated by newlines."""
        response: str = ''
        attribute_name: str
        for attribute_name in dir(self):
            if attribute_name.startswith('__'): continue
            attribute_value = getattr(self, attribute_name)
            if 'method' in str(attribute_value): continue
            response = f'{response}\n{attribute_name}: {attribute_value}'
        return response.strip()
            
    async def refresh(self) -> None:
        """Refreshes user data from the database."""
        new_settings: User = await get_user(self.user_id)
        self.alert_advent = new_settings.alert_advent
        self.alert_adventure = new_settings.alert_adventure
        self.alert_arena = new_settings.alert_arena
        self.alert_boo = new_settings.alert_boo
        self.alert_boosts = new_settings.alert_boosts
        self.alert_card_hand = new_settings.alert_card_hand
        self.alert_cel_dailyquest = new_settings.alert_cel_dailyquest
        self.alert_cel_multiply = new_settings.alert_cel_multiply
        self.alert_cel_sacrifice = new_settings.alert_cel_sacrifice
        self.alert_chimney = new_settings.alert_chimney
        self.alert_big_arena = new_settings.alert_big_arena
        self.alert_daily = new_settings.alert_daily
        self.alert_duel = new_settings.alert_duel
        self.alert_dungeon_miniboss = new_settings.alert_dungeon_miniboss
        self.alert_epic = new_settings.alert_epic
        self.alert_epic_shop = new_settings.alert_epic_shop
        self.alert_eternal_present = new_settings.alert_eternal_present
        self.alert_eternity_sealing = new_settings.alert_eternity_sealing
        self.alert_farm = new_settings.alert_farm
        self.alert_guild = new_settings.alert_guild
        self.alert_horse_breed = new_settings.alert_horse_breed
        self.alert_horse_race = new_settings.alert_horse_race
        self.alert_hunt = new_settings.alert_hunt
        self.alert_hunt_partner = new_settings.alert_hunt_partner
        self.alert_lootbox = new_settings.alert_lootbox
        self.alert_lottery = new_settings.alert_lottery
        self.alert_love_share = new_settings.alert_love_share
        self.alert_maintenance = new_settings.alert_maintenance
        self.alert_megarace = new_settings.alert_megarace
        self.alert_minirace = new_settings.alert_minirace
        self.alert_not_so_mini_boss = new_settings.alert_not_so_mini_boss
        self.alert_partner = new_settings.alert_partner
        self.alert_pet_tournament = new_settings.alert_pet_tournament
        self.alert_pets = new_settings.alert_pets
        self.alert_quest = new_settings.alert_quest
        self.alert_training = new_settings.alert_training
        self.alert_vote = new_settings.alert_vote
        self.alert_weekly = new_settings.alert_weekly
        self.alert_work = new_settings.alert_work
        self.alts = new_settings.alts
        self.ascended = new_settings.ascended
        self.area_20_cooldowns_enabled = new_settings.area_20_cooldowns_enabled
        self.auto_flex_enabled = new_settings.auto_flex_enabled
        self.auto_flex_ping_enabled = new_settings.auto_flex_ping_enabled
        self.auto_flex_tip_read = new_settings.auto_flex_tip_read
        self.auto_healing_active = new_settings.auto_healing_active
        self.auto_ready_enabled = new_settings.auto_ready_enabled
        self.bot_enabled = new_settings.bot_enabled
        self.chocolate_box_unlocked = new_settings.chocolate_box_unlocked
        self.clan_name = new_settings.clan_name
        self.christmas_area_enabled = new_settings.christmas_area_enabled
        self.cmd_cd_visible = new_settings.cmd_cd_visible
        self.cmd_inventory_visible = new_settings.cmd_inventory_visible
        self.cmd_ready_visible = new_settings.cmd_ready_visible
        self.cmd_slashboard_visible = new_settings.cmd_slashboard_visible
        self.context_helper_enabled = new_settings.context_helper_enabled
        self.current_area = new_settings.current_area
        self.dnd_mode_enabled = new_settings.dnd_mode_enabled
        self.eternal_boosts_tier = new_settings.eternal_boosts_tier
        self.farm_helper_mode = new_settings.farm_helper_mode
        self.guild_quest_prompt_active = new_settings.guild_quest_prompt_active
        self.halloween_helper_enabled = new_settings.halloween_helper_enabled
        self.hardmode_mode_enabled = new_settings.hardmode_mode_enabled
        self.heal_warning_enabled = new_settings.heal_warning_enabled
        self.hunt_end_time = new_settings.hunt_end_time
        self.hunt_reminders_combined = new_settings.hunt_reminders_combined
        self.inventory = new_settings.inventory
        self.last_adventure_mode = new_settings.last_adventure_mode
        self.last_farm_seed = new_settings.last_farm_seed
        self.last_hunt_mode = new_settings.last_hunt_mode
        self.last_lootbox = new_settings.last_lootbox
        self.last_quest_command = new_settings.last_quest_command
        self.last_training_command = new_settings.last_training_command
        self.last_tt = new_settings.last_tt
        self.last_work_command = new_settings.last_work_command
        self.megarace_helper_enabled = new_settings.megarace_helper_enabled
        self.multiplier_management_enabled = new_settings.multiplier_management_enabled
        self.partner_alert_threshold = new_settings.partner_alert_threshold
        self.partner_channel_id = new_settings.partner_channel_id
        self.partner_chocolate_box_unlocked = new_settings.partner_chocolate_box_unlocked
        self.partner_donor_tier = new_settings.partner_donor_tier
        self.partner_hunt_end_time = new_settings.partner_hunt_end_time
        self.partner_id = new_settings.partner_id
        self.partner_name = new_settings.partner_name
        self.partner_pocket_watch_multiplier = new_settings.partner_pocket_watch_multiplier
        self.pet_helper_enabled = new_settings.pet_helper_enabled
        self.pet_helper_icon_mode = new_settings.pet_helper_icon_mode
        self.pet_tip_read = new_settings.pet_tip_read
        self.ping_after_message = new_settings.ping_after_message
        self.portals_as_embed = new_settings.portals_as_embed
        self.portals_spacing_enabled = new_settings.portals_spacing_enabled
        self.potion_dragon_breath_active = new_settings.potion_dragon_breath_active
        self.potion_flask_active = new_settings.potion_flask_active
        self.reactions_enabled = new_settings.reactions_enabled
        self.ready_after_all_commands = new_settings.ready_after_all_commands
        self.ready_as_embed = new_settings.ready_as_embed
        self.ready_channel_arena = new_settings.ready_channel_arena
        self.ready_channel_duel = new_settings.ready_channel_duel
        self.ready_channel_dungeon = new_settings.ready_channel_dungeon
        self.ready_channel_horse = new_settings.ready_channel_horse
        self.ready_embed_color = new_settings.ready_embed_color
        self.ready_eternity_visible = new_settings.ready_eternity_visible
        self.ready_pets_claim_active = new_settings.ready_pets_claim_active
        self.ready_pets_claim_after_every_pet = new_settings.ready_pets_claim_after_every_pet
        self.ready_other_on_top = new_settings.ready_other_on_top
        self.ready_ping_user = new_settings.ready_ping_user
        self.ready_trade_daily_completed_visible = new_settings.ready_trade_daily_completed_visible
        self.ready_trade_daily_visible = new_settings.ready_trade_daily_visible
        self.ready_up_next_as_timestamp = new_settings.ready_up_next_as_timestamp
        self.ready_up_next_show_hidden_reminders = new_settings.ready_up_next_show_hidden_reminders
        self.ready_up_next_visible = new_settings.ready_up_next_visible
        self.reminder_channel_id = new_settings.reminder_channel_id
        self.round_card_active = new_settings.round_card_active
        self.ruby_counter_button_mode = new_settings.ruby_counter_button_mode
        self.ruby_counter_enabled = new_settings.ruby_counter_enabled
        self.slash_mentions_enabled = new_settings.slash_mentions_enabled
        self.time_potion_warning_enabled = new_settings.time_potion_warning_enabled
        self.time_travel_count = new_settings.time_travel_count
        self.top_hat_unlocked = new_settings.top_hat_unlocked
        self.tracking_enabled = new_settings.tracking_enabled
        self.trade_daily_done = new_settings.trade_daily_done
        self.trade_daily_total = new_settings.trade_daily_total
        self.training_helper_button_mode = new_settings.training_helper_button_mode
        self.training_helper_enabled = new_settings.training_helper_enabled
        self.user_donor_tier = new_settings.user_donor_tier
        self.user_pocket_watch_multiplier = new_settings.user_pocket_watch_multiplier

    async def add_alt(self, alt_id: int) -> None:
        """Adds an alt to the database. Also calls refresh().

        Arguments
        ---------
        alt_id: int
        """
        await alts_db.insert_alt(self.user_id, alt_id)
        await self.refresh()
        
    async def remove_alt(self, alt_id: int) -> None:
        """Deletes an alt in the database. Also calls refresh().

        Arguments
        ---------
        alt_id: int
        """
        await alts_db.delete_alt(self.user_id, alt_id)
        await self.refresh()
        
    async def update(self, **kwargs) -> None:
        """Updates the user record in the database. Also calls refresh().
        If user_donor_tier is updated and a partner is set, the partner's partner_donor_tier is updated as well.

        Arguments
        ---------
        kwargs (column=value):
            alert_advent_enabled: bool
            alert_advent_message: str
            alert_advent_visible: bool
            alert_adventure_enabled: bool
            alert_adventure_message: str
            alert_adventure_multiplier: float
            alert_adventure_visible: bool
            alert_arena_enabled: bool
            alert_arena_message: str
            alert_arena_visible: bool
            alert_big_arena_enabled: bool
            alert_big_arena_message: str
            alert_big_arena_visible: bool
            alert_boo_enabled: bool
            alert_boo_message: str
            alert_boo_multiplier: float
            alert_boo_visible: bool
            alert_boosts_enabled: bool
            alert_boosts_message: str
            alert_boosts_visible: bool
            alert_card_hand_enabled: bool
            alert_card_hand_message: str
            alert_card_hand_multiplier: float
            alert_card_hand_visible: bool
            alert_cel_dailyquest_enabled: bool
            alert_cel_dailyquest_message: str
            alert_cel_dailyquest_visible: bool
            alert_cel_multiply_enabled: bool
            alert_cel_multiply_message: str
            alert_cel_multiply_visible: bool
            alert_cel_sacrifice_enabled: bool
            alert_cel_sacrifice_message: str
            alert_cel_sacrifice_visible: bool
            alert_chimney_enabled: bool
            alert_chimney_message: str
            alert_chimney_multiplier: float
            alert_chimney_visible: bool
            alert_daily_enabled: bool
            alert_daily_message: str
            alert_daily_multiplier: float
            alert_daily_visible: bool
            alert_duel_enabled: bool
            alert_duel_message: str
            alert_duel_multiplier: float
            alert_duel_visible: bool
            alert_dungeon_miniboss_enabled: bool
            alert_dungeon_miniboss_message: str
            alert_dungeon_miniboss_visible: bool
            alert_epic_enabled: bool
            alert_epic_message: str
            alert_epic_multiplier: float
            alert_epic_visible: bool
            alert_epic_shop_enabled: bool
            alert_epic_shop_message: str
            alert_epic_shop_visible: bool
            alert_eternal_present_enabled: bool
            alert_eternal_present_message: str
            alert_eternal_present_visible: bool
            alert_eternity_sealing_enabled: bool
            alert_eternity_sealing_message: str
            alert_farm_enabled: bool
            alert_farm_message: str
            alert_farm_multiplier: float
            alert_farm_visible: bool
            alert_guild_enabled: bool
            alert_guild_message: str
            alert_guild_visible: bool
            alert_horse_breed_enabled: bool
            alert_horse_breed_message: str
            alert_horse_breed_visible: bool
            alert_horse_race_enabled: bool
            alert_horse_race_message: str
            alert_horse_race_visible: bool
            alert_hunt_enabled: bool
            alert_hunt_message: str
            alert_hunt_multiplier: float
            alert_hunt_visible: bool
            alert_hunt_partner_enabled: bool
            alert_hunt_partner_message: str
            alert_hunt_partner_multiplier: float
            alert_hunt_partner_visible: bool
            alert_lootbox_enabled: bool
            alert_lootbox_message: str
            alert_lootbox_multiplier: float
            alert_lootbox_visible: bool
            alert_lottery_enabled: bool
            alert_lottery_message: str
            alert_lottery_visible: bool
            alert_love_share_enabled: bool
            alert_love_share_message: str
            alert_love_share_visible: bool
            alert_maintenance_enabled: bool
            alert_maintenance_message: str
            alert_maintenance_visible: bool
            alert_megarace_enabled: bool
            alert_megarace_message: str
            alert_megarace_visible: bool
            alert_minirace_enabled: bool
            alert_minirace_message: str
            alert_minirace_visible: bool
            alert_not_so_mini_boss_enabled: bool
            alert_not_so_mini_boss_message: str
            alert_not_so_mini_boss_visible: bool
            alert_partner_enabled: bool
            alert_partner_message: str
            alert_pet_tournament_enabled: bool
            alert_pet_tournament_message: str
            alert_pet_tournament_visible: bool
            alert_pets_enabled: bool
            alert_pets_message: str
            alert_pets_visible: bool
            alert_quest_enabled: bool
            alert_quest_message: str
            alert_quest_multiplier: float
            alert_quest_visible: bool
            alert_training_enabled: bool
            alert_training_message: str
            alert_training_multiplier: float
            alert_training_visible: bool
            alert_vote_enabled: bool
            alert_vote_message: str
            alert_vote_visible: bool
            alert_weekly_enabled: bool
            alert_weekly_message: str
            alert_weekly_multiplier: float
            alert_weekly_visible: bool
            alert_work_enabled: bool
            alert_work_message: str
            alert_work_multiplier: float
            alert_work_visible: bool
            ascended: bool
            area_20_cooldowns_enabled: bool
            auto_flex_enabled: bool
            auto_flex_ping_enabled: bool
            auto_flex_tip_read: bool
            auto_healing_active: bool
            auto_ready_enabled: bool
            bot_enabled: bool
            chocolate_box_unlocked: bool
            clan_name: str
            cmd_cd_visible: bool
            cmd_inventory_visible: bool
            cmd_cmd_ready_visible: bool
            cmd_slashboard_visible: bool
            christmas_area_enabled: bool
            context_helper_enabled: bool
            current_area: int
            dnd_mode_enabled: bool
            eternal_boosts_tier: int
            farm_helper_mode: int
            guild_quest_prompt_active: bool
            halloween_helper_enabled: bool
            hardmode_mode_enabled: bool
            heal_warning_enabled: bool
            hunt_end_time: datetime
            hunt_reminders_combined: bool
            inventory_bread: int
            inventory_carrot: int
            inventory_potato: int
            inventory_present_eternal: int
            inventory_ruby: int
            inventory_seed_bread: int
            inventory_seed_carrot: int
            inventory_seed_potato: int
            last_adventure_mode: str
            last_farm_seed: str
            last_hunt_mode: str
            last_lootbox: str
            last_quest_command: str
            last_training_command: str
            last_tt: datetime UTC
            last_workt_command: str
            megarace_helper_enabled: bool
            multiplier_management_enabled: bool
            partner_alert_threshold: int
            partner_channel_id: int
            partner_chocolate_box_unlocked: bool
            partner_donor_tier: int
            partner_hunt_end_time: datetime
            partner_id: int
            partner_name: str
            partner_pocket_watch_multiplier: float
            pet_helper_enabled: bool
            pet_helper_icon_mode: bool
            pet_tip_read: bool
            ping_after_message: bool
            portals_as_embed: bool
            portals_spacing_enabled: bool
            potion_dragon_breath_active: bool
            potion_flask_active: bool
            reactions_enabled: bool
            ready_after_all_commands: bool
            ready_as_embed: bool
            ready_channel_arena: int
            ready_channel_duel: int
            ready_channel_dungeon: int
            ready_channel_horse: int
            ready_embed_color: str
            ready_eternity_visible: bool
            ready_pets_claim_active: bool
            ready_pets_claim_after_every_pet: bool
            ready_other_on_top: bool
            ready_ping_user: bool
            ready_trade_daily_completed_visible: bool
            ready_trade_daily_visible: bool
            ready_up_next_as_timestamp: bool
            ready_up_next_show_hidden_reminders: bool
            ready_up_next_visible: bool
            reminder_channel_id: int
            round_card_active: bool
            ruby_counter_button_mode: bool
            ruby_counter_enabled: bool
            slash_mentions_enabled: bool
            time_potion_warning_enabled: bool
            time_travel_count: int
            top_hat_unlocked: bool
            tracking_enabled: bool
            trade_daily_done: int
            trade_daily_total: int
            training_helper_button_mode: bool
            training_helper_enabled: bool
            user_donor_tier: int
            user_pocket_watch_multiplier: float
        """
        await _update_user(self, **kwargs)
        await self.refresh()

    async def update_multiplier(self, activity: str, time_left: timedelta) -> None:
        """
        Checks if the provided time left differs from the time left of the active reminder.
        If yes, it will calculate the difference between the two, and then calculate the new multiplier and update it.
        To not deviate too much, if the provided time left is <= 10 seconds (hunt: <= 5s), no calculation takes place.

        Arguments
        ---------
            activity (str)
            time_left (timedelta): The time left found in the cooldown embed.
        """
        if self.current_area == 20: return
        if activity not in strings.ACTIVITIES_WITH_CHANGEABLE_MULTIPLIER: return

        # TODO: Once refactored to proper activities, make these 2 lines a percentage of the activity cooldown
        if activity != 'hunt' and time_left <= timedelta(seconds=10): return
        if activity =='hunt' and time_left <= timedelta(seconds=5): return

        current_time = utils.utcnow()
        time_left_actual_seconds: float = time_left.total_seconds()
        
        # Get active reminder. If no reminder is active, there is nothing to do.
        reminder: reminders.Reminder | None = None
        time_left_expected_seconds: float = 0
        if activity != 'hunt':
            try:
                reminder = await reminders.get_user_reminder(self.user_id, activity)
                time_left_expected_seconds = (reminder.end_time - current_time).total_seconds()
            except exceptions.NoDataFoundError:
                pass
        else:
            if self.hunt_end_time <= current_time: return
            time_left_expected_seconds = (self.hunt_end_time - current_time).total_seconds()

        # Get the current multiplier
        activity_column: str = strings.ACTIVITIES_COLUMNS[activity]
        alert_settings: UserAlert = getattr(self, activity_column)
        current_multiplier: float = alert_settings.multiplier

        # Calculate the new multiplier
        new_multiplier: float = 1.0
        if time_left_expected_seconds > 0:
            new_multiplier =  time_left_actual_seconds / time_left_expected_seconds * current_multiplier
        if new_multiplier <= 0: new_multiplier = 1.0
        if new_multiplier > 1 and not self.current_area == 18: new_multiplier = 1.0
        
        # Round up hunt multiplier to 0.0x to avoid super small fluctuations
        if activity == 'hunt':
            decimals: int = 3
            new_multiplier *= 10**decimals
            new_multiplier = 10 * ceil(new_multiplier / 10)
            new_multiplier /= 10**decimals

        # Update multiplier
        if current_multiplier != new_multiplier:
            kwargs: dict[str, float] = {} 
            kwargs[f'{strings.ACTIVITIES_COLUMNS[activity]}_multiplier'] = new_multiplier
            await self.update(**kwargs)


# Miscellaneous functions
async def _dict_to_user(record: dict[str, Any]) -> User:
    """Creates a User object from a database record

    Arguments
    ---------
    record: Database record from table "user" as a dict.

    Returns
    -------
    User object.

    Raises
    ------
    LookupError if something goes wrong reading the dict. Also logs this error to the database.
    """
    function_name: str = '_dict_to_user'
    none_date: datetime = datetime(1970, 1, 1, 0, 0, 0)
    try:
        user = User(
            alert_advent = UserAlert(enabled=bool(record['alert_advent_enabled']),
                                     message=record['alert_advent_message'],
                                     multiplier=1.0,
                                     visible=bool(record['alert_advent_visible'])),
            alert_adventure = UserAlert(enabled=bool(record['alert_adventure_enabled']),
                                        message=record['alert_adventure_message'],
                                        multiplier=float(record['alert_adventure_multiplier']),
                                        visible=bool(record['alert_adventure_visible'])),
            alert_arena = UserAlert(enabled=bool(record['alert_arena_enabled']),
                                    message=record['alert_arena_message'],
                                    multiplier=1.0,
                                    visible=bool(record['alert_arena_visible'])),
            alert_boo = UserAlert(enabled=bool(record['alert_boo_enabled']),
                                    message=record['alert_boo_message'],
                                    multiplier=record['alert_boo_multiplier'],
                                    visible=bool(record['alert_boo_visible'])),
            alert_boosts = UserAlert(enabled=bool(record['alert_boosts_enabled']),
                                     message=record['alert_boosts_message'],
                                     multiplier=1.0,
                                     visible=bool(record['alert_boosts_visible'])),
            alert_card_hand = UserAlert(enabled=bool(record['alert_card_hand_enabled']),
                                        message=record['alert_card_hand_message'],
                                        multiplier=float(record['alert_card_hand_multiplier']),
                                        visible=bool(record['alert_card_hand_visible'])),
            alert_chimney = UserAlert(enabled=bool(record['alert_chimney_enabled']),
                                      message=record['alert_chimney_message'],
                                      multiplier=record['alert_chimney_multiplier'],
                                      visible=bool(record['alert_chimney_visible'])),
            alert_big_arena = UserAlert(enabled=bool(record['alert_big_arena_enabled']),
                                        message=record['alert_big_arena_message'],
                                        multiplier=1.0,
                                        visible=bool(record['alert_big_arena_visible'])),
            alert_cel_dailyquest = UserAlert(enabled=bool(record['alert_cel_dailyquest_enabled']),
                                             message=record['alert_cel_dailyquest_message'],
                                             multiplier=1.0,
                                             visible=bool(record['alert_cel_dailyquest_visible'])),
            alert_cel_multiply = UserAlert(enabled=bool(record['alert_cel_multiply_enabled']),
                                           message=record['alert_cel_multiply_message'],
                                           multiplier=1.0,
                                           visible=bool(record['alert_cel_multiply_visible'])),
            alert_cel_sacrifice = UserAlert(enabled=bool(record['alert_cel_sacrifice_enabled']),
                                           message=record['alert_cel_sacrifice_message'],
                                           multiplier=1.0,
                                           visible=bool(record['alert_cel_sacrifice_visible'])),
            alert_daily = UserAlert(enabled=bool(record['alert_daily_enabled']),
                                    message=record['alert_daily_message'],
                                    multiplier=float(record['alert_daily_multiplier']),
                                    visible=bool(record['alert_daily_visible'])),
            alert_duel = UserAlert(enabled=bool(record['alert_duel_enabled']),
                                   message=record['alert_duel_message'],
                                   multiplier=float(record['alert_duel_multiplier']),
                                   visible=bool(record['alert_duel_visible'])),
            alert_dungeon_miniboss = UserAlert(enabled=bool(record['alert_dungeon_miniboss_enabled']),
                                               message=record['alert_dungeon_miniboss_message'],
                                               multiplier=1.0,
                                               visible=bool(record['alert_dungeon_miniboss_visible'])),
            alert_epic = UserAlert(enabled=bool(record['alert_epic_enabled']),
                                   message=record['alert_epic_message'],
                                   multiplier=float(record['alert_epic_multiplier']),
                                   visible=bool(record['alert_epic_visible'])),
            alert_epic_shop = UserAlert(enabled=bool(record['alert_epic_shop_enabled']),
                                        message=record['alert_epic_shop_message'],
                                        multiplier=1,
                                        visible=bool(record['alert_epic_shop_visible'])),
            alert_eternal_present = UserAlert(enabled=bool(record['alert_eternal_present_enabled']),
                                              message=record['alert_eternal_present_message'],
                                              multiplier=1.0,
                                              visible=bool(record['alert_eternal_present_visible'])),
            alert_eternity_sealing = UserAlert(enabled=bool(record['alert_eternity_sealing_enabled']),
                                               message=record['alert_eternity_sealing_message'],
                                               multiplier=1.0,
                                               visible=False),
            alert_farm = UserAlert(enabled=bool(record['alert_farm_enabled']),
                                   message=record['alert_farm_message'],
                                   multiplier=float(record['alert_farm_multiplier']),
                                   visible=bool(record['alert_farm_visible'])),
            alert_guild = UserAlert(enabled=bool(record['alert_guild_enabled']),
                                   message=record['alert_guild_message'],
                                   multiplier=1.0,
                                   visible=bool(record['alert_guild_visible'])),
            alert_horse_breed = UserAlert(enabled=bool(record['alert_horse_breed_enabled']),
                                          message=record['alert_horse_breed_message'],
                                          multiplier=1.0,
                                          visible=bool(record['alert_horse_breed_visible'])),
            alert_horse_race = UserAlert(enabled=bool(record['alert_horse_race_enabled']),
                                         message=record['alert_horse_race_message'],
                                         multiplier=1.0,
                                         visible=bool(record['alert_horse_race_visible'])),
            alert_hunt = UserAlert(enabled=bool(record['alert_hunt_enabled']),
                                   message=record['alert_hunt_message'],
                                   multiplier=float(record['alert_hunt_multiplier']),
                                   visible=bool(record['alert_hunt_visible'])),
            alert_hunt_partner = UserAlert(enabled=bool(record['alert_hunt_partner_enabled']),
                                   message=record['alert_hunt_partner_message'],
                                   multiplier=float(record['alert_hunt_partner_multiplier']),
                                   visible=bool(record['alert_hunt_partner_visible'])),
            alert_lootbox = UserAlert(enabled=bool(record['alert_lootbox_enabled']),
                                      message=record['alert_lootbox_message'],
                                      multiplier=float(record['alert_lootbox_multiplier']),
                                      visible=bool(record['alert_lootbox_visible'])),
            alert_lottery = UserAlert(enabled=bool(record['alert_lottery_enabled']),
                                      message=record['alert_lottery_message'],
                                      multiplier=1.0,
                                      visible=bool(record['alert_lottery_visible'])),
            alert_love_share = UserAlert(enabled=bool(record['alert_love_share_enabled']),
                                         message=record['alert_love_share_message'],
                                         multiplier=1.0,
                                         visible=bool(record['alert_love_share_visible'])),
            alert_maintenance = UserAlert(enabled=bool(record['alert_maintenance_enabled']),
                                          message=record['alert_maintenance_message'],
                                          multiplier=1.0,
                                          visible=False),
            alert_megarace = UserAlert(enabled=bool(record['alert_megarace_enabled']),
                                       message=record['alert_megarace_message'],
                                       multiplier=1.0,
                                       visible=bool(record['alert_megarace_visible'])),
            alert_minirace = UserAlert(enabled=bool(record['alert_minirace_enabled']),
                                       message=record['alert_minirace_message'],
                                       multiplier=1.0,
                                       visible=bool(record['alert_minirace_visible'])),
            alert_not_so_mini_boss = UserAlert(enabled=bool(record['alert_not_so_mini_boss_enabled']),
                                               message=record['alert_not_so_mini_boss_message'],
                                               multiplier=1.0,
                                               visible=bool(record['alert_not_so_mini_boss_visible'])),
            alert_partner = UserAlert(enabled=bool(record['alert_partner_enabled']),
                                      message=record['alert_partner_message'],
                                      multiplier=1.0,
                                      visible=True),
            alert_pet_tournament = UserAlert(enabled=bool(record['alert_pet_tournament_enabled']),
                                             message=record['alert_pet_tournament_message'],
                                             multiplier=1.0,
                                             visible=bool(record['alert_pet_tournament_visible'])),
            alert_pets = UserAlert(enabled=bool(record['alert_pets_enabled']),
                                   message=record['alert_pets_message'],
                                   multiplier=1.0,
                                   visible=record['alert_pets_visible']),
            alert_quest = UserAlert(enabled=bool(record['alert_quest_enabled']),
                                    message=record['alert_quest_message'],
                                    multiplier=float(record['alert_quest_multiplier']),
                                    visible=bool(record['alert_quest_visible'])),
            alert_training = UserAlert(enabled=bool(record['alert_training_enabled']),
                                       message=record['alert_training_message'],
                                       multiplier=float(record['alert_training_multiplier']),
                                       visible=bool(record['alert_training_visible'])),
            alert_vote = UserAlert(enabled=bool(record['alert_vote_enabled']),
                                   message=record['alert_vote_message'],
                                   multiplier=1.0,
                                   visible=bool(record['alert_vote_visible'])),
            alert_weekly = UserAlert(enabled=bool(record['alert_weekly_enabled']),
                                    message=record['alert_weekly_message'],
                                    multiplier=float(record['alert_weekly_multiplier']),
                                    visible=bool(record['alert_weekly_visible'])),
            alert_work = UserAlert(enabled=bool(record['alert_work_enabled']),
                                   message=record['alert_work_message'],
                                   multiplier=float(record['alert_work_multiplier']),
                                   visible=bool(record['alert_work_visible'])),
            alts = record['alts'],
            ascended = bool(record['ascended']),
            area_20_cooldowns_enabled = bool(record['area_20_cooldowns_enabled']),
            auto_flex_enabled = bool(record['auto_flex_enabled']),
            auto_flex_ping_enabled = bool(record['auto_flex_ping_enabled']),
            auto_healing_active = bool(record['auto_healing_active']),
            auto_ready_enabled = bool(record['auto_ready_enabled']),
            auto_flex_tip_read = bool(record['auto_flex_tip_read']),
            bot_enabled = bool(record['bot_enabled']),
            chocolate_box_unlocked = bool(record['chocolate_box_unlocked']),
            clan_name = record['clan_name'],
            christmas_area_enabled = bool(record['christmas_area_enabled']),
            cmd_cd_visible = record['cmd_cd_visible'],
            cmd_inventory_visible = record['cmd_inventory_visible'],
            cmd_ready_visible = record['cmd_ready_visible'],
            cmd_slashboard_visible = record['cmd_slashboard_visible'],
            context_helper_enabled = bool(record['context_helper_enabled']),
            current_area = -1 if record['current_area'] is None else record['current_area'],
            dnd_mode_enabled = bool(record['dnd_mode_enabled']),
            eternal_boosts_tier = record['eternal_boosts_tier'],
            farm_helper_mode = record['farm_helper_mode'],
            guild_quest_prompt_active = bool(record['guild_quest_prompt_active']),
            halloween_helper_enabled = bool(record['halloween_helper_enabled']),
            hardmode_mode_enabled = bool(record['hardmode_mode_enabled']),
            heal_warning_enabled = bool(record['heal_warning_enabled']),
            hunt_end_time = datetime.fromisoformat(record['hunt_end_time']).replace(tzinfo=timezone.utc),
            hunt_reminders_combined = bool(record['hunt_reminders_combined']),
            inventory = UserInventory(bread=(record['inventory_bread']), carrot=(record['inventory_carrot']),
                                      potato=(record['inventory_potato']),
                                      present_eternal=(record['inventory_present_eternal']),
                                      ruby=(record['inventory_ruby']), seed_bread=(record['inventory_seed_bread']),
                                      seed_carrot=(record['inventory_seed_carrot']),
                                      seed_potato=(record['inventory_seed_potato'])),
            last_adventure_mode = '' if record['last_adventure_mode'] is None else record['last_adventure_mode'],
            last_farm_seed = '' if record['last_farm_seed'] is None else record['last_farm_seed'],
            last_hunt_mode = '' if record['last_hunt_mode'] is None else record['last_hunt_mode'],
            last_lootbox = '' if record['last_lootbox'] is None else record['last_lootbox'],
            last_quest_command = '' if record['last_quest_command'] is None else record['last_quest_command'],
            last_training_command = record['last_training_command'],
            last_tt = datetime.fromisoformat(record['last_tt']).replace(tzinfo=timezone.utc) if record['last_tt'] is not None else none_date,
            last_work_command = '' if record['last_work_command'] is None else record['last_work_command'],
            megarace_helper_enabled = bool(record['megarace_helper_enabled']),
            multiplier_management_enabled = bool(record['multiplier_management_enabled']),
            partner_alert_threshold = record['partner_alert_threshold'],
            partner_channel_id = record['partner_channel_id'],
            partner_chocolate_box_unlocked = bool(record['partner_chocolate_box_unlocked']),
            partner_donor_tier = record['partner_donor_tier'],
            partner_hunt_end_time = datetime.fromisoformat(record['partner_hunt_end_time']).replace(tzinfo=timezone.utc),
            partner_id = record['partner_id'],
            partner_name = record['partner_name'],
            partner_pocket_watch_multiplier = float(record['partner_pocket_watch_multiplier']),
            pet_helper_enabled = record['pet_helper_enabled'],
            pet_helper_icon_mode = bool(record['pet_helper_icon_mode']),
            pet_tip_read = bool(record['pet_tip_read']),
            ping_after_message = bool(record['ping_after_message']),
            portals_as_embed = bool(record['portals_as_embed']),
            portals_spacing_enabled = bool(record['portals_spacing_enabled']),
            potion_dragon_breath_active = bool(record['potion_dragon_breath_active']),
            potion_flask_active = bool(record['potion_flask_active']),
            reactions_enabled = bool(record['reactions_enabled']),
            ready_after_all_commands = bool(record['ready_after_all_commands']),
            ready_as_embed = bool(record['ready_as_embed']),
            ready_channel_arena = record['ready_channel_arena'],
            ready_channel_duel = record['ready_channel_duel'],
            ready_channel_dungeon = record['ready_channel_dungeon'],
            ready_channel_horse = record['ready_channel_horse'],
            ready_embed_color = record['ready_embed_color'],
            ready_eternity_visible = bool(record['ready_eternity_visible']),
            ready_other_on_top = bool(record['ready_other_on_top']),
            ready_pets_claim_active = bool(record['ready_pets_claim_active']),
            ready_pets_claim_after_every_pet = bool(record['ready_pets_claim_after_every_pet']),
            ready_ping_user = bool(record['ready_ping_user']),
            ready_trade_daily_completed_visible = bool(record['ready_trade_daily_completed_visible']),
            ready_trade_daily_visible = bool(record['ready_trade_daily_visible']),
            ready_up_next_as_timestamp = bool(record['ready_up_next_as_timestamp']),
            ready_up_next_show_hidden_reminders = bool(record['ready_up_next_show_hidden_reminders']),
            ready_up_next_visible = bool(record['ready_up_next_visible']),
            reminder_channel_id = record['reminder_channel_id'],
            round_card_active = bool(record['round_card_active']),
            ruby_counter_button_mode = bool(record['ruby_counter_button_mode']),
            ruby_counter_enabled = bool(record['ruby_counter_enabled']),
            slash_mentions_enabled = bool(record['slash_mentions_enabled']),
            time_potion_warning_enabled = bool(record['time_potion_warning_enabled']),
            time_travel_count = record['time_travel_count'],
            top_hat_unlocked = bool(record['top_hat_unlocked']),
            tracking_enabled = bool(record['tracking_enabled']),
            trade_daily_done = record['trade_daily_done'],
            trade_daily_total = record['trade_daily_total'],
            training_helper_button_mode = bool(record['training_helper_button_mode']),
            training_helper_enabled = bool(record['training_helper_enabled']),
            user_donor_tier = record['user_donor_tier'],
            user_id = record['user_id'],
            user_pocket_watch_multiplier = float(record['user_pocket_watch_multiplier']),
        )
    except Exception as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_DICT_TO_OBJECT.format(function=function_name, record=record)
        )
        raise LookupError(error)

    return user


# Get data
async def get_user(user_id: int) -> User:
    """Gets all user settings.

    Returns
    -------
    User object

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.FirstTimeUserError if no user was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table: str = 'users'
    function_name: str = 'get_user'
    sql: str = f'SELECT * FROM {table} WHERE user_id=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        record: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.FirstTimeUserError(f'No user data found in database for user "{user_id}".')
    record: dict[str, Any] = dict(record)
    record['alts'] = await alts_db.get_alts(user_id)
    user: User = await _dict_to_user(record)

    return user


async def get_all_users() -> tuple[User,...]:
    """Gets all user settings of all users.

    Returns
    -------
    Tuple with User objects

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table: str = 'users'
    function_name: str = 'get_all_users'
    sql: str = f'SELECT * FROM {table}'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql)
        records: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        raise exceptions.FirstTimeUserError(f'No user data found in database (how likely is that).')
    users: list[User] = []
    for record in records:
        record: dict[str, Any] = dict(record)
        record['alts'] = await alts_db.get_alts(record['user_id'])
        user: User = await _dict_to_user(record)
        users.append(user)

    return tuple(users)


async def get_users_by_clan_name(clan_name: str) -> tuple[User,...]:
    """Gets all user settings of all users that have a certain clan_name set.

    Returns
    -------
    Tuple with User objects

    Raises
    ------
    sqlite3.Error if something happened within the database.
    exceptions.NoDataFoundError if no guild was found.
    LookupError if something goes wrong reading the dict.
    Also logs all errors to the database.
    """
    table: str = 'users'
    function_name: str = 'get_users_by_clan_name'
    sql: str = f'SELECT * FROM {table} WHERE clan_name=?'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        records: list[Any] = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        raise exceptions.FirstTimeUserError(f'No users found for clan {clan_name} ')
    users: list[User] = []
    for record in records:
        record: dict[str, Any] = dict(record)
        record['alts'] = await alts_db.get_alts(record['user_id'])
        user: User = await _dict_to_user(record)
        users.append(user)

    return tuple(users)


async def get_user_count() -> int:
    """Gets the amount of users in the table "users".

    Returns
    -------
    Amound of users: int

    Raises
    ------
    sqlite3.Error if something happened within the database. Also logs this error to the log file.
    """
    table: str = 'users'
    function_name: str = 'get_user_count'
    sql: str = f'SELECT COUNT(user_id) FROM {table}'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql)
        record: Any = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    user_count: int
    (user_count,) = record

    return user_count


# Write Data
async def _update_user(user: User, **kwargs) -> None:
    """Updates user record. Use User.update() to trigger this function.
    If user_donor_tier is updated and a partner is set, the partner's partner_donor_tier is updated as well.

    Arguments
    ---------
    user_id: int
    kwargs (column=value):
        alert_advent_enabled: bool
        alert_advent_message: str
        alert_advent_visible: bool
        alert_adventure_enabled: bool
        alert_adventure_message: str
        alert_adventure_multiplier: float
        alert_adventure_visible: bool
        alert_arena_enabled: bool
        alert_arena_message: str
        alert_arena_visible: bool
        alert_big_arena_enabled: bool
        alert_big_arena_message: str
        alert_big_arena_visible: bool
        alert_boo_enabled: bool
        alert_boo_message: str
        alert_boo_multiplier: float
        alert_boo_visible: bool
        alert_boosts_enabled: bool
        alert_boosts_message: str
        alert_boosts_visible: bool
        alert_card_hand_enabled: bool
        alert_card_hand_message: str
        alert_card_hand_multiplier: float
        alert_card_hand_visible: bool
        alert_cel_dailyquest_enabled: bool
        alert_cel_dailyquest_message: str
        alert_cel_dailyquest_visible: bool
        alert_cel_multiply_enabled: bool
        alert_cel_multiply_message: str
        alert_cel_multiply_visible: bool
        alert_cel_sacrifice_enabled: bool
        alert_cel_sacrifice_message: str
        alert_cel_sacrifice_visible: bool
        alert_chimney_enabled: bool
        alert_chimney_message: str
        alert_chimney_multiplier: float
        alert_chimney_visible: bool
        alert_daily_enabled: bool
        alert_daily_message: str
        alert_daily_multiplier: float
        alert_daily_visible: bool
        alert_duel_enabled: bool
        alert_duel_message: str
        alert_duel_multiplier: float
        alert_duel_visible: bool
        alert_dungeon_miniboss_enabled: bool
        alert_dungeon_miniboss_message: str
        alert_dungeon_miniboss_visible: bool
        alert_epic_enabled: bool
        alert_epic_message: str
        alert_epic_multiplier: float
        alert_epic_visible: bool
        alert_epic_shop_enabled: bool
        alert_epic_shop_message: str
        alert_epic_shop_visible: bool
        alert_eternal_present_enabled: bool
        alert_eternal_present_message: str
        alert_eternal_present_visible: bool
        alert_eternity_sealing_enabled: bool
        alert_eternity_sealing_message: str
        alert_farm_enabled: bool
        alert_farm_message: str
        alert_farm_multiplier: float
        alert_farm_visible: bool
        alert_guild_enabled: bool
        alert_guild_message: str
        alert_guild_visible: bool
        alert_horse_breed_enabled: bool
        alert_horse_breed_message: str
        alert_horse_breed_visible: bool
        alert_horse_race_enabled: bool
        alert_horse_race_message: str
        alert_horse_race_visible: bool
        alert_hunt_enabled: bool
        alert_hunt_message: str
        alert_hunt_multiplier: float
        alert_hunt_visible: bool
        alert_hunt_partner_enabled: bool
        alert_hunt_partner_message: str
        alert_hunt_partner_multiplier: float
        alert_hunt_partner_visible: bool
        alert_lootbox_enabled: bool
        alert_lootbox_message: str
        alert_lootbox_multiplier: float
        alert_lootbox_visible: bool
        alert_lottery_enabled: bool
        alert_lottery_message: str
        alert_lottery_visible: bool
        alert_love_share_enabled: bool
        alert_love_share_message: str
        alert_love_share_visible: bool
        alert_maintenance_enabled: bool
        alert_maintenance_message: str
        alert_maintenance_visible: bool
        alert_megarace_enabled: bool
        alert_megarace_message: str
        alert_megarace_visible: bool
        alert_minirace_enabled: bool
        alert_minirace_message: str
        alert_minirace_visible: bool
        alert_not_so_mini_boss_enabled: bool
        alert_not_so_mini_boss_message: str
        alert_not_so_mini_boss_visible: bool
        alert_partner_enabled: bool
        alert_partner_message: str
        alert_pet_tournament_enabled: bool
        alert_pet_tournament_message: str
        alert_pet_tournament_visible: bool
        alert_pets_enabled: bool
        alert_pets_message: str
        alert_pets_visible: bool
        alert_quest_enabled: bool
        alert_quest_message: str
        alert_quest_multiplier: float
        alert_quest_visible: bool
        alert_training_enabled: bool
        alert_training_message: str
        alert_training_multiplier: float
        alert_training_visible: bool
        alert_vote_enabled: bool
        alert_vote_message: str
        alert_vote_visible: bool
        alert_weekly_enabled: bool
        alert_weekly_message: str
        alert_weekly_multiplier: float
        alert_weekly_visible: bool
        alert_work_enabled: bool
        alert_work_message: str
        alert_work_multiplier: float
        alert_work_visible: bool
        ascended: bool
        area_20_cooldowns_enabled: bool
        auto_flex_enabled: bool
        auto_flex_ping_enabled: bool
        auto_flex_tip_read: bool
        auto_healing_active: bool
        auto_ready_enabled: bool
        bot_enabled: bool
        chocolate_box_unlocked: bool
        clan_name: str
        cmd_cd_visible: bool
        cmd_inventory_visible: bool
        cmd_cmd_ready_visible: bool
        cmd_slashboard_visible: bool
        christmas_area_enabled: bool
        context_helper_enabled: bool
        current_area: int
        dnd_mode_enabled: bool
        eternal_boosts_tier: int
        farm_helper_mode: int
        guild_quest_prompt_active: bool
        halloween_helper_enabled: bool
        hardmode_mode_enabled: bool
        heal_warning_enabled: bool
        hunt_end_time: datetime
        hunt_reminders_combined: bool
        inventory_bread: int
        inventory_carrot: int
        inventory_potato: int
        inventory_present_eternal: int
        inventory_ruby: int
        inventory_seed_bread: int
        inventory_seed_carrot: int
        inventory_seed_potato: int
        last_adventure_mode: str
        last_farm_seed: str
        last_hunt_mode: str
        last_lootbox: str
        last_quest_command: str
        last_training_command: str
        last_tt: datetime UTC
        last_workt_command: str
        megarace_helper_enabled: bool
        multiplier_management_enabled: bool
        partner_alert_threshold: int
        partner_channel_id: int
        partner_chocolate_box_unlocked: bool
        partner_donor_tier: int
        partner_hunt_end_time: datetime
        partner_id: int
        partner_name: str$
        partner_pocket_watch_multiplier: float
        pet_helper_enabled: bool
        pet_helper_icon_mode: bool
        pet_tip_read: bool
        ping_after_message: bool
        portals_as_embed: bool
        portals_spacing_enabled: bool
        potion_dragon_breath_active: bool
        potion_flask_active: bool
        reactions_enabled: bool
        ready_after_all_commands: bool
        ready_as_embed: bool
        ready_channel_arena: int
        ready_channel_duel: int
        ready_channel_dungeon: int
        ready_channel_horse: int
        ready_embed_color: str
        ready_eternity_visible: bool
        ready_pets_claim_active: bool
        ready_pets_claim_after_every_pet: bool
        ready_other_on_top: bool
        ready_ping_user: bool
        ready_trade_daily_completed_visible: bool
        ready_trade_daily_visible: bool
        ready_up_next_as_timestamp: bool
        ready_up_next_show_hidden_reminders: bool
        ready_up_next_visible: bool
        reminder_channel_id: int
        round_card_active: bool
        ruby_counter_button_mode: bool
        ruby_counter_enabled: bool
        slash_mentions_enabled: bool
        time_potion_warning_enabled: bool
        time_travel_count: int
        top_hat_unlocked: bool
        tracking_enabled: bool
        trade_daily_done: int
        trade_daily_total: int
        training_helper_button_mode: bool
        training_helper_enabled: bool
        user_donor_tier: int
        user_pocket_watch_multiplier: float

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table: str = 'users'
    function_name: str = '_update_user'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        sql: str = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['user_id'] = user.user_id
        sql = f'{sql} WHERE user_id = :user_id'
        cur.execute(sql, kwargs)
        if 'user_donor_tier' in kwargs and user.partner_id is not None:
            partner: User = await get_user(user.partner_id)
            await partner.update(partner_donor_tier=kwargs['user_donor_tier'])
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise


async def insert_user(user_id: int) -> User:
    """Inserts a record in the table "users".

    Returns
    -------
    User object with the newly created user.

    Raises
    ------
    sqlite3.Error if something happened within the database.
    Also logs all errors to the database.
    """
    function_name: str = 'insert_user'
    table: str = 'users'
    columns: str = ''
    if settings.LITE_MODE:
        reactions_enabled: int = 0
        ready_after_all_commands: int = 0
    else:
        reactions_enabled: int = 1
        ready_after_all_commands: int = 1
    values: list[int] = [user_id, reactions_enabled, ready_after_all_commands]
    for activity, default_message in strings.DEFAULT_MESSAGES.items():
        columns = f'{columns},{strings.ACTIVITIES_COLUMNS[activity]}_message'
        values.append(default_message)
    sql: str = f'INSERT INTO {table} (user_id, reactions_enabled, ready_after_all_commands{columns}) VALUES ('
    value: int
    for value in values:
        sql = f'{sql}?,'
    sql = f'{sql.strip(",")})'
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute(sql, values)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    user: User = await get_user(user_id)

    return user