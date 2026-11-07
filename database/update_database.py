# update_database.py
"""Updates the database to the newest version."""
import sys

if __name__ == '__main__':
    print('As of 2.39.0, the database is automatically updated on startup. Please start the bot normally.')
    sys.exit()


import os
import re
import sqlite3
from typing import Any

from resources import functions, logs, settings


def get_user_version() -> int:
    """Returns the current user version from the database"""
    try:
        cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
        cur.execute('PRAGMA user_version')
        record: Any = cur.fetchone()
        return int(dict(record)['user_version'])
    except sqlite3.Error as error:
        error_message: str = f'Unable to read database version. Error: {error}'
        print(error_message)
        logs.logger.error(f'Database: Unable to read database version. Error: {error}')
        raise

def update_database() -> bool:
    """Updates the database. Returns True if the db_version after the update equals NACVI_DB_VERSION."""
    cur: sqlite3.Cursor = settings.NAVI_DB.cursor()
    db_version: int = get_user_version()
    logs.logger.info(f'Database: Current database version: {db_version}')
    logs.logger.info(f'Database: Target database version: {settings.NAVI_DB_VERSION}')
    if db_version == settings.NAVI_DB_VERSION:
        logs.logger.info('Database Update: Nothing to do, exiting.')
        return True
    logs.logger.info('Database: Backing up database to /database/navi_db_backup.db...')
    backup_db_file: str = os.path.join(settings.BOT_DIR, 'database/navi_db_backup.db')
    navi_backup_db: sqlite3.Connection = sqlite3.connect(backup_db_file)
    settings.NAVI_DB.backup(navi_backup_db)
    navi_backup_db.close()
    logs.logger.info('Database: Starting database update...')

    # Recreate users table if database was never updated yet to make sure everything is as it should be
    if db_version == 0:
        cur.execute('ALTER TABLE users RENAME TO users_old')
        sql: tuple[str, ...] = (
            "CREATE TABLE users "
            "(user_id INTEGER UNIQUE PRIMARY KEY NOT NULL, "
            "user_donor_tier INTEGER DEFAULT (0) NOT NULL, "
            "bot_enabled INTEGER DEFAULT (1) NOT NULL, "
            "auto_flex_enabled INTEGER NOT NULL DEFAULT (1), "
            "auto_flex_tip_read INTEGER NOT NULL DEFAULT (0), "
            "auto_ready_enabled INTEGER NOT NULL DEFAULT (0), "
            "christmas_area_enabled INTEGER NOT NULL DEFAULT (0), "
            "clan_name TEXT REFERENCES clans (clan_name), "
            "cmd_cd_visible INTEGER NOT NULL DEFAULT (0), "
            "cmd_inventory_visible INTEGER NOT NULL DEFAULT (0), "
            "cmd_ready_visible INTEGER NOT NULL DEFAULT (0), "
            "cmd_slashboard_visible INTEGER NOT NULL DEFAULT (0), "
            "context_helper_enabled INTEGER NOT NULL DEFAULT (1), "
            "dnd_mode_enabled INTEGER DEFAULT (0) NOT NULL, "
            "guild_quest_prompt_active INTEGER NOT NULL DEFAULT (0), "
            "halloween_helper_enabled INTEGER NOT NULL DEFAULT (1), "
            "hardmode_mode_enabled INTEGER DEFAULT (0) NOT NULL, "
            "heal_warning_enabled INTEGER DEFAULT (1) NOT NULL, "
            "hunt_rotation_enabled INTEGER NOT NULL DEFAULT (0), "
            "last_adventure_mode TEXT, "
            "last_farm_seed TEXT, "
            "last_hunt_mode TEXT, "
            "last_lootbox TEXT, "
            "last_quest_command TEXT NOT NULL DEFAULT ('quest'), "
            "last_training_command TEXT NOT NULL DEFAULT ('training'), "
            "last_tt DATETIME DEFAULT ('1970-01-01 00:00:00') NOT NULL, "
            "last_work_command TEXT, "
            "megarace_helper_enabled INTEGER NOT NULL DEFAULT (1), "
            "partner_channel_id INTEGER, "
            "partner_donor_tier INTEGER DEFAULT (0) NOT NULL, "
            "partner_hunt_end_time DATETIME NOT NULL DEFAULT ('1970-01-01 00:00:00'), "
            "partner_id INTEGER, partner_name TEXT, "
            "pet_helper_enabled INTEGER NOT NULL DEFAULT (1), "
            "pet_helper_icon_mode INTEGER NOT NULL DEFAULT (1), "
            "pet_tip_read INTEGER NOT NULL DEFAULT (0), "
            "ping_after_message INTEGER NOT NULL DEFAULT (0), "
            "reactions_enabled INTEGER NOT NULL DEFAULT (1), "
            "ready_as_embed INTEGER NOT NULL DEFAULT (0), "
            "ready_embed_color TEXT NOT NULL DEFAULT ('000000'), "
            "ready_other_on_top INTEGER NOT NULL DEFAULT (0), "
            "ready_pets_claim_active INTEGER NOT NULL DEFAULT (0), "
            "ready_pets_claim_after_every_pet INTEGER NOT NULL DEFAULT (0), "
            "ready_up_next_as_timestamp INTEGER NOT NULL DEFAULT (0), "
            "ready_up_next_visible INTEGER NOT NULL DEFAULT (1), "
            "rubies INTEGER DEFAULT (0) NOT NULL, "
            "ruby_counter_button_mode INTEGER NOT NULL DEFAULT (1), "
            "ruby_counter_enabled INTEGER DEFAULT (1) NOT NULL, "
            "slash_mentions_enabled INTEGER NOT NULL DEFAULT (1), "
            "time_travel_count INTEGER, "
            "tracking_enabled INTEGER NOT NULL DEFAULT (1), "
            "training_helper_button_mode INTEGER NOT NULL DEFAULT (1), "
            "training_helper_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_advent_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_advent_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_advent_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_adventure_enabled INTEGER DEFAULT (True) NOT NULL, "
            "alert_adventure_message TEXT DEFAULT ('{name} Hey! It''s time for {command}!') NOT NULL, "
            "alert_adventure_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_arena_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_arena_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_arena_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_big_arena_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_big_arena_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_big_arena_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_boo_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_boo_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_boo_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_chimney_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_chimney_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_chimney_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_daily_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_daily_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_daily_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_duel_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_duel_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_duel_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_dungeon_miniboss_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_dungeon_miniboss_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_dungeon_miniboss_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_epic_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_epic_message TEXT NOT NULL DEFAULT ('{name} Hey! Your EPIC item cooldown is ready!'), "
            "alert_epic_visible INTEGER NOT NULL DEFAULT (0), "
            "alert_farm_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_farm_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_farm_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_guild_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_guild_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_guild_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_horse_breed_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_horse_breed_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_horse_breed_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_horse_race_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_horse_race_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_horse_race_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_hunt_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_hunt_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_hunt_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_lootbox_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_lootbox_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_lootbox_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_lottery_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_lottery_message TEXT NOT NULL DEFAULT ('{name} Hey! The lottery just finished. Use </lottery:957815874063061072> to check out who won and {command} to enter the next draw!'), "
            "alert_lottery_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_megarace_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_megarace_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_megarace_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_minirace_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_minirace_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_minirace_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_not_so_mini_boss_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_not_so_mini_boss_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_not_so_mini_boss_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_partner_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_partner_message TEXT NOT NULL DEFAULT ('{name} **{partner}** found {loot} for you!'), "
            "alert_pet_tournament_enabled INTEGER NOT NULL DEFAULT (1), "
            "alert_pet_tournament_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_pet_tournament_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_pets_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_pets_message TEXT NOT NULL DEFAULT ('{name} Hey! Your pet `{id}` is back! {emoji}'), "
            "alert_pets_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_quest_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_quest_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_quest_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_training_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_training_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_training_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_vote_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_vote_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_vote_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_weekly_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_weekly_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_weekly_visible INTEGER NOT NULL DEFAULT (1), "
            "alert_work_enabled INTEGER DEFAULT (1) NOT NULL, "
            "alert_work_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_work_visible INTEGER NOT NULL DEFAULT (1))"
        )
        cur.execute(sql)
        cur.execute('PRAGMA table_info(users_old)')
        columns: list[Any] = cur.fetchall()
        columns_sql: str = ''
        column: Any
        for column in columns:
            column: dict[str, str] = dict(column)
            columns_sql = f'{columns_sql}, {column["name"]}'
        columns_sql = columns_sql.strip(' ,')
        cur.execute(f'INSERT INTO users ({columns_sql}) SELECT {columns_sql} FROM users_old')
        cur.execute('DROP TABLE users_old')

        # Make sure all records exist in table cooldowns
        cooldowns: dict[str, tuple[int, int]] = {
            'adventure': (3600, 1),
            'arena': (86400, 1),
            'chimney': (10800, 0),
            'clan': (7200, 0),
            'daily': (85800, 0),
            'duel': (7200, 0),
            'dungeon-miniboss': (43200, 1),
            'epic': (1800, 0),
            'farm': (600, 1),
            'horse': (86400, 1),
            'hunt': (60, 1),
            'lootbox': (10800, 0),
            'quest': (21600, 1),
            'quest-decline': (3600, 1),
            'training': (900, 1),
            'weekly': (604200, 0),
            'work': (300, 1),
        }
        activity: str
        cooldown_data: tuple[int, int]
        for activity, cooldown_data in cooldowns.items():
            cooldown_time: int
            donor_affected: int
            cooldown_time, donor_affected = cooldown_data
            cur.execute('SELECT cooldown, donor_affected FROM cooldowns WHERE activity = ?', (activity,))
            record: Any = cur.fetchone()
            if record:
                record = dict(record)
                if cooldown_time != int(record['cooldown']) or donor_affected != int(record['donor_affected']):
                    cur.execute(
                        'UPDATE cooldowns SET cooldown = ?, donor_affected = ? WHERE activity = ?',
                        (cooldown_time, donor_affected, activity)
                    )
            else:
                cur.execute(
                    'INSERT INTO cooldowns (activity, cooldown, donor_affected) VALUES (?, ?, ?)',
                    (activity, cooldown_time, donor_affected)
                )

    # Update database with new stuff added in later versions.
    sqls: list[str] = []
    if db_version < 1:
        sqls += [
            'ALTER TABLE guilds ADD auto_flex_enabled INTEGER NOT NULL DEFAULT (0)',
            "ALTER TABLE tracking_log ADD type TEXT NOT NULL DEFAULT ('single')",
        ]

    if db_version < 2:
        sqls += [
            "ALTER TABLE users ADD alert_adventure_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_chimney_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_daily_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_duel_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_epic_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_farm_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_hunt_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_lootbox_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_quest_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_training_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_weekly_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_work_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD ascended INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD current_area INTEGER",
        ]

    if db_version < 3:
        sqls += [
            "ALTER TABLE users ADD alert_party_popper_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_party_popper_message TEXT NOT NULL DEFAULT ('{name} Hey! Your party popper just ran out!')",
            "ALTER TABLE users ADD alert_party_popper_visible INTEGER NOT NULL DEFAULT (0)",
        ]

    if db_version < 4:
        sqls += [
            "CREATE TABLE users_portals (sort_index INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "user_id INTEGER NOT NULL, channel_id INTEGER NOT NULL)",
            "CREATE UNIQUE INDEX user_channel ON users_portals (user_id, channel_id)",
            "ALTER TABLE users ADD portals_as_embed INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD portals_spacing_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD ready_up_next_show_hidden_reminders INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD ready_channel_arena INTEGER",
            "ALTER TABLE users ADD ready_channel_duel INTEGER",
            "ALTER TABLE users ADD ready_channel_dungeon INTEGER",
            "ALTER TABLE users ADD ready_channel_horse INTEGER",
        ]

    if db_version < 5:
        sqls += [
            "ALTER TABLE users ADD ready_after_all_commands INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD alert_boosts_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_boosts_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! Your {boost_emoji} **{boost_item}** just ran out!')",
            "ALTER TABLE users ADD alert_boosts_visible INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD farm_helper_mode INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_bread INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_carrot INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_seed_bread INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_seed_carrot INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_seed_potato INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD inventory_potato INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD potion_dragon_breath_active INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD auto_flex_brew_electronical_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_epic_berry_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_coinflip_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_enchant_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_farm_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_heal_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_lb_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_event_training_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_forge_cookie_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_hal_boo_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_edgy_ultra_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_godly_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_godly_tt_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_omega_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_omega_ultra_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_party_popper_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_lb_void_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_pets_catch_epic_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_pets_catch_tt_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_pets_claim_omega_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_pr_ascension_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_mob_drops_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_time_travel_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_hyperlog_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_ultimatelog_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_ultralog_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_superfish_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_watermelon_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_xmas_chimney_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_xmas_godly_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_xmas_snowball_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_xmas_void_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users RENAME COLUMN rubies TO inventory_ruby",
        ]

        # Update default event messages
        default_message_event_old: str = (
            '{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the '
            f'official EPIC RPG server.'
        )
        default_message_event_new: str = (
            '{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485>.'
        )
        cur.execute('SELECT * FROM users')
        all_users: list[Any] = cur.fetchall()
        if all_users:
            user: Any
            for user in all_users:
                user = dict(user)
                new_values: dict[str, str] = {}
                column: str
                value: str
                for column, value in user.items():
                    if value == default_message_event_old:
                        new_values[column] = default_message_event_new
                if new_values:
                    sql: str = f'UPDATE users SET'
                    for value in new_values:
                        sql = f'{sql} {value} = :{value},'
                    sql = sql.strip(",")
                    new_values['user_id'] = user['user_id']
                    sql = f'{sql} WHERE user_id = :user_id'
                    cur.execute(sql, new_values)

    if db_version < 6:
        sqls += [
            "ALTER TABLE guilds ADD auto_flex_lb_a18_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_epicberry_enabled INTEGER NOT NULL DEFAULT (1)",
        ]

    if db_version < 7:
        sqls += [
            "CREATE TABLE alts (sort_index INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
            "user1_id INTEGER NOT NULL, user2_id INTEGER NOT NULL)",
            "CREATE UNIQUE INDEX users_unique ON alts (user1_id, user2_id)",
            "ALTER TABLE users ADD reminder_channel_id INTEGER",
        ]

    if db_version < 8:
        sqls += [
            "ALTER TABLE users ADD user_pocket_watch_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD partner_alert_threshold INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD partner_pocket_watch_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD ready_ping_user INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD auto_flex_artifacts_enabled INTEGER NOT NULL DEFAULT (1)",
        ]

    if db_version < 9:
        sqls += [
            "ALTER TABLE users ADD alert_cel_dailyquest_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_cel_dailyquest_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_cel_dailyquest_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_cel_multiply_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_cel_multiply_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_cel_multiply_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_cel_sacrifice_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_cel_sacrifice_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_cel_sacrifice_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_maintenance_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_maintenance_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! Maintenance is over!')",
            "ALTER TABLE users ADD alert_maintenance_visible INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 10:
        sqls += [
            "ALTER TABLE users ADD top_hat_unlocked INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD trade_daily_done INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD trade_daily_total INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD ready_trade_daily_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD ready_trade_daily_completed_visible INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 11:
        sqls += [
            "ALTER TABLE guilds ADD auto_flex_card_slots_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_card_drop_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 12:
        sqls += [
            "ALTER TABLE guilds ADD auto_flex_xmas_eternal_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_eternal_present_enabled INTEGER DEFAULT (1) NOT NULL",
            "ALTER TABLE users ADD alert_eternal_present_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time to {command} your ETERNAL presents! Make sure you open all of them in **one** command!')",
            "ALTER TABLE users ADD alert_eternal_present_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD inventory_present_eternal INTEGER NOT NULL DEFAULT (0)",
        ]
    if db_version < 13:
        sqls += [
            "ALTER TABLE users ADD auto_flex_ping_enabled INTEGER DEFAULT (0) NOT NULL",
        ]
    if db_version < 14:
        sqls += [
            "ALTER TABLE users ADD alert_card_hand_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_card_hand_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_card_hand_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD round_card_active INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD potion_flask_active INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD auto_flex_card_hand_enabled INTEGER NOT NULL DEFAULT (1)",
            "INSERT INTO cooldowns (activity, cooldown, donor_affected) VALUES ('card-hand', 86400, 0)",
        ]
    if db_version < 15:
        sqls += [
            "ALTER TABLE users ADD alert_card_hand_multiplier REAL NOT NULL DEFAULT (1)",
        ]
    if db_version < 16:
        sqls += [
            "ALTER TABLE users ADD chocolate_box_unlocked INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD partner_chocolate_box_unlocked INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD alert_epic_shop_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_epic_shop_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! The {epic_shop_emoji} **{epic_shop_item}** is back on sale in the {command}!')",
            "ALTER TABLE users ADD alert_epic_shop_visible INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 17:
        sqls += [
            "ALTER TABLE users ADD alert_love_share_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_love_share_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_love_share_visible INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 18:
        sqls += [
            "UPDATE cooldowns SET donor_affected = 1 WHERE activity = 'card-hand'",
        ]
    if db_version < 19:
        sqls += [
            "ALTER TABLE users ADD area_20_cooldowns_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 20:
        sqls += [
            "ALTER TABLE users ADD time_potion_warning_enabled INTEGER NOT NULL DEFAULT (0)",
        ]
    if db_version < 21:
        sqls += [
            "ALTER TABLE users ADD auto_healing_active INTEGER NOT NULL DEFAULT (0)",
        ]
    if db_version < 22:
        sqls += [
            "ALTER TABLE users ADD multiplier_management_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_boo_multiplier REAL NOT NULL DEFAULT (1)",
        ]
    if db_version < 23:
        sqls += [
            "ALTER TABLE guilds ADD auto_flex_lb_eternal_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
    if db_version < 24:
        sqls += [
            "ALTER TABLE users ADD alert_hunt_partner_enabled INTEGER DEFAULT (1) NOT NULL",
            "ALTER TABLE users ADD alert_hunt_partner_message TEXT NOT NULL DEFAULT ('{name} Hey! Your partner **{partner}** is ready to {command}!')",
            "ALTER TABLE users ADD alert_hunt_partner_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_hunt_partner_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD hunt_reminders_combined INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE users ADD hunt_end_time DATETIME NOT NULL DEFAULT ('1970-01-01 00:00:00')",
            "ALTER TABLE guilds ADD event_arena_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_arena_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `JOIN` to get some cookies!')",
            "ALTER TABLE guilds ADD event_coin_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_coin_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `CATCH` to get some coins!')",
            "ALTER TABLE guilds ADD event_fish_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_fish_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `LURE` to get some fish!')",
            "ALTER TABLE guilds ADD event_legendary_boss_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_legendary_boss_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `TIME TO FIGHT` to kill a dragon!')",
            "ALTER TABLE guilds ADD event_log_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_log_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `CUT` to get some logs!')",
            "ALTER TABLE guilds ADD event_lootbox_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_lootbox_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `SUMMON` to get a lootbox!')",
            "ALTER TABLE guilds ADD event_miniboss_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_miniboss_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `FIGHT` to get some coins!')",
        ]
    if db_version < 25:
        sqls += [
            "ALTER TABLE guilds ADD auto_flex_card_golden_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
        cur.execute("SELECT * FROM settings WHERE name = 'seasonal_event'")
        record: Any = cur.fetchone()
        if not record:
            sqls += [
                "INSERT INTO settings (name, value) VALUES ('seasonal_event', 'none')",
            ]
    if db_version < 26:
        sqls += [
            "ALTER TABLE guilds ADD event_rare_hunt_monster_enabled INTEGER NOT NULL DEFAULT (0)",
            "ALTER TABLE guilds ADD event_rare_hunt_monster_message TEXT NOT NULL DEFAULT ('@here Hey! Click or type `LETS GET THAT PICKAXE` to get an artifact part!')",
            "ALTER TABLE users ADD eternal_boosts_tier INTEGER DEFAULT (0) NOT NULL",
        ]
    if db_version < 27:
        sqls += [
            "ALTER TABLE users ADD alert_eternity_sealing_enabled INTEGER DEFAULT (1) NOT NULL",
            "ALTER TABLE users ADD alert_eternity_sealing_message TEXT NOT NULL DEFAULT ('{name} Hey! The eternity just sealed itself!')",
            "ALTER TABLE users ADD ready_eternity_visible INTEGER DEFAULT (1) NOT NULL",
        ]

    if db_version < 28:

        # Create new clan members table
        cur.execute(
            "CREATE TABLE IF NOT EXISTS clan_members (user_id INTEGER NOT NULL, clan_name TEXT NOT NULL, member_type TEXT NOT NULL)",
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS user_id_unique ON clan_members (user_id)",
        )

        # Migrate old clan member columns to new table
        cur.execute("SELECT * FROM clans")
        records: list[Any] = cur.fetchall()
        record: Any
        old_columns_found: bool = False
        for record in records:
            record_dict: dict[str, Any] = dict(record)
            if 'member1_id' not in record_dict: break
            old_columns_found = True
            member_ids: list[int] = [
                record_dict['leader_id'],
                record_dict['member1_id'],
                record_dict['member2_id'],
                record_dict['member3_id'],
                record_dict['member4_id'],
                record_dict['member5_id'],
                record_dict['member6_id'],
                record_dict['member7_id'],
                record_dict['member8_id'],
                record_dict['member9_id'],
                record_dict['member10_id'],
            ]
            member_ids_unique: list[int] = []
            member_id: int
            for member_id in member_ids:
                if member_id not in member_ids_unique and member_id is not None:
                    member_ids_unique.append(member_id)
            index: int
            for index, member_id in enumerate(member_ids_unique):
                member_type: str = 'leader' if index == 0 else 'member'
                cur.execute(f"SELECT * FROM clan_members WHERE user_id = ?", (member_id,))
                record_member: Any = cur.fetchone()
                if record_member:
                    cur.execute(f"UPDATE clan_members SET clan_name = ?, member_type = ? WHERE user_id = ?",
                                (record_dict['clan_name'], member_type, member_id))
                else:
                    cur.execute(f"INSERT INTO clan_members (clan_name, user_id, member_type) VALUES (?, ?, ?)",
                                (record_dict['clan_name'], member_id, member_type))
            cur.execute('UPDATE clans SET leader_id = NULL WHERE clan_name = ?', (record_dict['clan_name'],))

        if old_columns_found:
            cur.execute('ALTER TABLE clans DROP COLUMN member1_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member2_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member3_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member4_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member5_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member6_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member7_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member8_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member9_id')
            cur.execute('ALTER TABLE clans DROP COLUMN member10_id')

        # Remove column clan_name in users
        sqls += [
            "ALTER TABLE users DROP COLUMN clan_name",
        ]
        
    if db_version < 29:
        sqls += [
            "ALTER TABLE users ADD alert_color_tournament_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_color_tournament_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_color_tournament_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_color_tournament_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_surf_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_surf_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_surf_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_surf_visible INTEGER NOT NULL DEFAULT (1)",
            "INSERT INTO cooldowns (activity, cooldown, donor_affected) VALUES ('surf', 14400, 0)",
        ]
        
    if db_version < 30:
        sqls += [
            "ALTER TABLE users ADD surf_helper_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
        
    if db_version < 31:
        sqls += [
            "ALTER TABLE users ADD alert_produce_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_produce_message TEXT NOT NULL DEFAULT "
            "('{name} Hey! It''s time for {command}!')",
            "ALTER TABLE users ADD alert_produce_multiplier REAL NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_produce_visible INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD alert_produce_unlocked INTEGER NOT NULL DEFAULT (0)",
            "INSERT INTO cooldowns (activity, cooldown, donor_affected) VALUES ('produce', 1800, 1)",
            "ALTER TABLE guilds ADD auto_flex_lb_galaxy_enabled INTEGER NOT NULL DEFAULT (1)",
            "ALTER TABLE guilds ADD auto_flex_work_walkingnormiefish_enabled INTEGER NOT NULL DEFAULT (1)",
        ]
    
    # Run SQLs to make sure db is at version 31 at this point before the big one
    sql: str
    for sql in sqls:
        try:
            cur.execute(sql)
        except sqlite3.Error as error:
            error_msg: str = error.args[0].lower()
            if 'duplicate column name' in error_msg:
                continue
            elif 'no such column' in error_msg:
                continue
            elif 'cooldowns.activity' in error_msg:
                continue
            else:
                raise
    sqls = []

    if db_version <32:
        """Encrypt and/or hash all API data"""
        try:
            settings.NAVI_DB.create_function("uid_hash", 1, lambda value: functions.create_hash(value))
            settings.NAVI_DB.create_function("uid_token", 1, lambda value: functions.encrypt(value))
            
            db_create_users_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()[0]
            db_create_alts_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='alts'").fetchone()[0]
            db_create_clan_members_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='clan_members'").fetchone()[0]
            db_create_clans_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='clans'").fetchone()[0]
            db_create_clans_raids_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='clans_raids'").fetchone()[0]
            db_create_errors_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='errors'").fetchone()[0]
            db_create_guilds_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='guilds'").fetchone()[0]
            db_create_reminders_clans_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reminders_clans'").fetchone()[0]
            db_create_reminders_users_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reminders_users'").fetchone()[0]
            db_create_tracking_log_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tracking_log'").fetchone()[0]
            db_create_users_portals_sql = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users_portals'").fetchone()[0]
            
            db_extras_users = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='users' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_alts = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='alts' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_clan_members = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='clan_members' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_clans = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='clans' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_clans_raids = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='clans_raids' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_errors = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='errors' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_guilds = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='guilds' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_reminders_clans = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='reminders_clans' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_reminders_users = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='reminders_users' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_tracking_log = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='tracking_log' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db_extras_users_portals = [record[0] for record in cur.execute("SELECT sql FROM sqlite_master WHERE tbl_name='users_portals' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            
            db_columns_users = [record[1] for record in cur.execute("PRAGMA table_info(users)")]
            db_columns_guilds = [record[1] for record in cur.execute("PRAGMA table_info(guilds)")]

            cur.execute("PRAGMA foreign_keys=OFF")
            cur.execute("BEGIN")
            
            # Migrate table "users"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE users_new', db_create_users_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b.+?\b,', 'user_id_hash TEXT UNIQUE PRIMARY KEY NOT NULL, user_id_token BLOB NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1:
                raise Exception("Column user_id not found in table 'users', check db_create_users_sql")
            new_sql, number_of_replacements = re.subn(r'\bpartner_id\b.+?\b,', 'partner_id_hash TEXT, partner_id_token BLOB,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1:
                raise Exception("Column partner_id not found in table 'users', check db_create_users_sql")
            new_sql, number_of_replacements = re.subn(r'\bpartner_channel_id\b.+?\b,', 'partner_channel_id_token BLOB,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1:
                raise Exception("Column partner_channel_id not found in table 'users', check db_create_users_sql")
            new_sql, number_of_replacements = re.subn(r'\bpartner_name\b.+?\b,', 'partner_name_token BLOB,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1:
                raise Exception("Column partner_name not found in table 'users', check db_create_users_sql")
            new_sql, number_of_replacements = re.subn(r'\breminder_channel_id\b.+?\b,', 'reminder_channel_id_token BLOB,',
                                                    new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1:
                raise Exception("Column reminder_channel_id not found in table 'users', check db_create_users_sql")
            cur.execute(new_sql)
            insert_columns = (
                ", ".join(column for column in db_columns_users)
                .replace('user_id,', 'user_id_hash, user_id_token,')
                .replace('partner_id,', 'partner_id_hash, partner_id_token,')
                .replace('partner_channel_id,', 'partner_channel_id_token,')
                .replace('partner_name,', 'partner_name_token,')
                .replace('reminder_channel_id,', 'reminder_channel_id_token,')
            )
            select_columns = (
                ", ".join(column for column in db_columns_users)
                .replace('user_id,', 'uid_hash(user_id), uid_token(user_id),')
                .replace('partner_id,', 'uid_hash(partner_id), uid_token(partner_id),')
                .replace('partner_channel_id,', 'uid_token(partner_channel_id),')
                .replace('partner_name,', 'uid_token(partner_name),')
                .replace('reminder_channel_id,', 'uid_token(reminder_channel_id),')
            )
            cur.execute(f"INSERT INTO users_new ({insert_columns}) SELECT {select_columns} FROM users")
            record_count_old = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM users_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old users, but only migrated {record_count_new} users.")
            cur.execute("DROP TABLE users")
            cur.execute("ALTER TABLE users_new RENAME TO users")
            for sql in db_extras_users:
                cur.execute(sql.replace('user_id', 'user_id_hash'))

            # Migrate table "alts"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE alts_new', db_create_alts_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser1_id\b.+?\b,', 'user1_id_hash TEXT NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user1_id not found in table 'alts', check db_create_alts_sql")
            new_sql, number_of_replacements = re.subn(r'\buser2_id\b\s+\bINTEGER\b\s+\bNOT\b\s+\bNULL\b', 'user2_id_hash TEXT NOT NULL',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user2_id not found in table 'alts', check db_create_alts_sql")
            cur.execute(new_sql)
            insert_columns = "user1_id_hash, user2_id_hash, sort_index"
            select_columns = "uid_hash(user1_id), uid_hash(user2_id), sort_index"
            cur.execute(f"INSERT INTO alts_new ({insert_columns}) SELECT {select_columns} FROM alts")
            record_count_old = cur.execute("SELECT COUNT(*) FROM alts").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM alts_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old alts, but only migrated {record_count_new} alts.")
            cur.execute("DROP TABLE alts")
            cur.execute("ALTER TABLE alts_new RENAME TO alts")
            for sql in db_extras_alts:
                cur.execute(sql.replace('user1_id', 'user1_id_hash').replace('user2_id', 'user2_id_hash'))
                
            # Migrate table "clan_members"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE clan_members_new', db_create_clan_members_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b.+?\b,', 'user_id_hash TEXT NOT NULL, user_id_token BLOB NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'clan_members', check db_create_clan_members_sql")
            cur.execute(new_sql)
            insert_columns = "user_id_hash, user_id_token, clan_name, member_type"
            select_columns = "uid_hash(user_id), uid_token(user_id), clan_name, member_type"
            cur.execute(f"INSERT INTO clan_members_new ({insert_columns}) SELECT {select_columns} FROM clan_members")
            record_count_old = cur.execute("SELECT COUNT(*) FROM clan_members").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM clan_members_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old clan_members, but only migrated {record_count_new} clan_members.")
            cur.execute("DROP TABLE clan_members")
            cur.execute("ALTER TABLE clan_members_new RENAME TO clan_members")
            for sql in db_extras_clan_members:
                cur.execute(sql.replace('user_id', 'user_id_hash'))
                
            # Migrate table "clans"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE clans_new', db_create_clans_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\bleader_id\b.+?\b,', '',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column leader_id not found in table 'clans', check db_create_clans_sql")
            new_sql, number_of_replacements = re.subn(r'\bchannel_id\b.+?\b,', 'channel_id_token BLOB,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column channel_id not found in table 'clans', check db_create_clans_sql")
            new_sql, number_of_replacements = re.subn(r'\bquest_user_id\b.+?\b,', 'quest_user_id_token BLOB,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column quest_user_id not found in table 'clans', check db_create_clans_sql")
            cur.execute(new_sql)
            insert_columns = ("clan_name, alert_enabled, alert_message, channel_id_token, stealth_current, stealth_threshold, "
                            "quest_user_id_token, upgrade_quests_enabled, alert_visible")
            select_columns = ("clan_name, alert_enabled, alert_message, uid_token(channel_id), stealth_current, stealth_threshold, "
                            "uid_token(quest_user_id), upgrade_quests_enabled, alert_visible")
            cur.execute(f"INSERT INTO clans_new ({insert_columns}) SELECT {select_columns} FROM clans")
            record_count_old = cur.execute("SELECT COUNT(*) FROM clans").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM clans_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old clans, but only migrated {record_count_new} clans.")
            cur.execute("DROP TABLE clans")
            cur.execute("ALTER TABLE clans_new RENAME TO clans")
            for sql in db_extras_clans:
                cur.execute(sql.replace('user_id', 'user_id_hash'))
                
            # Migrate table "clans_raids"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE clans_raids_new', db_create_clans_raids_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b.+?\b,', 'user_id_hash TEXT NOT NULL, user_id_token BLOB NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'clans_raids', check db_create_clans_raids_sql")
            cur.execute(new_sql)
            insert_columns = "clan_name, user_id_hash, user_id_token, energy, raid_time"
            select_columns = "clan_name, uid_hash(user_id), uid_token(user_id), energy, raid_time"
            cur.execute(f"INSERT INTO clans_raids_new ({insert_columns}) SELECT {select_columns} FROM clans_raids")
            record_count_old = cur.execute("SELECT COUNT(*) FROM clans_raids").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM clans_raids_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old clans_raids, but only migrated {record_count_new} clans_raids.")
            cur.execute("DROP TABLE clans_raids")
            cur.execute("ALTER TABLE clans_raids_new RENAME TO clans_raids")
            for sql in db_extras_clans_raids:
                cur.execute(sql.replace('user_id', 'user_id_hash'))
                
            # Migrate table "errors"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE errors_new', db_create_errors_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\bjump_url\b\s+\bTEXT\b', 'jump_url_token BLOB',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column jump_url not found in table 'errors', check db_create_errors_sql")
            cur.execute(new_sql)
            insert_columns = "date_time, error, jump_url_token"
            select_columns = "date_time, error, uid_token(jump_url)"
            cur.execute(f"INSERT INTO errors_new ({insert_columns}) SELECT {select_columns} FROM errors")
            record_count_old = cur.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM errors_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old errors, but only migrated {record_count_new} errors.")
            cur.execute("DROP TABLE errors")
            cur.execute("ALTER TABLE errors_new RENAME TO errors")
            for sql in db_extras_errors:
                cur.execute(sql)

            # Migrate table "guilds"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE guilds_new', db_create_guilds_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\bguild_id\b.+?\b,', 'guild_id_hash TEXT UNIQUE PRIMARY KEY,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column guild_id not found in table 'guilds', check db_create_guilds_sql")
            cur.execute(new_sql)
            insert_columns = ", ".join(column for column in db_columns_guilds).replace('guild_id,', 'guild_id_hash,').replace('prefix,','')
            select_columns = ", ".join(column for column in db_columns_guilds).replace('guild_id,', 'uid_hash(guild_id),').replace('prefix,','')
            cur.execute(f"INSERT INTO guilds_new ({insert_columns}) SELECT {select_columns} FROM guilds")
            record_count_old = cur.execute("SELECT COUNT(*) FROM guilds").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM guilds_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old guilds, but only migrated {record_count_new} guilds.")
            cur.execute("DROP TABLE guilds")
            cur.execute("ALTER TABLE guilds_new RENAME TO guilds")
            for sql in db_extras_guilds:
                cur.execute(sql.replace('guild_id', 'guild_id_hash'))
                
            # Migrate table "reminders_clans"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE reminders_clans_new', db_create_reminders_clans_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\bchannel_id\b.+?\b,', 'channel_id_token BLOB NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column channel_id not found in table 'reminders_clans', check db_create_reminders_clans_sql")
            cur.execute(new_sql)
            insert_columns = "clan_name, activity, channel_id_token, end_time, message, triggered"
            select_columns = "clan_name, activity, uid_token(channel_id), end_time, message, triggered"
            cur.execute(f"INSERT INTO reminders_clans_new ({insert_columns}) SELECT {select_columns} FROM reminders_clans")
            record_count_old = cur.execute("SELECT COUNT(*) FROM reminders_clans").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM reminders_clans_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old reminders_clans, but only migrated {record_count_new} reminders_clans.")
            cur.execute("DROP TABLE reminders_clans")
            cur.execute("ALTER TABLE reminders_clans_new RENAME TO reminders_clans")
            for sql in db_extras_reminders_clans:
                cur.execute(sql)
                
            # Migrate table "reminders_users"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE reminders_users_new', db_create_reminders_users_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b\s+\bINTEGER\b', 'user_id_hash TEXT',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'reminders_users', check db_create_reminders_users_sql")
            new_sql, number_of_replacements = re.subn(r'user_id,', 'user_id_hash,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'reminders_users', check db_create_reminders_users_sql")
            new_sql, number_of_replacements = re.subn(r'\bchannel_id\b.+?\b,', 'channel_id_token BLOB NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column channel_id not found in table 'reminders_users', check db_create_reminders_users_sql")
            cur.execute(new_sql)
            insert_columns = "user_id_hash, activity, channel_id_token, end_time, message, triggered, custom_id, pet_id"
            select_columns = "uid_hash(user_id), activity, uid_token(channel_id), end_time, message, triggered, custom_id, pet_id"
            cur.execute(f"INSERT INTO reminders_users_new ({insert_columns}) SELECT {select_columns} FROM reminders_users")
            record_count_old = cur.execute("SELECT COUNT(*) FROM reminders_users").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM reminders_users_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old reminders_users, but only migrated {record_count_new} reminders_users.")
            cur.execute("DROP TABLE reminders_users")
            cur.execute("ALTER TABLE reminders_users_new RENAME TO reminders_users")
            for sql in db_extras_reminders_users:
                cur.execute(sql.replace('user_id', 'user_id_hash'))

            # Migrate table "tracking_log"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE tracking_log_new', db_create_tracking_log_sql, flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b.+?\b,', 'user_id_hash TEXT NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'tracking_log', check db_create_tracking_log_sql")
            new_sql, number_of_replacements = re.subn(r'\bguild_id\b.+?\b,', '',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column guild_id not found in table 'tracking_log', check db_create_tracking_log_sql")
            cur.execute(new_sql)
            insert_columns = "user_id_hash, command, command_count, date_time, type"
            select_columns = "uid_hash(user_id), command, command_count, date_time, type"
            cur.execute(f"INSERT INTO tracking_log_new ({insert_columns}) SELECT {select_columns} FROM tracking_log")
            record_count_old = cur.execute("SELECT COUNT(*) FROM tracking_log").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM tracking_log_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old tracking_logs, but only migrated {record_count_new} tracking_logs.")
            cur.execute("DROP TABLE tracking_log")
            cur.execute("ALTER TABLE tracking_log_new RENAME TO tracking_log")
            for sql in db_extras_tracking_log:
                cur.execute(sql.replace('user_id', 'user_id_hash'))
                
            # Migrate table "users_portals"
            new_sql = re.sub(r'^CREATE TABLE\s+\S+', 'CREATE TABLE users_portals_new', db_create_users_portals_sql.replace("'",""), flags=re.IGNORECASE)
            new_sql, number_of_replacements = re.subn(r'\buser_id\b.+?\b,', 'user_id_hash TEXT NOT NULL,',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column user_id not found in table 'users_portals', check db_create_users_portals_sql")
            new_sql, number_of_replacements = re.subn(r'\bchannel_id\b\s+\bINTEGER\b\s+\bNOT\b\s+\bNULL\b', 'channel_id_hash TEXT NOT NULL, channel_id_token BLOB NOT NULL',
                                                            new_sql, flags=re.IGNORECASE)
            if number_of_replacements != 1: 
                raise Exception("Column channel_id not found in table 'users_portals', check db_create_users_portals_sql")
            cur.execute(new_sql)
            insert_columns = "user_id_hash, channel_id_hash, channel_id_token, sort_index"
            select_columns = "uid_hash(user_id), uid_hash(channel_id), uid_token(channel_id), sort_index"
            cur.execute(f"INSERT INTO users_portals_new ({insert_columns}) SELECT {select_columns} FROM users_portals")
            record_count_old = cur.execute("SELECT COUNT(*) FROM users_portals").fetchone()[0]
            record_count_new = cur.execute("SELECT COUNT(*) FROM users_portals_new").fetchone()[0]
            if record_count_old != record_count_new:
                raise Exception(f"Row count mismatch: Found {record_count_old} old users_portals, but only migrated {record_count_new} users_portals.")
            cur.execute("DROP TABLE users_portals")
            cur.execute("ALTER TABLE users_portals_new RENAME TO users_portals")
            for sql in db_extras_users_portals:
                cur.execute(sql.replace('user_id', 'user_id_hash').replace('channel_id', 'channel_id_hash'))

            # Drop table "tracking_leaderboard" which was never used for anything
            cur.execute("DROP TABLE IF EXISTS tracking_leaderboard")
        
            # Check for forgein key errors
            foreign_key_errors = cur.execute("PRAGMA foreign_key_check").fetchall()
            assert not foreign_key_errors, f"foreign key violations: {foreign_key_errors[:5]}"

            # Commit
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
        finally:            
            cur.execute("PRAGMA foreign_keys=ON")

    # Run all SQLs since version 32
    for sql in sqls:
        try:
            cur.execute(sql)
        except sqlite3.Error as error:
            error_msg: str = error.args[0].lower()
            if 'duplicate column name' in error_msg:
                continue
            elif 'no such column' in error_msg:
                continue
            elif 'cooldowns.activity' in error_msg:
                continue
            else:
                raise

    # Set DB version, vaccum, integrity check
    cur.execute(f'PRAGMA user_version = {settings.NAVI_DB_VERSION}')
    db_version = get_user_version()
    logs.logger.info(f'Database: Updated database to version {db_version}.')
    logs.logger.info('Database: Vacuuming...')
    cur.execute('VACUUM')
    logs.logger.info('Database: Running integrity check...')
    cur.execute('PRAGMA integrity_check')
    logs.logger.info(f"Database: Check result: {dict(cur.fetchone())['integrity_check']}")

    return db_version == settings.NAVI_DB_VERSION