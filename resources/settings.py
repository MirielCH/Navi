# settings.py
"""Contains global settings"""

import os
import sqlite3
from typing import NamedTuple

from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = True if os.getenv('DEBUG_MODE') == 'ON' else False

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BOT_DIR, 'database/navi_db.db')

NAVI_DB = sqlite3.connect(DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
NAVI_DB.row_factory = sqlite3.Row

LOG_FILE = os.path.join(BOT_DIR, 'logs/discord.log')

DONOR_COOLDOWNS = (1, 0.9, 0.8, 0.65)

EPIC_RPG_ID = 555955826880413696

DEV_GUILDS = [730115558766411857,812650049565753355] # Secret Valley, Charivari

EMBED_COLOR = 0x3abad3

DEFAULT_PREFIX = 'navi '
DEFAULT_FOOTER = 'Hey! Listen!'

TIMEOUT = 20
TIMEOUT_LONGER = 30
TIMEOUT_LONGEST = 40
INTERACTION_TIMEOUT = 60

class ClanReset(NamedTuple):
    """Clan Reset time. Week starts at monday, UTC"""
    weekday: int = 5
    hour: int = 21
    minute: int = 59

CLAN_DEFAULT_STEALTH_THRESHOLD = 90