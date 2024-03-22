# settings.py
"""Contains global settings"""

import os
import sqlite3
import sys
from typing import NamedTuple, TextIO

from dotenv import load_dotenv


ENV_VARIABLE_MISSING: str = (
    'Required setting {var} in the .env file is missing. Please check your default.env file and update your .env file '
    'accordingly.'
)

PYTHON_VERSION: float = 3.12
NAVI_DB_VERSION: int = 21

# Files and directories
BOT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE: str = os.path.join(BOT_DIR, 'database/navi_db.db')
if os.path.isfile(DB_FILE):
    NAVI_DB: sqlite3.Connection = sqlite3.connect(DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
else:
    print(f'Database {DB_FILE} does not exist. Please follow the setup instructions in the README first.')
    sys.exit()
NAVI_DB.row_factory = sqlite3.Row
LOG_FILE: str = os.path.join(BOT_DIR, 'logs/discord.log')
IMG_NAVI: str = os.path.join(BOT_DIR, 'images/navi.png')
_VERSION_FILE: str = os.path.join(BOT_DIR, 'VERSION')


# Load .env variables
load_dotenv()

TOKEN: str | None = os.getenv('DISCORD_TOKEN').strip('" ')
if not TOKEN:
    print(ENV_VARIABLE_MISSING.format(var='DISCORD_TOKEN'))
    sys.exit()

_env_owner_id: str | None = os.getenv('OWNER_ID').strip('" ')
if not _env_owner_id:
    print(ENV_VARIABLE_MISSING.format(var='OWNER_ID'))
    sys.exit()
try:
    OWNER_ID: int = int(_env_owner_id)
except:
    print(f'Owner ID "{_env_owner_id}" in the .env variable OWNER_ID is not a number.')
    sys.exit()

DEBUG_MODE: bool = True if os.getenv('DEBUG_MODE') == 'ON' else False
LITE_MODE: bool = True if os.getenv('LITE_MODE') == 'ON' else False

_env_dev_ids: str | None = os.getenv('DEV_IDS')
if not _env_dev_ids:
    DEV_IDS: list[int] = []
else:
    try:
        DEV_IDS: list[int] = [int(dev_id.strip('" ')) for dev_id in _env_dev_ids.split(',')]
    except Exception as error:
        print(f'{error}\nCheck the syntax of the .env variable DEV_IDS.')
        sys.exit()
DEV_IDS += [OWNER_ID,]

_env_dev_guilds: str | None = os.getenv('DEV_GUILDS')
if not _env_dev_guilds:
    print(ENV_VARIABLE_MISSING.format(var='DEV_GUILDS'))
    sys.exit()
else:
    try:
        DEV_GUILDS: list[int] = [int(guild_id.strip('" ')) for guild_id in _env_dev_guilds.split(',')]
    except Exception as error:
        print(f'{error}\nCheck the syntax of the .env variable DEV_GUILDS.')
        sys.exit()

_env_embed_color: str | None = os.getenv('EMBED_COLOR')
if not _env_embed_color:
    EMBED_COLOR: int = 0x000000
else:
    try:
        EMBED_COLOR: int = int(_env_embed_color.strip('# '), base=16)
    except:
        print(f'Can\'t convert value "{_env_embed_color}" of variable EMBED_COLOR in the .env file to an integer.')
        sys.exit()

LINK_INVITE: str | None = os.getenv('LINK_INVITE')
if LINK_INVITE:
    LINK_INVITE = LINK_INVITE.strip('" ')
else:
    LINK_INVITE = None

LINK_SUPPORT: str | None = os.getenv('LINK_SUPPORT')
if LINK_SUPPORT:
    LINK_SUPPORT = LINK_SUPPORT.strip('" ')
else:
    LINK_SUPPORT = None

LINK_PRIVACY_POLICY: str | None = os.getenv('LINK_PRIVACY_POLICY')
if LINK_PRIVACY_POLICY:
    LINK_PRIVACY_POLICY = LINK_PRIVACY_POLICY.strip('" ')
else:
    LINK_PRIVACY_POLICY = None

LINK_TERMS: str | None = os.getenv('LINK_TERMS')
if LINK_TERMS:
    LINK_TERMS = LINK_TERMS.strip('" ')
else:
    LINK_TERMS = None
    
_env_complaint_channel_id: str | None = os.getenv('COMPLAINT_CHANNEL_ID')
if _env_complaint_channel_id:
    try:
        COMPLAINT_CHANNEL_ID: int | None = int(_env_complaint_channel_id.strip('" '))
    except:
        print(f'Complain channel ID "{_env_complaint_channel_id}" in the .env variable COMPLAINT_CHANNEL_ID is not a number.')
        sys.exit()
else:
    COMPLAINT_CHANNEL_ID: int | None = None
        
_env_suggestion_channel_id: str | None = os.getenv('SUGGESTION_CHANNEL_ID')
if _env_suggestion_channel_id:
    try:
        SUGGESTION_CHANNEL_ID: int | None = int(_env_suggestion_channel_id.strip('" '))
    except:
        print(f'Suggestion channel ID "{_env_suggestion_channel_id}" in the .env variable SUGGESTION_CHANNEL_ID is not a number.')
        sys.exit()
else:
    SUGGESTION_CHANNEL_ID: int | None = None


# Read bot version
_version_file_stream: TextIO = open(_VERSION_FILE, 'r')
VERSION: str = _version_file_stream.readline().rstrip('\n')
_version_file_stream.close()


DONOR_COOLDOWNS: list[float] = (1.0, 0.9, 0.8, 0.65)

EPIC_RPG_ID: int = 555955826880413696
TESTY_ID: int = 1050765002950332456 # Miriel's test bot to test triggers


DEFAULT_PREFIX: str = 'navi '

INTERACTION_TIMEOUT: int = 300

class ClanReset(NamedTuple):
    """Clan Reset time. Week starts at monday, UTC"""
    weekday: int = 5
    hour: int = 21
    minute: int = 59

CLAN_DEFAULT_STEALTH_THRESHOLD: int = 90

CHOCOLATE_BOX_MULTIPLIER: float = 0.98
CHRISTMAS_AREA_MULTIPLIER: float = 1.0 # Set this to 0.9 during christmas event and to 1 during the rest of the year
POTION_FLASK_MULTIPLIER: float = 0.9999 # Why did I even do this
ROUND_CARD_MULTIPLIER: float = 0.1