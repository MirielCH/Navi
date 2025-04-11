# regex.py

import re

from resources import strings

# --- Cooldown timestring ---
PATTERNS_COOLDOWN_TIMESTRING: tuple[str, ...] = (
    r"wait at least \*\*(.+?)\*\*...", #English
    r"espera al menos \*\*(.+?)\*\*...", #Spanish
    r"espere pelo menos \*\*(.+?)\*\*...", #Portuguese
)


# --- User data extraction ---
USER_ID_FROM_ICON_URL: re.Pattern = re.compile(r"(?:avatars|users)\/(.+?)\/")
USERNAME_FROM_EMBED_AUTHOR: re.Pattern = re.compile(r"^(.+?) — ")
NAME_FROM_MESSAGE: re.Pattern = re.compile(r"\s\*\*(.+?)\*\*\s")
NAME_FROM_MESSAGE_START: re.Pattern = re.compile(r"^\*\*(.+?)\*\*\s")


# --- User command detection ---
COMMAND_ADVENTURE: re.Pattern = re.compile(rf"(?:\badv\b|\badventure\b)")
COMMAND_ALCHEMY: re.Pattern = re.compile(rf"\balchemy\b")
COMMAND_AREA_MOVE: re.Pattern = re.compile(rf"(?:\barea\b|\bmove\b)\s+\b\d\d?\b")
COMMAND_AREA_MOVE_CANDY_CANE: re.Pattern = re.compile(
    rf"(?:(?:\barea\b|\bmove\b)\s+\b\d\d?\b|(?:\bxmas\b\s+|\bchristmas\b\s+)(?:\buse\b|\beat\b)\s+\bcandy\b\s+\bcane\b)"
)
COMMAND_ARENA: re.Pattern = re.compile(rf"\barena\b")
COMMAND_ARTIFACTS: re.Pattern = re.compile(rf"\bartifacts?\b")
COMMAND_BOOSTS: re.Pattern = re.compile(rf"\bboosts?\b")
COMMAND_BUY: re.Pattern = re.compile(rf"\bbuy\b")
COMMAND_CARD_HAND: re.Pattern = re.compile(rf"\bcards?\b\s+\bhand\b")
COMMAND_CARD_SLOTS: re.Pattern = re.compile(rf"\bcards?\b\s+\bslots\b")
COMMAND_CLAN: re.Pattern = re.compile(rf"\bguild\b")
COMMAND_CLAN_BUY_SPECIAL_SEED: re.Pattern = re.compile(rf"\bbuy\b\s+\bspecial\b\s+\bseed\b")
COMMAND_CLAN_RAID: re.Pattern = re.compile(rf"\bguild\b\s+\braid\b")
COMMAND_CLAN_RAID_UPGRADE: re.Pattern = re.compile(rf"\bguild\b\s+(?:\braid\b|\bupgrade\b)")
COMMAND_CLAN_UPGRADE: re.Pattern = re.compile(rf"guild\b\s+upgrade\b")
_patterns_craft_artifact: str = rf"(?:"
for artifact in strings.ARTIFACTS_EMOJIS.keys():
    _patterns_craft_artifact = fr'{_patterns_craft_artifact}\b{artifact}\b|'
