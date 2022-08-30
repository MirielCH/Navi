# regex.py

import re

from resources import strings


# --- Cooldown timestring ---
PATTERNS_COOLDOWN_TIMESTRING = [
    "wait at least \*\*(.+?)\*\*...", #English
    "espera al menos \*\*(.+?)\*\*...", #Spanish
    "espere pelo menos \*\*(.+?)\*\*...", #Portuguese
]


# --- User data extraction ---
USER_ID_FROM_ICON_URL = re.compile(r"avatars\/(.+?)\/")
USERNAME_FROM_EMBED_AUTHOR = re.compile(r"^(.+?) — ")
NAME_FROM_MESSAGE = re.compile(r"\s\*\*(.+?)\*\*\s")
NAME_FROM_MESSAGE_START = re.compile(r"^\*\*(.+?)\*\*\s")


# --- User command detection ---
PREFIX = rf'(?:rpg\b\s+)?'
COMMAND_ADVENTURE = re.compile(rf"{PREFIX}(?:\badv\b|\badventure\b)")
COMMAND_ARENA = re.compile(rf"{PREFIX}\barena\b")
COMMAND_CLAN = re.compile(rf"{PREFIX}\bguild\b")
COMMAND_CLAN_RAID = re.compile(rf"{PREFIX}\bguild\b\s+\braid\b")
COMMAND_CLAN_RAID_UPGRADE = re.compile(rf"{PREFIX}\bguild\b\s+(?:\braid\b|\bupgrade\b)")
COMMAND_CLAN_UPGRADE = re.compile(rf"{PREFIX}guild\b\s+upgrade\b")
COMMAND_CRAFT_COIN_SWORD = re.compile(rf"{PREFIX}\bcraft\b\s+\bcoin\b\s+\bsword\b")
COMMAND_CRAFT_RUBY_ARMOR = re.compile(rf"{PREFIX}\bcraft\b\s+\bruby\b\s+\barmor\b")
COMMAND_CRAFT_RUBY_SWORD = re.compile(rf"{PREFIX}\bcraft\b\s+\bruby\b\s+\bsword\b")
COMMAND_COOLDOWNS = re.compile(rf"{PREFIX}(?:\bcd\b|\bcooldowns\b)")
COMMAND_DAILY = re.compile(rf"{PREFIX}\bdaily\b")
COMMAND_DUEL = re.compile(rf"{PREFIX}\bduel\b")
COMMAND_DUNGEON_MINIBOSS = re.compile(rf"{PREFIX}(?:\bdung\b|\bdungeon\b|\bminiboss\b)")
COMMAND_ENCHANT = re.compile(rf"{PREFIX}(?:\benchant\b|\brefine\b|\btransmute\b|\btranscend\b)")
COMMAND_EPIC_QUEST = re.compile(rf"{PREFIX}\bepic\b\s+\bquest\b")
COMMAND_EVENTS = re.compile(rf"{PREFIX}\bevents?\b")
COMMAND_FARM = re.compile(rf"{PREFIX}\bfarm\b")
COMMAND_FORGE_ULTRAEDGY_ARMOR = re.compile(rf"{PREFIX}\bforge\b\s+\bultra-edgy\b\s+\barmor\b")
COMMAND_HEAL = re.compile(rf"{PREFIX}\bheal\b")
COMMAND_HF_LIGHTSPEED = re.compile(rf"{PREFIX}\bhf\b\s+\blightspeed\b")
COMMAND_HORSE = re.compile(rf"{PREFIX}horse\b\s+(?:\bbreed\b|\bbreeding\b|\brace\b)")
COMMAND_HORSE_RACE = re.compile(rf"{PREFIX}\bhorse\b\s+\brace\b")
COMMAND_HUNT = re.compile(rf'{PREFIX}\bhunt\b')
COMMAND_HUNT_ADVENTURE = re.compile(rf"{PREFIX}(?:\bhunt\b|\badv\b|\badventure\b)")
COMMAND_INVENTORY = re.compile(rf"{PREFIX}(?:\bi\b|\binv\b|\binventory\b)")
COMMAND_LOOTBOX = re.compile(rf"{PREFIX}\bbuy\s+[a-z]+\s+(?:\blb\b|\blootbox\b)")
COMMAND_LOTTERY = re.compile(rf'{PREFIX}(?:\blottery\b|\bbuy\b\s+\blottery\b\s+\bticket\b)')
COMMAND_NSMB_BIGARENA = re.compile(rf"{PREFIX}(?:\bbig\b\s+\barena\b|\bminintboss\b)")
COMMAND_OMEGA_HORSE_TOKEN = re.compile(rf"{PREFIX}\buse\b\s+\bomega\b\s+\bhorse\b\s+\btoken\b")
COMMAND_OPEN = re.compile(rf"{PREFIX}\bopen\b")
COMMAND_PETS_ADVENTURE_CLAIM = re.compile(rf"{PREFIX}\bpets?\s+(?:\badv\b|\badventure\b)\s+\bclaim\b")
COMMAND_PETS_ADVENTURE_START = re.compile(rf"{PREFIX}\bpets?\s+(?:\badv\b|\badventure\b)\s+(?:\bfind\b|\blearn\b|\bdrill\b)")
COMMAND_PETS_ADVENTURE_CANCEL = re.compile(rf"{PREFIX}\bpets?\s+(?:\badv\b|\badventure\b)\s+\bcancel\b")
COMMAND_PETS_FUSION = re.compile(rf"{PREFIX}\bpets?\b\s+\bfusion\b")
COMMAND_PETS_TOURNAMENT = re.compile(rf"{PREFIX}\bpets?\b\s+\btournament\s+\b[a-z]+\b")
COMMAND_QUEST = re.compile(rf'{PREFIX}\bquest\b')
COMMAND_QUEST_EPIC_QUEST = re.compile(rf"{PREFIX}(?:\bepic\b\s+\bquest\b|\bquest\b)")
COMMAND_PETS = re.compile(rf"{PREFIX}\bpets?\b")
COMMAND_SELL_RUBY = re.compile(rf"{PREFIX}\bsell\b\s+\bruby\b")
COMMAND_SLEEPY_POTION = re.compile(rf"{PREFIX}\b[a-z]+\b\s+\buse\b\s+\bsleepy\b\s+\bpotion\b")
COMMAND_TIME_TRAVEL = re.compile(rf"{PREFIX}(?:\bsuper\b\s+)?\btime\b\s+\btravel\b")
COMMAND_TRADE_RUBY = re.compile(rf"{PREFIX}\btrade\b\s+\b[e-f]\b")
COMMAND_TRAINING = re.compile(rf"{PREFIX}(?:\btr\b|\btraining)")
COMMAND_TRAINING_ULTRAINING = re.compile(rf"{PREFIX}(?:ul)?(?:tr\b|training\b)")
COMMAND_ULTRAINING = re.compile(rf"{PREFIX}(?:ultr\b|ultraining\b)")
COMMAND_VOTE = re.compile(rf"{PREFIX}\bvote\b")
COMMAND_WEEKLY = re.compile(rf"{PREFIX}\bweekly\b")
COMMAND_WORK = rf"{PREFIX}(?:"
for command in strings.WORK_COMMANDS:
    COMMAND_WORK = fr'{COMMAND_WORK}\b{command}\b|'
COMMAND_WORK = re.compile(fr'{COMMAND_WORK.strip("|")})')