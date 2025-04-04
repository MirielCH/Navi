# settings.py
"""Contains global settings"""

import os
import sqlite3
import sys
from typing import Final, NamedTuple, TextIO

from dotenv import load_dotenv



ENV_VARIABLE_MISSING: Final[str] = (
    'Required setting {var} in the .env file is missing. Please check your default.env file and update your .env file '
    'accordingly.'
)

PYTHON_VERSION: Final[float] = 3.12
NAVI_DB_VERSION: Final[int] = 27

# Files and directories
BOT_DIR: Final[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE: Final[str] = os.path.join(BOT_DIR, 'database/navi_db.db')
if os.path.isfile(DB_FILE):
    NAVI_DB: Final[sqlite3.Connection] = sqlite3.connect(DB_FILE, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
else:
    print(f'Database {DB_FILE} does not exist. Please follow the setup instructions in the README first.')
    sys.exit()
NAVI_DB.row_factory = sqlite3.Row
LOG_FILE: Final[str] = os.path.join(BOT_DIR, 'logs/discord.log')
IMG_NAVI: Final[str] = os.path.join(BOT_DIR, 'images/navi.png')
_VERSION_FILE: Final[str] = os.path.join(BOT_DIR, 'VERSION')


# Load .env variables
load_dotenv()

TOKEN: Final[str | None] = os.getenv('DISCORD_TOKEN').strip('" ')
if not TOKEN:
    print(ENV_VARIABLE_MISSING.format(var='DISCORD_TOKEN'))
    sys.exit()

_owner_id_env: str | None = os.getenv('OWNER_ID').strip('" ')
if not _owner_id_env:
    print(ENV_VARIABLE_MISSING.format(var='OWNER_ID'))
    sys.exit()
try:
    OWNER_ID: Final[int] = int(_owner_id_env)
except:
    print(f'Owner ID "{_owner_id_env}" in the .env variable OWNER_ID is not a number.')
    sys.exit()

DEBUG_MODE: Final[bool] = True if os.getenv('DEBUG_MODE') == 'ON' else False
LITE_MODE: Final[bool] = True if os.getenv('LITE_MODE') == 'ON' else False

_dev_ids_env: str | None = os.getenv('DEV_IDS')
if not _dev_ids_env:
    _dev_ids: Final[list[int]] = []
else:
    try:
        _dev_ids: list[int] = [int(dev_id.strip('" ')) for dev_id in _dev_ids_env.split(',')]
    except Exception as error:
        print(f'{error}\nCheck the syntax of the .env variable DEV_IDS.')
        sys.exit()
DEV_IDS: Final[list[int]] = _dev_ids + [OWNER_ID,]

_dev_guilds_env: str | None = os.getenv('DEV_GUILDS')
if not _dev_guilds_env:
    print(ENV_VARIABLE_MISSING.format(var='DEV_GUILDS'))
    sys.exit()
else:
    try:
        DEV_GUILDS: Final[list[int]] = [int(guild_id.strip('" ')) for guild_id in _dev_guilds_env.split(',')]
    except Exception as error:
        print(f'{error}\nCheck the syntax of the .env variable DEV_GUILDS.')
        sys.exit()

_embed_color_env: str | None = os.getenv('EMBED_COLOR')
if not _embed_color_env:
    EMBED_COLOR: Final[int] = 0x000000
else:
    try:
        EMBED_COLOR: Final[int] = int(_embed_color_env.strip('# '), base=16)
    except:
        print(f'Can\'t convert value "{_embed_color_env}" of variable EMBED_COLOR in the .env file to an integer.')
        sys.exit()

_emoji_guilds_env: str | None = os.getenv('EMOJI_GUILDS')
if not _emoji_guilds_env:
    print(ENV_VARIABLE_MISSING.format(var='EMOJI_GUILDS'))
    sys.exit()
else:
    try:
        EMOJI_GUILDS: Final[list[int]] = [int(guild_id.strip('" ')) for guild_id in _emoji_guilds_env.split(',')]
    except Exception as error:
        print(f'{error}\nCheck the syntax of the .env variable EMOJI_GUILDS.')
        sys.exit()

_link_invite_env: str | None = os.getenv('LINK_INVITE')
if _link_invite_env:
    LINK_INVITE: Final[str | None] = _link_invite_env.strip('" ')
else:
    LINK_INVITE: Final[str | None] = None

_link_support_env: str | None = os.getenv('LINK_SUPPORT')
if _link_support_env:
    LINK_SUPPORT: Final[str | None] = _link_support_env.strip('" ')
else:
    LINK_SUPPORT: Final[str | None] = None

_link_privacy_policy_env: str | None = os.getenv('LINK_PRIVACY_POLICY')
if _link_privacy_policy_env:
    LINK_PRIVACY_POLICY: Final[str | None] = _link_privacy_policy_env.strip('" ')
else:
    LINK_PRIVACY_POLICY: Final[str | None] = None

_link_terms_env: str | None = os.getenv('LINK_TERMS')
if _link_terms_env:
    LINK_TERMS: Final[str | None] = _link_terms_env.strip('" ')
else:
    LINK_TERMS: Final[str | None] = None
    
_complaint_channel_id_env: str | None = os.getenv('COMPLAINT_CHANNEL_ID')
if _complaint_channel_id_env:
    try:
        COMPLAINT_CHANNEL_ID: Final[int | None] = int(_complaint_channel_id_env.strip('" '))
    except:
        print(f'Complain channel ID "{_complaint_channel_id_env}" in the .env variable COMPLAINT_CHANNEL_ID is not a number.')
        sys.exit()
else:
    COMPLAINT_CHANNEL_ID: Final[int | None] = None
        
_suggestion_channel_id_env: str | None = os.getenv('SUGGESTION_CHANNEL_ID')
if _suggestion_channel_id_env:
    try:
        SUGGESTION_CHANNEL_ID: Final[int | None] = int(_suggestion_channel_id_env.strip('" '))
    except:
        print(f'Suggestion channel ID "{_suggestion_channel_id_env}" in the .env variable SUGGESTION_CHANNEL_ID is not a number.')
        sys.exit()
else:
    SUGGESTION_CHANNEL_ID: Final[int | None] = None


# Read bot version
_version_file_stream: TextIO = open(_VERSION_FILE, 'r')
VERSION: Final[str] = _version_file_stream.readline().rstrip('\n')
_version_file_stream.close()


DONOR_COOLDOWNS: Final[tuple[float, float, float, float]] = (1.0, 0.9, 0.8, 0.65)

EPIC_RPG_ID: Final[int] = 555955826880413696
TESTY_ID: Final[int] = 1050765002950332456 # Miriel's test bot to test triggers


DEFAULT_PREFIX: Final[str] = 'navi '

INTERACTION_TIMEOUT: Final[int] = 300

class ClanReset(NamedTuple):
    """Clan Reset time. Week starts at monday, UTC"""
    weekday: int = 5
    hour: int = 21
    minute: int = 59

CLAN_DEFAULT_STEALTH_THRESHOLD: Final[int] = 90

CHOCOLATE_BOX_MULTIPLIER: Final[float] = 0.97
CHRISTMAS_AREA_MULTIPLIER: Final[float] = 1.0 # Set this to 0.9 during christmas event and to 1 during the rest of the year
POTION_FLASK_MULTIPLIER: Final[float] = 0.9999 # Why did I even do this
ROUND_CARD_MULTIPLIER: Final[float] = 0.1