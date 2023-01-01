# update_databae.py
"""Migrates the database to the newest version.

This file needs to be run directly. Only required when the bot tells you on startup.

BACK UP YOUR DATABASE BEFORE RUNNING THIS!
"""

import sqlite3
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
DB_FILE = CURRENT_DIR / 'navi_db.db'
NAVI_DB = sqlite3.connect(DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
NAVI_DB.row_factory = sqlite3.Row
NAVI_DB_VERSION = 2

def get_user_version() -> int:
    """Returns the current user version from the database"""
    try:
        cur = NAVI_DB.cursor()
        cur.execute('PRAGMA user_version')
        record = cur.fetchone()
        return int(dict(record)['user_version'])
    except sqlite3.Error as error:
        print(f'Unable to read database version. Error: {error}')
        raise

if __name__ == '__main__':
    cur = NAVI_DB.cursor()
    db_version = get_user_version()
    print(
        f'Current database version: {db_version}\n'
        f'Target database version: {NAVI_DB_VERSION}\n'
    )
    if db_version == NAVI_DB_VERSION:
        print('Nothing to do.')
        quit()
    user_input = input(
        f'MAKE A BACKUP OF YOUR DATABASE. You have been warned.\n'
        f'Continue update? [y/n]\n'
    )
    if user_input.lower() not in ['y','yes']:
        print('Aborted. No changes were made.')
        quit()
    print('Updating database...')

    # Recreate users table if database was never updated yet to make sure everything is as it should be
    if db_version == 0:
        cur.execute('ALTER TABLE users RENAME TO users_old')
        sql = (
            "CREATE TABLE users "
            "(user_id INTEGER UNIQUE PRIMARY KEY NOT NULL, "
            "user_donor_tier INTEGER DEFAULT (0) NOT NULL, "
            "bot_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "auto_flex_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "auto_flex_tip_read BOOLEAN NOT NULL DEFAULT (0), "
            "auto_ready_enabled BOOLEAN NOT NULL DEFAULT (0), "
            "christmas_area_enabled BOOLEAN NOT NULL DEFAULT (0), "
            "clan_name TEXT REFERENCES clans (clan_name), "
            "cmd_cd_visible BOOLEAN NOT NULL DEFAULT (0), "
            "cmd_inventory_visible BOOLEAN NOT NULL DEFAULT (0), "
            "cmd_ready_visible BOOLEAN NOT NULL DEFAULT (0), "
            "cmd_slashboard_visible BOOLEAN NOT NULL DEFAULT (0), "
            "context_helper_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "dnd_mode_enabled BOOLEAN DEFAULT (0) NOT NULL, "
            "guild_quest_prompt_active BOOLEAN NOT NULL DEFAULT (0), "
            "halloween_helper_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "hardmode_mode_enabled BOOLEAN DEFAULT (0) NOT NULL, "
            "heal_warning_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "hunt_rotation_enabled BOOLEAN NOT NULL DEFAULT (0), "
            "last_adventure_mode TEXT, "
            "last_farm_seed TEXT, "
            "last_hunt_mode TEXT, "
            "last_lootbox TEXT, "
            "last_quest_command TEXT NOT NULL DEFAULT ('quest'), "
            "last_training_command TEXT NOT NULL DEFAULT ('training'), "
            "last_tt DATETIME DEFAULT ('1970-01-01 00:00:00') NOT NULL, "
            "last_work_command TEXT, "
            "megarace_helper_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "partner_channel_id INTEGER, "
            "partner_donor_tier INTEGER DEFAULT (0) NOT NULL, "
            "partner_hunt_end_time DATETIME NOT NULL DEFAULT ('1970-01-01 00:00:00'), "
            "partner_id INTEGER, partner_name TEXT, "
            "pet_helper_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "pet_helper_icon_mode BOOLEAN NOT NULL DEFAULT (1), "
            "pet_tip_read BOOLEAN NOT NULL DEFAULT (0), "
            "ping_after_message BOOLEAN NOT NULL DEFAULT (0), "
            "reactions_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "ready_as_embed BOOLEAN NOT NULL DEFAULT (0), "
            "ready_embed_color TEXT NOT NULL DEFAULT ('000000'), "
            "ready_other_on_top BOOLEAN NOT NULL DEFAULT (0), "
            "ready_pets_claim_active BOOLEAN NOT NULL DEFAULT (0), "
            "ready_pets_claim_after_every_pet BOOLEAN NOT NULL DEFAULT (0), "
            "ready_up_next_as_timestamp BOOLEAN NOT NULL DEFAULT (0), "
            "ready_up_next_visible BOOLEAN NOT NULL DEFAULT (1), "
            "rubies INTEGER DEFAULT (0) NOT NULL, "
            "ruby_counter_button_mode BOOLEAN NOT NULL DEFAULT (1), "
            "ruby_counter_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "slash_mentions_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "time_travel_count INTEGER, "
            "tracking_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "training_helper_button_mode BOOLEAN NOT NULL DEFAULT (1), "
            "training_helper_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_advent_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_advent_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_advent_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_adventure_enabled BOOLEAN DEFAULT (True) NOT NULL, "
            "alert_adventure_message TEXT DEFAULT ('{name} Hey! It''s time for {command}!') NOT NULL, "
            "alert_adventure_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_arena_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_arena_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_arena_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_big_arena_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_big_arena_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_big_arena_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_boo_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_boo_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_boo_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_chimney_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_chimney_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_chimney_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_daily_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_daily_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_daily_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_duel_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_duel_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_duel_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_dungeon_miniboss_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_dungeon_miniboss_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_dungeon_miniboss_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_epic_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_epic_message TEXT NOT NULL DEFAULT ('{name} Hey! Your EPIC item cooldown is ready!'), "
            "alert_epic_visible BOOLEAN NOT NULL DEFAULT (0), "
            "alert_farm_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_farm_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_farm_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_guild_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_guild_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_guild_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_horse_breed_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_horse_breed_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_horse_breed_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_horse_race_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_horse_race_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_horse_race_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_hunt_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_hunt_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_hunt_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_lootbox_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_lootbox_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_lootbox_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_lottery_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_lottery_message TEXT NOT NULL DEFAULT ('{name} Hey! The lottery just finished. Use </lottery:957815874063061072> to check out who won and {command} to enter the next draw!'), "
            "alert_lottery_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_megarace_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_megarace_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_megarace_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_minirace_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_minirace_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_minirace_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_not_so_mini_boss_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_not_so_mini_boss_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_not_so_mini_boss_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_partner_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_partner_message TEXT NOT NULL DEFAULT ('{name} **{partner}** found {loot} for you!'), "
            "alert_pet_tournament_enabled BOOLEAN NOT NULL DEFAULT (1), "
            "alert_pet_tournament_message TEXT NOT NULL DEFAULT ('{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'), "
            "alert_pet_tournament_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_pets_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_pets_message TEXT NOT NULL DEFAULT ('{name} Hey! Your pet `{id}` is back! {emoji}'), "
            "alert_pets_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_quest_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_quest_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_quest_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_training_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_training_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_training_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_vote_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_vote_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_vote_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_weekly_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_weekly_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_weekly_visible BOOLEAN NOT NULL DEFAULT (1), "
            "alert_work_enabled BOOLEAN DEFAULT (1) NOT NULL, "
            "alert_work_message TEXT NOT NULL DEFAULT ('{name} Hey! It''s time for {command}!'), "
            "alert_work_visible BOOLEAN NOT NULL DEFAULT (1))"
        )
        cur.execute(sql)
        cur.execute('PRAGMA table_info(users_old)')
        columns = cur.fetchall()
        columns_sql = ''
        for column in columns:
            column = dict(column)
            columns_sql = f'{columns_sql}, {column["name"]}'
        columns_sql = columns_sql.strip(' ,')
        cur.execute(f'INSERT INTO users ({columns_sql}) SELECT {columns_sql} FROM users_old')
        cur.execute('DROP TABLE users_old')

        # Make sure all records exist in table cooldowns
        cooldowns = {
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
        for activity, cooldown_data in cooldowns.items():
            cooldown_time, donor_affected = cooldown_data
            cur.execute('SELECT cooldown, donor_affected FROM cooldowns WHERE activity = ?', (activity,))
            record = cur.fetchone()
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
    if db_version < NAVI_DB_VERSION:
        sqls = [
            'ALTER TABLE guilds ADD auto_flex_enabled BOOLEAN NOT NULL DEFAULT (0)',
            "ALTER TABLE tracking_log ADD type TEXT NOT NULL DEFAULT ('single')",
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
            "ALTER TABLE users ADD ascended BOOLEAN NOT NULL DEFAULT (1)",
            "ALTER TABLE users ADD current_area INTEGER",
        ]
        for sql in sqls:
            try:
                cur.execute(sql)
            except sqlite3.Error as error:
                if 'duplicate column name' in error.args[0]:
                    continue
                else:
                    raise
        cur.execute(f'PRAGMA user_version = {NAVI_DB_VERSION}')
    db_version = get_user_version()
    print(
        f'Updated database to version {db_version}.\n\n'
        f'Vacuuming...'
    )
    cur.execute('VACUUM')
    print(
        f'Done.\n\n'
        f'Running integrity check...'
    )
    cur.execute('PRAGMA integrity_check')
    print(f"Check result: {dict(cur.fetchone())['integrity_check']}")