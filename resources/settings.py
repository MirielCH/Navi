# settings.py
"""Contains global settings"""

import os
import sqlite3
import sys
from typing import NamedTuple

from dotenv import load_dotenv


ENV_VARIABLE_MISSING = (
    'Required setting {var} in the .env file is missing. Please check your default.env file and update your .env file '
    'accordingly.'
)


# Files and directories
BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BOT_DIR, 'database/navi_db.db')
NAVI_DB = sqlite3.connect(DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
NAVI_DB.row_factory = sqlite3.Row
LOG_FILE = os.path.join(BOT_DIR, 'logs/discord.log')
IMG_NAVI = os.path.join(BOT_DIR, 'images/navi.png')
VERSION_FILE = os.path.join(BOT_DIR, 'VERSION')


# Load .env variables
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    print(ENV_VARIABLE_MISSING.format(var='DISCORD_TOKEN'))
    sys.exit()

OWNER_ID = os.getenv('OWNER_ID')
if OWNER_ID is None:
    print(ENV_VARIABLE_MISSING.format(var='OWNER_ID'))
    sys.exit()
try:
    OWNER_ID = int(OWNER_ID)
except:
    print(f'Owner ID "{OWNER_ID}" in the .env variable OWNER_ID is not a number.')
    sys.exit()

DEBUG_MODE = True if os.getenv('DEBUG_MODE') == 'ON' else False
if DEBUG_MODE is None:
    print(ENV_VARIABLE_MISSING.format(var='DEBUG_MODE'))
    sys.exit()

DEV_IDS = os.getenv('DEV_IDS')
if DEV_IDS is None or DEV_IDS == '':
    DEV_IDS = []
else:
    DEV_IDS = DEV_IDS.split(',')
    try:
        DEV_IDS = [int(dev_id.strip()) for dev_id in DEV_IDS]
    except:
        print('At least one id in the .env variable DEV_IDS is not a number.')
        sys.exit()
DEV_IDS += [OWNER_ID,]

DEV_GUILDS = os.getenv('DEV_GUILDS')
if DEV_GUILDS is None:
    print(ENV_VARIABLE_MISSING.format(var='DEV_GUILDS'))
    sys.exit()
if DEV_GUILDS == '':
    print('Variable DEV_GUILDS in the .env file is required. Please set at least one dev guild.')
    sys.exit()
else:
    DEV_GUILDS = DEV_GUILDS.split(',')
    try:
        DEV_GUILDS = [int(guild_id.strip()) for guild_id in DEV_GUILDS]
    except:
        print('At least one id in the .env variable DEV_GUILDS is not a number.')
        sys.exit()

EMBED_COLOR = os.getenv('EMBED_COLOR')
if EMBED_COLOR is None:
    EMBED_COLOR = 0x000000
else:
    try:
        EMBED_COLOR = int(EMBED_COLOR.strip('#'), base=16)
    except:
        print(f'Can\'t convert value "{EMBED_COLOR}" of variable EMBED_COLOR in the .env file to an integer.')
        sys.exit()


# Read bot version
_version_file = open(VERSION_FILE, 'r')
VERSION = _version_file.readline().rstrip('\n')
_version_file.close()


DONOR_COOLDOWNS = (1, 0.9, 0.8, 0.65)

EPIC_RPG_ID = 555955826880413696
TESTY_ID = 1050765002950332456 # Miriel's test bot to test triggers


DEFAULT_PREFIX = 'navi '

TIMEOUT = 20
TIMEOUT_LONGER = 30
TIMEOUT_LONGEST = 40
INTERACTION_TIMEOUT = 300

class ClanReset(NamedTuple):
    """Clan Reset time. Week starts at monday, UTC"""
    weekday: int = 5
    hour: int = 21
    minute: int = 59

CLAN_DEFAULT_STEALTH_THRESHOLD = 90