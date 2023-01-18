# users.py
"""Provides access to the table "users" in the database"""

from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import NamedTuple, Tuple

from database import errors
from resources import exceptions, settings, strings


# Containers
class UserAlert(NamedTuple):
    """Object that summarizes all user settings for a specific alert"""
    enabled: bool
    message: str
    multiplier: float
    visible: bool

@dataclass()
class User():
    """Object that represents a record from table "user"."""
    alert_advent: UserAlert
    alert_adventure: UserAlert
    alert_arena: UserAlert
    alert_big_arena: UserAlert
    alert_boo: UserAlert
    alert_chimney: UserAlert
    alert_daily: UserAlert
    alert_duel: UserAlert
    alert_dungeon_miniboss: UserAlert
    alert_epic: UserAlert
    alert_farm: UserAlert
    alert_guild: UserAlert
    alert_horse_breed: UserAlert
    alert_horse_race: UserAlert
    alert_hunt: UserAlert
    alert_lootbox: UserAlert
    alert_lottery: UserAlert
    alert_not_so_mini_boss: UserAlert
    alert_partner: UserAlert
    alert_party_popper: UserAlert
    alert_pet_tournament: UserAlert
    alert_pets: UserAlert
    alert_quest: UserAlert
    alert_training: UserAlert
    alert_vote: UserAlert
    alert_weekly: UserAlert
    alert_work: UserAlert
    ascended: bool
    auto_flex_enabled: bool
    auto_flex_tip_read: bool
    auto_ready_enabled: bool
    bot_enabled: bool
    clan_name: str
    christmas_area_enabled: bool
    cmd_cd_visible: bool
    cmd_inventory_visible: bool
    cmd_ready_visible: bool
    cmd_slashboard_visible: bool
    context_helper_enabled: bool
    current_area: int
    dnd_mode_enabled: bool
    halloween_helper_enabled: bool
    hardmode_mode_enabled: bool
    heal_warning_enabled: bool
    hunt_rotation_enabled: bool
    last_adventure_mode: str
    last_farm_seed: str
    last_hunt_mode: str
    last_lootbox: str
    last_quest_command: str
    last_training_command: str
    last_tt: datetime
    last_work_command: str
    partner_channel_id: int
    partner_donor_tier: int
    partner_hunt_end_time: datetime
    partner_id: int
    partner_name: str
    pet_helper_enabled: bool
    pet_helper_icon_mode: bool
    pet_tip_read: bool
    ping_after_message: bool
    portals_as_embed: bool
    portals_spacing_enabled: bool
    guild_quest_prompt_active: bool
    reactions_enabled: bool
    ready_as_embed: bool
    ready_channel_arena: int
    ready_channel_duel: int
    ready_channel_dungeon: int
    ready_channel_horse: int
    ready_embed_color: str
    ready_pets_claim_active: bool
    ready_pets_claim_after_every_pet: bool
    ready_other_on_top: bool
    ready_up_next_as_timestamp: bool
    ready_up_next_show_hidden_reminders: bool
    ready_up_next_visible: bool
    rubies: int
    ruby_counter_button_mode: bool
    ruby_counter_enabled: bool
    slash_mentions_enabled: bool
    time_travel_count: int
    tracking_enabled: bool
    training_helper_button_mode: bool
    training_helper_enabled: bool
    user_donor_tier: int
    user_id: int

    async def refresh(self) -> None:
        """Refreshes user data from the database."""
        new_settings: User = await get_user(self.user_id)
        self.alert_advent = new_settings.alert_advent
        self.alert_adventure = new_settings.alert_adventure
        self.alert_arena = new_settings.alert_arena
        self.alert_boo = new_settings.alert_boo
        self.alert_chimney = new_settings.alert_chimney
        self.alert_big_arena = new_settings.alert_big_arena
        self.alert_daily = new_settings.alert_daily
        self.alert_duel = new_settings.alert_duel
        self.alert_dungeon_miniboss = new_settings.alert_dungeon_miniboss
        self.alert_epic = new_settings.alert_epic
        self.alert_farm = new_settings.alert_farm
        self.alert_guild = new_settings.alert_guild
        self.alert_horse_breed = new_settings.alert_horse_breed
        self.alert_horse_race = new_settings.alert_horse_race
        self.alert_hunt = new_settings.alert_hunt
        self.alert_lootbox = new_settings.alert_lootbox
        self.alert_lottery = new_settings.alert_lottery
        self.alert_not_so_mini_boss = new_settings.alert_not_so_mini_boss
        self.alert_partner = new_settings.alert_partner
        self.alert_party_popper = new_settings.alert_party_popper
        self.alert_pet_tournament = new_settings.alert_pet_tournament
        self.alert_pets = new_settings.alert_pets
        self.alert_quest = new_settings.alert_quest
        self.alert_training = new_settings.alert_training
        self.alert_vote = new_settings.alert_vote
        self.alert_weekly = new_settings.alert_weekly
        self.alert_work = new_settings.alert_work
        self.ascended = new_settings.ascended
        self.auto_flex_enabled = new_settings.auto_flex_enabled
        self.auto_flex_tip_read = new_settings.auto_flex_tip_read
        self.auto_ready_enabled = new_settings.auto_ready_enabled
        self.bot_enabled = new_settings.bot_enabled
        self.clan_name = new_settings.clan_name
        self.christmas_area_enabled = new_settings.christmas_area_enabled
        self.cmd_cd_visible = new_settings.cmd_cd_visible
        self.cmd_inventory_visible = new_settings.cmd_inventory_visible
        self.cmd_ready_visible = new_settings.cmd_ready_visible
        self.cmd_slashboard_visible = new_settings.cmd_slashboard_visible
        self.context_helper_enabled = new_settings.context_helper_enabled
        self.current_area = new_settings.current_area
        self.dnd_mode_enabled = new_settings.dnd_mode_enabled
        self.halloween_helper_enabled = new_settings.halloween_helper_enabled
        self.hardmode_mode_enabled = new_settings.hardmode_mode_enabled
        self.heal_warning_enabled = new_settings.heal_warning_enabled
        self.hunt_rotation_enabled = new_settings.hunt_rotation_enabled
        self.last_adventure_mode = new_settings.last_adventure_mode
        self.last_farm_seed = new_settings.last_farm_seed
        self.last_hunt_mode = new_settings.last_hunt_mode
        self.last_lootbox = new_settings.last_lootbox
        self.last_quest_command = new_settings.last_quest_command
        self.last_training_command = new_settings.last_training_command
        self.last_tt = new_settings.last_tt
        self.last_work_command = new_settings.last_work_command
        self.partner_channel_id = new_settings.partner_channel_id
        self.partner_donor_tier = new_settings.partner_donor_tier
        self.partner_hunt_end_time = new_settings.partner_hunt_end_time
        self.partner_id = new_settings.partner_id
        self.partner_name = new_settings.partner_name
        self.pet_helper_enabled = new_settings.pet_helper_enabled
        self.pet_helper_icon_mode = new_settings.pet_helper_icon_mode
        self.pet_tip_read = new_settings.pet_tip_read
        self.ping_after_message = new_settings.ping_after_message
        self.portals_as_embed = new_settings.portals_as_embed
        self.portals_spacing_enabled = new_settings.portals_spacing_enabled
        self.guild_quest_prompt_active = new_settings.guild_quest_prompt_active
        self.reactions_enabled = new_settings.reactions_enabled
        self.ready_as_embed = new_settings.ready_as_embed
        self.ready_channel_arena = new_settings.ready_channel_arena
        self.ready_channel_duel = new_settings.ready_channel_duel
        self.ready_channel_dungeon = new_settings.ready_channel_dungeon
        self.ready_channel_horse = new_settings.ready_channel_horse
        self.ready_embed_color = new_settings.ready_embed_color
        self.ready_pets_claim_active = new_settings.ready_pets_claim_active
        self.ready_pets_claim_after_every_pet = new_settings.ready_pets_claim_after_every_pet
        self.ready_other_on_top = new_settings.ready_other_on_top
        self.ready_up_next_as_timestamp = new_settings.ready_up_next_as_timestamp
        self.ready_up_next_show_hidden_reminders = new_settings.ready_up_next_show_hidden_reminders
        self.ready_up_next_visible = new_settings.ready_up_next_visible
        self.rubies = new_settings.rubies
        self.ruby_counter_button_mode = new_settings.ruby_counter_button_mode
        self.ruby_counter_enabled = new_settings.ruby_counter_enabled
        self.slash_mentions_enabled = new_settings.slash_mentions_enabled
        self.time_travel_count = new_settings.time_travel_count
        self.tracking_enabled = new_settings.tracking_enabled
        self.training_helper_button_mode = new_settings.training_helper_button_mode
        self.training_helper_enabled = new_settings.training_helper_enabled
        self.user_donor_tier = new_settings.user_donor_tier

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
            alert_boo_visible: bool
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
            alert_lootbox_enabled: bool
            alert_lootbox_message: str
            alert_lootbox_multiplier: float
            alert_lootbox_visible: bool
            alert_lottery_enabled: bool
            alert_lottery_message: str
            alert_lottery_visible: bool
            alert_not_so_mini_boss_enabled: bool
            alert_not_so_mini_boss_message: str
            alert_not_so_mini_boss_visible: bool
            alert_partner_enabled: bool
            alert_partner_message: str
            alert_party_popper_enabled: bool
            alert_party_popper_message: str
            alert_party_popper_visible: bool
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
            auto_flex_enabled: bool
            auto_flex_tip_read: bool
            auto_ready_enabled: bool
            bot_enabled: bool
            clan_name: str
            cmd_cd_visible: bool
            cmd_inventory_visible: bool
            cmd_cmd_ready_visible: bool
            cmd_slashboard_visible: bool
            christmas_area_enabled: bool
            context_helper_enabled: bool
            current_area: int
            dnd_mode_enabled: bool
            guild_quest_prompt_active: bool
            halloween_helper_enabled: bool
            hardmode_mode_enabled: bool
            heal_warning_enabled: bool
            hunt_rotation_enabled: bool
            last_adventure_mode: str
            last_farm_seed: str
            last_hunt_mode: str
            last_lootbox: str
            last_quest_command: str
            last_training_command: str
            last_tt: datetime UTC
            last_workt_command: str
            partner_channel_id: int
            partner_donor_tier: int
            partner_hunt_end_time: datetime
            partner_id: int
            partner_name: str
            pet_helper_enabled: bool
            pet_helper_icon_mode: bool
            pet_tip_read: bool
            ping_after_message: bool
            portals_as_embed: bool
            portals_spacing_enabled: bool
            reactions_enabled: bool
            ready_as_embed: bool
            ready_channel_arena: int
            ready_channel_duel: int
            ready_channel_dungeon: int
            ready_channel_horse: int
            ready_embed_color: str
            ready_pets_claim_active: bool
            ready_pets_claim_after_every_pet: bool
            ready_other_on_top: bool
            ready_up_next_as_timestamp: bool
            ready_up_next_show_hidden_reminders: bool
            ready_up_next_visible: bool
            rubies: int
            ruby_counter_button_mode: bool
            ruby_counter_enabled: bool
            slash_mentions_enabled: bool
            time_travel_count: int
            tracking_enabled: bool
            training_helper_button_mode: bool
            training_helper_enabled: bool
            user_donor_tier: int
        """
        await _update_user(self, **kwargs)
        await self.refresh()


# Miscellaneous functions
async def _dict_to_user(record: dict) -> User:
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
    function_name = '_dict_to_user'
    none_date = datetime(1970, 1, 1, 0, 0, 0)
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
                                    multiplier=1.0,
                                    visible=bool(record['alert_boo_visible'])),
            alert_chimney = UserAlert(enabled=bool(record['alert_chimney_enabled']),
                                      message=record['alert_chimney_message'],
                                      multiplier=float(record['alert_chimney_multiplier']),
                                      visible=bool(record['alert_chimney_visible'])),
            alert_big_arena = UserAlert(enabled=bool(record['alert_big_arena_enabled']),
                                        message=record['alert_big_arena_message'],
                                        multiplier=1.0,
                                        visible=bool(record['alert_big_arena_visible'])),
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
            alert_lootbox = UserAlert(enabled=bool(record['alert_lootbox_enabled']),
                                      message=record['alert_lootbox_message'],
                                      multiplier=float(record['alert_lootbox_multiplier']),
                                      visible=bool(record['alert_lootbox_visible'])),
            alert_lottery = UserAlert(enabled=bool(record['alert_lottery_enabled']),
                                      message=record['alert_lottery_message'],
                                      multiplier=1.0,
                                      visible=bool(record['alert_lottery_visible'])),
            alert_not_so_mini_boss = UserAlert(enabled=bool(record['alert_not_so_mini_boss_enabled']),
                                               message=record['alert_not_so_mini_boss_message'],
                                               multiplier=1.0,
                                               visible=bool(record['alert_not_so_mini_boss_visible'])),
            alert_partner = UserAlert(enabled=bool(record['alert_partner_enabled']),
                                      message=record['alert_partner_message'],
                                      multiplier=1.0,
                                      visible=True),
            alert_party_popper = UserAlert(enabled=bool(record['alert_party_popper_enabled']),
                                           message=record['alert_party_popper_message'],
                                           multiplier=1.0,
                                           visible=bool(record['alert_party_popper_visible'])),
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
            ascended = bool(record['ascended']),
            auto_flex_enabled = bool(record['auto_flex_enabled']),
            auto_ready_enabled = bool(record['auto_ready_enabled']),
            auto_flex_tip_read = bool(record['auto_flex_tip_read']),
            bot_enabled = bool(record['bot_enabled']),
            clan_name = record['clan_name'],
            christmas_area_enabled = bool(record['christmas_area_enabled']),
            cmd_cd_visible = record['cmd_cd_visible'],
            cmd_inventory_visible = record['cmd_inventory_visible'],
            cmd_ready_visible = record['cmd_ready_visible'],
            cmd_slashboard_visible = record['cmd_slashboard_visible'],
            context_helper_enabled = bool(record['context_helper_enabled']),
            current_area = -1 if record['current_area'] is None else record['current_area'],
            dnd_mode_enabled = bool(record['dnd_mode_enabled']),
            guild_quest_prompt_active = bool(record['guild_quest_prompt_active']),
            halloween_helper_enabled = bool(record['halloween_helper_enabled']),
            hardmode_mode_enabled = bool(record['hardmode_mode_enabled']),
            heal_warning_enabled = bool(record['heal_warning_enabled']),
            hunt_rotation_enabled = bool(record['hunt_rotation_enabled']),
            last_adventure_mode = '' if record['last_adventure_mode'] is None else record['last_adventure_mode'],
            last_farm_seed = '' if record['last_farm_seed'] is None else record['last_farm_seed'],
            last_hunt_mode = '' if record['last_hunt_mode'] is None else record['last_hunt_mode'],
            last_lootbox = '' if record['last_lootbox'] is None else record['last_lootbox'],
            last_quest_command = '' if record['last_quest_command'] is None else record['last_quest_command'],
            last_training_command = record['last_training_command'],
            last_tt = datetime.fromisoformat(record['last_tt']) if record['last_tt'] is not None else none_date,
            last_work_command = '' if record['last_work_command'] is None else record['last_work_command'],
            partner_channel_id = record['partner_channel_id'],
            partner_donor_tier = record['partner_donor_tier'],
            partner_hunt_end_time = datetime.fromisoformat(record['partner_hunt_end_time']),
            partner_id = record['partner_id'],
            partner_name = record['partner_name'],
            pet_helper_enabled = record['pet_helper_enabled'],
            pet_helper_icon_mode = bool(record['pet_helper_icon_mode']),
            pet_tip_read = bool(record['pet_tip_read']),
            ping_after_message = bool(record['ping_after_message']),
            portals_as_embed = bool(record['portals_as_embed']),
            portals_spacing_enabled = bool(record['portals_spacing_enabled']),
            reactions_enabled = bool(record['reactions_enabled']),
            ready_as_embed = bool(record['ready_as_embed']),
            ready_channel_arena = record['ready_channel_arena'],
            ready_channel_duel = record['ready_channel_duel'],
            ready_channel_dungeon = record['ready_channel_dungeon'],
            ready_channel_horse = record['ready_channel_horse'],
            ready_embed_color = record['ready_embed_color'],
            ready_other_on_top = bool(record['ready_other_on_top']),
            ready_pets_claim_active = bool(record['ready_pets_claim_active']),
            ready_pets_claim_after_every_pet = bool(record['ready_pets_claim_after_every_pet']),
            ready_up_next_as_timestamp = bool(record['ready_up_next_as_timestamp']),
            ready_up_next_show_hidden_reminders = bool(record['ready_up_next_show_hidden_reminders']),
            ready_up_next_visible = bool(record['ready_up_next_visible']),
            rubies = record['rubies'],
            ruby_counter_button_mode = bool(record['ruby_counter_button_mode']),
            ruby_counter_enabled = bool(record['ruby_counter_enabled']),
            slash_mentions_enabled = bool(record['slash_mentions_enabled']),
            time_travel_count = record['time_travel_count'],
            training_helper_button_mode = bool(record['training_helper_button_mode']),
            tracking_enabled = bool(record['tracking_enabled']),
            training_helper_enabled = bool(record['training_helper_enabled']),
            user_donor_tier = record['user_donor_tier'],
            user_id = record['user_id'],
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
    table = 'users'
    function_name = 'get_user'
    sql = f'SELECT * FROM {table} WHERE user_id=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (user_id,))
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not record:
        raise exceptions.FirstTimeUserError(f'No user data found in database for user "{user_id}".')
    user = await _dict_to_user(dict(record))

    return user


async def get_all_users() -> Tuple[User]:
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
    table = 'users'
    function_name = 'get_all_users'
    sql = f'SELECT * FROM {table}'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        raise exceptions.FirstTimeUserError(f'No user data found in database (how likely is that).')
    users = []
    for record in records:
        user = await _dict_to_user(dict(record))
        users.append(user)

    return tuple(users)


async def get_users_by_clan_name(clan_name: str) -> Tuple[User]:
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
    table = 'users'
    function_name = 'get_users_by_clan_name'
    sql = f'SELECT * FROM {table} WHERE clan_name=?'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, (clan_name,))
        records = cur.fetchall()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    if not records:
        raise exceptions.FirstTimeUserError(f'No users found for clan {clan_name} ')
    users = []
    for record in records:
        user = await _dict_to_user(dict(record))
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
    table = 'users'
    function_name = 'get_user_count'
    sql = f'SELECT COUNT(user_id) FROM {table}'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql)
        record = cur.fetchone()
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
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
        alert_boo_visible: bool
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
        alert_lootbox_enabled: bool
        alert_lootbox_message: str
        alert_lootbox_multiplier: float
        alert_lootbox_visible: bool
        alert_lottery_enabled: bool
        alert_lottery_message: str
        alert_lottery_visible: bool
        alert_not_so_mini_boss_enabled: bool
        alert_not_so_mini_boss_message: str
        alert_not_so_mini_boss_visible: bool
        alert_partner_enabled: bool
        alert_partner_message: str
        alert_party_popper_enabled: bool
        alert_party_popper_message: str
        alert_party_popper_visible: bool
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
        auto_flex_enabled: bool
        auto_flex_tip_read: bool
        auto_ready_enabled: bool
        bot_enabled: bool
        clan_name: str
        cmd_cd_visible: bool
        cmd_inventory_visible: bool
        cmd_cmd_ready_visible: bool
        cmd_slashboard_visible: bool
        christmas_area_enabled: bool
        context_helper_enabled: bool
        current_area: int
        dnd_mode_enabled: bool
        guild_quest_prompt_active: bool
        halloween_helper_enabled: bool
        hardmode_mode_enabled: bool
        heal_warning_enabled: bool
        hunt_rotation_enabled: bool
        last_adventure_mode: str
        last_farm_seed: str
        last_hunt_mode: str
        last_lootbox: str
        last_quest_command: str
        last_training_command: str
        last_tt: datetime UTC
        last_workt_command: str
        partner_channel_id: int
        partner_donor_tier: int
        partner_hunt_end_time: datetime
        partner_id: int
        partner_name: str
        pet_helper_enabled: bool
        pet_helper_icon_mode: bool
        pet_tip_read: bool
        ping_after_message: bool
        portals_as_embed: bool
        portals_spacing_enabled: bool
        reactions_enabled: bool
        ready_as_embed: bool
        ready_channel_arena: int
        ready_channel_duel: int
        ready_channel_dungeon: int
        ready_channel_horse: int
        ready_embed_color: str
        ready_pets_claim_active: bool
        ready_pets_claim_after_every_pet: bool
        ready_other_on_top: bool
        ready_up_next_as_timestamp: bool
        ready_up_next_show_hidden_reminders: bool
        ready_up_next_visible: bool
        rubies: int
        ruby_counter_button_mode: bool
        ruby_counter_enabled: bool
        slash_mentions_enabled: bool
        time_travel_count: int
        tracking_enabled: bool
        training_helper_button_mode: bool
        training_helper_enabled: bool
        user_donor_tier: int

    Raises
    ------
    sqlite3.Error if something happened within the database.
    NoArgumentsError if no kwargs are passed (need to pass at least one)
    Also logs all errors to the database.
    """
    table = 'users'
    function_name = '_update_user'
    if not kwargs:
        await errors.log_error(
            strings.INTERNAL_ERROR_NO_ARGUMENTS.format(table=table, function=function_name)
        )
        raise exceptions.NoArgumentsError('You need to specify at least one keyword argument.')
    try:
        cur = settings.NAVI_DB.cursor()
        sql = f'UPDATE {table} SET'
        for kwarg in kwargs:
            sql = f'{sql} {kwarg} = :{kwarg},'
        sql = sql.strip(",")
        kwargs['user_id'] = user.user_id
        sql = f'{sql} WHERE user_id = :user_id'
        cur.execute(sql, kwargs)
        if 'user_donor_tier' in kwargs and user.partner_id is not None:
            partner = await get_user(user.partner_id)
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
    function_name = 'insert_user'
    table = 'users'
    columns = ''
    values = [user_id,]
    for activity, default_message in strings.DEFAULT_MESSAGES.items():
        columns = f'{columns},{strings.ACTIVITIES_COLUMNS[activity]}_message'
        values.append(default_message)
    sql = f'INSERT INTO {table} (user_id{columns}) VALUES ('
    for value in values:
        sql = f'{sql}?,'
    sql = f'{sql.strip(",")})'
    try:
        cur = settings.NAVI_DB.cursor()
        cur.execute(sql, values)
    except sqlite3.Error as error:
        await errors.log_error(
            strings.INTERNAL_ERROR_SQLITE3.format(error=error, table=table, function=function_name, sql=sql)
        )
        raise
    user = await get_user(user_id)

    return user