COMMAND_CRAFT_ARTIFACT: re.Pattern = re.compile(fr'{_patterns_craft_artifact.strip("|")})')
COMMAND_CRAFT_COIN_SWORD: re.Pattern = re.compile(rf"\bcraft\b\s+\bcoin\b\s+\bsword\b")
COMMAND_CRAFT_RUBY_ARMOR: re.Pattern = re.compile(rf"\bcraft\b\s+\bruby\b\s+\barmor\b")
COMMAND_CRAFT_RUBY_SWORD: re.Pattern = re.compile(rf"\bcraft\b\s+\bruby\b\s+\bsword\b")
COMMAND_COINFLIP: re.Pattern = re.compile(rf"(?:\bcf\b|\bcoinflip\b)")
COMMAND_COOLDOWNS: re.Pattern = re.compile(rf"(?:\bcd\b|\bcooldowns\b)")
COMMAND_DAILY: re.Pattern = re.compile(rf"\bdaily\b")
COMMAND_DUEL: re.Pattern = re.compile(rf"\bduel\b")
COMMAND_DUNGEON_MINIBOSS_MININTBOSS: re.Pattern = re.compile(rf"(?:\bdung\b|\bdungeon\b|\bminiboss\b|\bminintboss\b)")
COMMAND_ENCHANT: re.Pattern = re.compile(rf"(?:\benchant\b|\brefine\b|\btransmute\b|\btranscend\b)")
COMMAND_EPIC_QUEST: re.Pattern = re.compile(rf"\bepic\b\s+\bquest\b")
COMMAND_EPIC_SHOP: re.Pattern = re.compile(rf"\bepic\b\s+\bshop\b")
COMMAND_EPIC_SHOP_BUY: re.Pattern = re.compile(rf"\bepic\b\s+\bshop\b\s+\bbuy\b")
COMMAND_EVENTS: re.Pattern = re.compile(rf"\bevents?\b")
COMMAND_FARM: re.Pattern = re.compile(rf"\bfarm\b")
COMMAND_FORGE_OMEGA_SWORD: re.Pattern = re.compile(rf"\bforge\b\s+\bomega\b\s+\bsword\b")
COMMAND_FORGE_ULTRAEDGY_ARMOR: re.Pattern = re.compile(rf"\bforge\b\s+\bultra-edgy\b\s+\barmor\b")
COMMAND_FORGE_GODLY_COOKIE: re.Pattern = re.compile(rf"\bforge\b\s+\bgodly\b\s+\bcookie\b")
COMMAND_HAL_BOO: re.Pattern = re.compile(rf"(?:\bhal\b|\bhalloween\b)\s+\bboo\b")
COMMAND_HAL_BUY_HALLOWEEN_BOOST: re.Pattern = re.compile(rf"(?:\bhal\b|\bhalloween\b)\s+\bbuy\b\s+\bhalloween\b\s+\bboost\b")
COMMAND_HAL_CRAFT_SPOOKY_SCROLL: re.Pattern = re.compile(rf"(?:\bhal\b|\bhalloween\b)\s+\bcraft\b\s+\bspooky\b\s+\bscroll\b")
COMMAND_HEAL: re.Pattern = re.compile(rf"\bheal\b")
COMMAND_HF_LIGHTSPEED: re.Pattern = re.compile(rf"\b(?:hf\b|horsefestival\b)\s+lightspeed\b")
COMMAND_HF_MEGARACE: re.Pattern = re.compile(rf"\b(?:hf\b|horsefestival\b)\s+megarace\b")
COMMAND_HF_MINIRACE: re.Pattern = re.compile(rf"\b(?:hf\b|horsefestival\b)\s+minirace\b")
COMMAND_HORSE: re.Pattern = re.compile(rf"(?:\bhorse\b\s+(?:\bbreed\b|\bbreeding\b|\brace\b)|(?:\bhorsefestival\b|\bhf\b)\s+\blightspeed\b)")
COMMAND_HORSE_RACE: re.Pattern = re.compile(rf"\bhorse\b\s+\brace\b")
COMMAND_HUNT: re.Pattern = re.compile(rf'\bhunt\b')
COMMAND_HUNT_ADVENTURE: re.Pattern = re.compile(rf"(?:\bhunt\b|\badv\b|\badventure\b)")
COMMAND_INVENTORY: re.Pattern = re.compile(rf"(?:\bi\b|\binv\b|\binventory\b)")
COMMAND_LOOTBOX: re.Pattern = re.compile(rf"\bbuy\s+[a-z]+\s+(?:\blb\b|\blootbox\b)")
COMMAND_LOTTERY: re.Pattern = re.compile(rf'(?:\blottery\b|\bbuy\b\s+\blottery\b\s+\bticket\b)')
COMMAND_LOVE_BUY_VALENTINE_BOOST: re.Pattern = re.compile(rf'\b(?:love|valentine)\b\s+\bbuy\b\s+\bvalentine\b\s+\bboost\b')
COMMAND_LOVE_SHARE: re.Pattern = re.compile(rf"(?:\blove\b|\bval\b|\bvalentine\b)\s+\bshare\b")
COMMAND_NSMB_BIGARENA: re.Pattern = re.compile(rf"(?:\bbig\b\s+\barena\b|\bminintboss\b)")
COMMAND_OMEGA_HORSE_TOKEN: re.Pattern = re.compile(rf"\buse\b\s+\bomega\b\s+\bhorse\b\s+\btoken\b")
COMMAND_OPEN: re.Pattern = re.compile(rf"(?:\bopen\b|\buse\b)")
COMMAND_PATREON: re.Pattern = re.compile(rf"(?:\bdonate\b|\bpatreon\b)")
COMMAND_PETS_ADVENTURE_CLAIM: re.Pattern = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+\bclaim\b")
COMMAND_PETS_ADVENTURE_START: re.Pattern = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+(?:\bfind\b|\blearn\b|\bdrill\b)")
COMMAND_PETS_ADVENTURE_CANCEL: re.Pattern = re.compile(rf"\bpets?\s+(?:\badv\b|\badventure\b)\s+\bcancel\b")
COMMAND_PETS_FUSION: re.Pattern = re.compile(rf"\bpets?\b\s+\bfusion\b")
COMMAND_PETS_TOURNAMENT: re.Pattern = re.compile(rf"\bpets?\b\s+\btournament\s+\b[a-z]+\b")
COMMAND_PROFILE_MENU: re.Pattern = re.compile(
    rf'(?:\bprofile\b|\bp\b|\bprofessions?\b|\bpr\b|\bhorse\b|\bcooldowns?\b|\bcd\b|\bready\b|\brd\b|\bbank\b|\binventory\b|\binv\b|\bi\b)'
)
COMMAND_QUEST: re.Pattern = re.compile(rf'\bquest\b')
COMMAND_QUEST_DUEL: re.Pattern = re.compile(rf'(?:\bquest\b|\bduel\b)')
COMMAND_QUEST_EPIC_QUEST: re.Pattern = re.compile(rf"(?:\bepic\b\s+\bquest\b|\bquest\b)")
COMMAND_PETS: re.Pattern = re.compile(rf"\bpets?\b")
COMMAND_PETS_CLAIM: re.Pattern = re.compile(rf"\bpets?\b\s+\bclaim\b")
COMMAND_PETS_SUMMARY: re.Pattern = re.compile(rf"\bpets?\b\s+\bsummary\b")
COMMAND_PROFESSIONS_ASCEND: re.Pattern = re.compile(rf"(?:\bpr\b|\bprofessions?\b)\s+ascend")
COMMAND_PROFILE_PROGRESS: re.Pattern = re.compile(rf"(?:\bp\b|\bprofile\b|\bprogress\b)")
COMMAND_READY: re.Pattern = re.compile(rf"(?:\brd\b|\bready\b)")
COMMAND_RETURNING_BUY_DUNGEON_RESET: re.Pattern = re.compile(rf"(?:ret\b|returning\b)\s+\bbuy\b\s+\bdungeon\b\s+\breset\b")
COMMAND_SELL_RUBY: re.Pattern = re.compile(rf"\bsell\b\s+\bruby\b")
COMMAND_SLEEPY_POTION: re.Pattern = re.compile(rf"\b[a-z]+\b\s+\buse\b\s+\bsleepy\b\s+\bpotion\b")
COMMAND_TIME_CAPSULE: re.Pattern = re.compile(rf"\buse\s+\btime\b\s+\bcapsule\b")
COMMAND_TIME_TRAVEL: re.Pattern = re.compile(rf"(?:(?:\bsuper\b\s+)?\btime\b\s+\btravel\b|\bsuper\b\s+\btravel\b)")
COMMAND_TRADE: re.Pattern = re.compile(rf"\btrade\b")
COMMAND_TRADE_DAILY: re.Pattern = re.compile(rf"\btrade\b\s+\bg\b")
COMMAND_TRADE_RUBY: re.Pattern = re.compile(rf"\btrade\b\s+\b[e-g]\b")
COMMAND_TRAINING: re.Pattern = re.compile(rf"(?:\btr\b|\btraining)")
COMMAND_TRAINING_BUNNY_PET: re.Pattern = re.compile(rf"(?:\btr\b|\btraining\b|\buse\b\s+\bchocolate\b\s+\bbunny\b)")
COMMAND_TRAINING_ULTRAINING: re.Pattern = re.compile(rf"(?:ul)?(?:tr\b|training\b)")
COMMAND_ULTRAINING: re.Pattern = re.compile(rf"(?:ultr\b|ultraining\b)")
COMMAND_ULTRAINING_BUY_TRAINING_RESET: re.Pattern = re.compile(rf"(?:ultr\b|ultraining\b)\s+\bbuy\b\s+\btraining\b\s+\breset\b")
COMMAND_USE_ARENA_TOKEN: re.Pattern = re.compile(rf"use\s+\barena\b\s+\btoken\b")
COMMAND_USE_EPIC_ITEM: re.Pattern = re.compile(
    rf"use\s+(?:\bepic\b\s+\bseed\b|\bultra\b\s+\bbait\b|\bcoin\b\s+\btrumpet\b|\blegendary\b\s+\btoothbrush\b)"
)
COMMAND_USE_EPIC_ITEM_ARENA_TOKEN: re.Pattern = re.compile(
    rf"use\s+(?:\bepic\b\s+\bseed\b|\bultra\b\s+\bbait\b|\bcoin\b\s+\btrumpet\b|\blegendary\b\s+\btoothbrush\b|\barena\b\s+\btoken\b)"
)
COMMAND_USE_MEGA_BOOST: re.Pattern = re.compile(rf"use\s+\bmega\b\s+\bboost\b")
COMMAND_USE_PARTY_POPPER: re.Pattern = re.compile(rf"use\s+\bparty\b\s+\bpopper\b")
COMMAND_USE_ROUND_CARD: re.Pattern = re.compile(rf"use\s+\bround\b\s+\bcard\b")
COMMAND_USE_TIME_COOKIE: re.Pattern = re.compile(rf"use\s+\btime\b\s+\bcookie\b")
COMMAND_UNSEAL_ETERNITY: re.Pattern = re.compile(rf"\bvoid\b\s+\bunseal\b\s+\be(?:ternity)?\b")
COMMAND_VOTE: re.Pattern = re.compile(rf"\bvote\b")
COMMAND_WEEKLY: re.Pattern = re.compile(rf"\bweekly\b")
_patterns_work: str = rf"(?:"
for command in strings.WORK_COMMANDS:
    _patterns_work = fr'{_patterns_work}\b{command}\b|'
COMMAND_WORK: re.Pattern = re.compile(fr'{_patterns_work.strip("|")})')
COMMAND_XMAS_BUY_CHRISTMAS_BOOST: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+\bbuy\b\s+\bchristmas\b\s+\bboost\b")
COMMAND_XMAS_CALENDAR: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+\bcalendar\b")
COMMAND_XMAS_CHIMNEY: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+\bchimney\b")
COMMAND_XMAS_CRAFT_COOKIES_AND_MILK: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+\bcraft\b\s+\bcookies\b\s+\band\b\s+\bmilk\b")
COMMAND_XMAS_EAT_GINGERBREAD: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+(?:\beat\b|\buse\b)\s+\bgingerbread\b")
COMMAND_XMAS_OPEN_ETERNAL: re.Pattern = re.compile(rf"(?:\bxmas\b|\bchristmas\b)\s+\bopen\b\s+\beternal\b")