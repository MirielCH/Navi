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
COMMAND_ADVENTURE = re.compile(rf"(?:\badv\b|\badventure\b)")
COMMAND_ARENA = re.compile(rf"\barena\b")
COMMAND_CLAN = re.compile(rf"\bguild\b")
COMMAND_CLAN_RAID = re.compile(rf"\bguild\b\s+\braid\b")
COMMAND_CLAN_RAID_UPGRADE = re.compile(rf"\bguild\b\s+(?:\braid\b|\bupgrade\b)")
COMMAND_CLAN_UPGRADE = re.compile(rf"guild\b\s+upgrade\b")
COMMAND_CRAFT_COIN_SWORD = re.compile(rf"\bcraft\b\s+\bcoin\b\s+\bsword\b")
COMMAND_CRAFT_RUBY_ARMOR = re.compile(rf"\bcraft\b\s+\bruby\b\s+\barmor\b")
COMMAND_CRAFT_RUBY_SWORD = re.compile(rf"\bcraft\b\s+\bruby\b\s+\bsword\b")
COMMAND_COOLDOWNS = re.compile(rf"(?:\bcd\b|\bcooldowns\b)")
COMMAND_DAILY = re.compile(rf"\bdaily\b")
COMMAND_DUEL = re.compile(rf"\bduel\b")
COMMAND_DUNGEON_MINIBOSS_MININTBOSS = re.compile(rf"(?:\bdung\b|\bdungeon\b|\bminiboss\b|\bminintboss\b)")
COMMAND_ENCHANT = re.compile(rf"(?:\benchant\b|\brefine\b|\btransmute\b|\btranscend\b)")
COMMAND_EPIC_QUEST = re.compile(rf"\bepic\b\s+\bquest\b")
COMMAND_EVENTS = re.compile(rf"\bevents?\b")
COMMAND_FARM = re.compile(rf"\bfarm\b")
COMMAND_FORGE_ULTRAEDGY_ARMOR = re.compile(rf"\bforge\b\s+\bultra-edgy\b\s+\barmor\b")
COMMAND_HEAL = re.compile(rf"\bheal\b")
COMMAND_HF_LIGHTSPEED = re.compile(rf"\bhf\b\s+\blightspeed\b")
COMMAND_HORSE = re.compile(rf"horse\b\s+(?:\bbreed\b|\bbreeding\b|\brace\b)")
COMMAND_HORSE_RACE = re.compile(rf"\bhorse\b\s+\brace\b")
COMMAND_HUNT = re.compile(rf'\bhunt\b')
COMMAND_HUNT_ADVENTURE = re.compile(rf"(?:\bhunt\b|\badv\b|\badventure\b)")
COMMAND_INVENTORY = re.compile(rf"(?:\bi\b|\binv\b|\binventory\b)")
COMMAND_LOOTBOX = re.compile(rf"\bbuy\s+[a-z]+\s+(?:\blb\b|\blootbox\b)")
COMMAND_LOTTERY = re.compile(rf'(?:\blottery\b|\bbuy\b\s+\blottery\b\s+\bticket\b)')
COMMAND_NSMB_BIGARENA = re.compile(rf"(?:\bbig\b\s+\barena\b|\bminintboss\b)")
COMMAND_OMEGA_HORSE_TOKEN = re.compile(rf"\buse\b\s+\bomega\b\s+\bhorse\b\s+\btoken\b")
COMMAND_OPEN = re.compile(rf"\bopen\b")
COMMAND_PETS_ADVENTURE_CLAIM = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+\bclaim\b")
COMMAND_PETS_ADVENTURE_START = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+(?:\bfind\b|\blearn\b|\bdrill\b)")
COMMAND_PETS_ADVENTURE_CANCEL = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+\bcancel\b")
COMMAND_PETS_FUSION = re.compile(rf"\bpets?\b\s+\bfusion\b")
COMMAND_PETS_TOURNAMENT = re.compile(rf"\bpets?\b\s+\btournament\s+\b[a-z]+\b")
COMMAND_QUEST = re.compile(rf'\bquest\b')
COMMAND_QUEST_EPIC_QUEST = re.compile(rf"(?:\bepic\b\s+\bquest\b|\bquest\b)")
COMMAND_PETS = re.compile(rf"\bpets?\b")
COMMAND_READY = re.compile(rf"(?:\brd\b|\bready\b)")
COMMAND_SELL_RUBY = re.compile(rf"\bsell\b\s+\bruby\b")
COMMAND_SLEEPY_POTION = re.compile(rf"\b[a-z]+\b\s+\buse\b\s+\bsleepy\b\s+\bpotion\b")
COMMAND_TIME_TRAVEL = re.compile(rf"(?:(?:\bsuper\b\s+)?\btime\b\s+\btravel\b|\bsuper\b\s+\btravel\b)")
COMMAND_TRADE_RUBY = re.compile(rf"\btrade\b\s+\b[e-f]\b")
COMMAND_TRAINING = re.compile(rf"(?:\btr\b|\btraining)")
COMMAND_TRAINING_ULTRAINING = re.compile(rf"(?:ul)?(?:tr\b|training\b)")
COMMAND_ULTRAINING = re.compile(rf"(?:ultr\b|ultraining\b)")
COMMAND_VOTE = re.compile(rf"\bvote\b")
COMMAND_WEEKLY = re.compile(rf"\bweekly\b")
COMMAND_WORK = rf"(?:"
for command in strings.WORK_COMMANDS:
    COMMAND_WORK = fr'{COMMAND_WORK}\b{command}\b|'
COMMAND_WORK = re.compile(fr'{COMMAND_WORK.strip("|")})')