# strings.py
"""Contains global strings"""

import re

from resources import settings

# --- Error messages ---
MSG_INTERACTION_ERROR = 'You are not allowed to use this interaction.'


# --- Internal error messages ---
INTERNAL_ERROR_NO_DATA_FOUND = 'No data found in database.\nTable: {table}\nFunction: {function}\nSQL: {sql}'
INTERNAL_ERROR_SQLITE3 = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\SQL: {sql}'
INTERNAL_ERROR_LOOKUP = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\Records: {record}'
INTERNAL_ERROR_NO_ARGUMENTS = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'
INTERNAL_ERROR_DICT_TO_OBJECT = 'Error converting record into object\nFunction: {function}\nRecord: {record}\n'


# --- Default messages ---
DEFAULT_MESSAGE = 'Hey! It\'s time for {command}!'
DEFAULT_MESSAGE_EVENT = (
    'Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the '
    f'official EPIC RPG server.'
)
DEFAULT_MESSAGE_CUSTOM_REMINDER = 'Hey! This is your reminder for **{message}**!'

DEFAULT_MESSAGES = {
    'adventure': DEFAULT_MESSAGE,
    'arena': DEFAULT_MESSAGE,
    'big-arena': DEFAULT_MESSAGE_EVENT,
    'daily': DEFAULT_MESSAGE,
    'duel': DEFAULT_MESSAGE,
    'dungeon-miniboss': DEFAULT_MESSAGE,
    'farm': DEFAULT_MESSAGE,
    'guild': DEFAULT_MESSAGE,
    'horse': DEFAULT_MESSAGE,
    'horse-race': DEFAULT_MESSAGE_EVENT,
    'hunt': DEFAULT_MESSAGE,
    'lootbox': DEFAULT_MESSAGE,
    'lottery': 'Hey! The lottery just finished. Use `rpg lottery` to check out who won and {command} to enter the next draw!',
    'minintboss': DEFAULT_MESSAGE_EVENT,
    'partner': '**{user}** found {loot} for you!',
    'pets': 'Hey! Your pet `{id}` is back! {emoji}',
    'pet-tournament': DEFAULT_MESSAGE_EVENT,
    'quest': DEFAULT_MESSAGE,
    'training': DEFAULT_MESSAGE,
    'vote': DEFAULT_MESSAGE,
    'weekly': DEFAULT_MESSAGE,
    'work': DEFAULT_MESSAGE,
}


CLAN_LEADERBOARD_ROAST_ZERO_ENERGY = (
    '<:amongus_sus:875996946903478292> There is one player among us that wants us to believe he is not an impostor.'
)

MSG_ERROR = 'Whoops, something went wrong here.'
MSG_NOT_CLAN_LEADER = (
    '**{username}**, you are not registered as a guild owner. Only guild owners can change guild channel settings.\n'
    'If you _are_ the guild owner, run `rpg guild list` to add or update your guild in my database.\n'
    'If you don\'t know yet, check `{prefix}guild` to see how guild channel reminders work.\n\n'
    'If you want to enable or disable the personal guild command reminder, use `{prefix}enable|disable guild` instead.'
)
MSG_INVALID_ARGUMENT = 'Invalid argument. Check `{prefix}help` for the correct commands.'
MSG_SYNTAX = 'The command syntax is `{syntax}`.'
MSG_CLAN_NOT_REGISTERED = 'Your guild is not registered with Navi. If you are in a guild, use `rpg guild list` to add it.'

DONOR_TIERS = (
    'Non-donator',
    'Donator',
    'EPIC donator',
    'SUPER donator',
    'MEGA donator',
    'HYPER donator',
    'ULTRA donator',
    'ULTIMATE donator',
)


# --- Activities ---
SLEEPY_POTION_AFFECTED_ACTIVITIES = (
    'adventure',
    'arena',
    'daily',
    'duel',
    'dungeon-miniboss',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'quest',
    'training',
    'weekly',
    'work'
)

ACTIVITIES = (
    'adventure',
    'arena',
    'big-arena',
    'daily',
    'duel',
    'dungeon-miniboss',
    'farm',
    'guild',
    'horse',
    'horse-race',
    'hunt',
    'lootbox',
    'lottery',
    'minintboss',
    'partner',
    'pets',
    'pet-tournament',
    'quest',
    'training',
    'vote',
    'weekly',
    'work',
)

ACTIVITIES_ALL = list(ACTIVITIES[:])
ACTIVITIES_ALL.append('all')
ACTIVITIES_ALL.sort()

ACTIVITIES_COMMANDS = (
    'adventure',
    'arena',
    'daily',
    'duel',
    'dungeon-miniboss',
    'farm',
    'guild',
    'horse',
    'hunt',
    'lootbox',
    'quest',
    'training',
    'vote',
    'weekly',
    'work',
)

ACTIVITIES_EVENTS = (
    'big-arena',
    'horse-race',
    'lottery',
    'minintboss',
    'pet-tournament',
)

ACTIVITIES_SLASH_COMMANDS = {
    'adventure': 'adventure',
    'arena': 'arena',
    'big-arena': 'big arena',
    'daily': 'daily',
    'duel': 'duel',
    'dungeon-miniboss': 'dungeon',
    'farm': 'farm',
    'guild': 'guild raid',
    'horse': 'horse breeding',
    'horse-race': 'horse race',
    'hunt': 'hunt',
    'lootbox': 'buy',
    'lottery': 'lottery',
    'minintboss': 'minintboss',
    'pet-tournament': 'pets tournament',
    'quest': 'quest',
    'training': 'training',
    'vote': 'vote',
    'weekly': 'weekly',
    'work': 'work',
}

ACTIVITIES_ALIASES = {
    'adv': 'adventure',
    'lb': 'lootbox',
    'tr': 'training',
    'farming': 'farm',
    'chop': 'work',
    'fish': 'work',
    'mine': 'work',
    'pickup': 'work',
    'axe': 'work',
    'net': 'work',
    'pickaxe': 'work',
    'ladder': 'work',
    'boat': 'work',
    'bowsaw': 'work',
    'drill': 'work',
    'tractor': 'work',
    'chainsaw': 'work',
    'bigboat': 'work',
    'dynamite': 'work',
    'greenhouse': 'work',
    'pet': 'pets',
    'tournament': 'pet-tournament',
    'pettournament': 'pet-tournament',
    'lootboxalert': 'partner',
    'lbalert': 'partner',
    'lb-alert': 'partner',
    'partner-alert': 'partner',
    'partneralert': 'partner',
    'notsominiboss': 'minintboss',
    'notsomini': 'minintboss',
    'nsmb': 'minintboss',
    'minin\'tboss': 'minintboss',
    'minint': 'minintboss',
    'big': 'big-arena',
    'bigarena': 'big-arena',
    'voting': 'vote',
    'dungeon': 'dungeon-miniboss',
    'dung': 'dungeon-miniboss',
    'mb': 'dungeon-miniboss',
    'miniboss': 'dungeon-miniboss',
    'horserace': 'horse-race',
    'horseracing': 'horse-race',
    'racing': 'horse-race',
    'race': 'horse-race',
    'horsebreed': 'horse',
    'horsebreeding': 'horse',
    'breed': 'horse',
    'breeding': 'horse',
    'dueling': 'duel',
    'duelling': 'duel',
}

ACTIVITIES_COLUMNS = {
    'adventure': 'alert_adventure',
    'arena': 'alert_arena',
    'big-arena': 'alert_big_arena',
    'daily': 'alert_daily',
    'duel': 'alert_duel',
    'dungeon-miniboss': 'alert_dungeon_miniboss',
    'farm': 'alert_farm',
    'guild': 'alert_guild',
    'horse': 'alert_horse_breed',
    'horse-race': 'alert_horse_race',
    'hunt': 'alert_hunt',
    'lootbox': 'alert_lootbox',
    'lottery': 'alert_lottery',
    'minintboss': 'alert_not_so_mini_boss',
    'partner': 'alert_partner',
    'pets': 'alert_pets',
    'pet-tournament': 'alert_pet_tournament',
    'quest': 'alert_quest',
    'training': 'alert_training',
    'vote': 'alert_vote',
    'weekly': 'alert_weekly',
    'work': 'alert_work',
}

ACTIVITIES_WITH_COOLDOWN = (
    'adventure',
    'arena',
    'daily',
    'farm',
    'guild',
    'horse',
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'training',
    'weekly',
    'work',
)


# --- Monsters ---
MONSTERS_ADVENTURE = (
    '**Ancientest Dragon**',
    '**Yes, As You Expected, Another Hyper Giant Dragon But OP etc**',
    '**Another Mutant Dragon Like In Area 11 But Stronger**',
    '**Attack Helicopter**',
    '**Bunch of Bees**',
    '**Chimera**',
    '**Centaur**',
    '**Cyclops**',
    '**Dark Knight**',
    '**Dinosaur**',
    '**Ent**',
    '**Even More Ancient Dragon**',
    '**Giant Spider**',
    '**Golem**',
    '**Hydra**',
    '**Hyper Giant Aeronautical Engine**',
    '**Hyper Giant Bowl**',
    '**Hyper Giant Chest**',
    '**Hyper Giant Door**',
    '**Hyper Giant Dragon**',
    '**Hyper Giant Toilet**',
    '**I Have No More Ideas Dragon**',
    '**Just Purple Dragon**',
    '**Kraken**',
    '**Leviathan**',
    '**Mammoth**',
    '**Mutant Book**',
    '**Mutant Backpack**',
    '**Mutant Dragon**',
    "**Mutant 'ESC' Key**",
    '**Mutantest Dragon**',
    '**Mutant Shoe**',
    '**Mutant Water Bottle**',
    '**Ogre**',
    '**Titan**',
    '**Typhon**',
    '**War Tank**',
    '**Wyrm**',
    '**Werewolf**',
    '**Ancient Dragon**',
    '**Time Annihilator**',
    '**Time Devourer**',
    '**Time Slicer**',
    '**Black Hole**',
    '**Supernova**',
    '**Wormhole**',
    '**Corrupted Killer Robot**',
    '**Corrupted Mermaid**',
    '**Corrupted Dragon**',
    '**Shadow Creature**',
    '**Shadow Entity**',
    '**Abyss Worm**',
    '**Void Cone**',
    '**Void Cube**',
    '**Void Sphere**',
    '**Dragon**',
    'Krampus',
    '**Yeti**',
    '**Hyper Giant Ice Block**',
)

MONSTERS_HUNT = (
    '**Adult Dragon**',
    '**Baby Demon**',
    '**Baby Dragon**',
    '**Baby Robot**',
    '**Cecaelia**',
    '**Definitely Not Young Dragon**',
    '**Demon**',
    '**Dullahan**',
    '**Giant Crocodile**',
    '**Giant Piranha**',
    '**Giant Scorpion**',
    '**Ghoul**',
    '**Ghost**',
    '**Goblin**',
    '**Harpy**',
    '**How Do You Dare Call This Dragon "Young"???**',
    '**Imp**',
    '**Kid Dragon**',
    '**Killer Robot**',
    '**Manticore**',
    '**Mermaid**',
    '**Not So Young Dragon**',
    '**Not Young At All Dragon**',
    '**Nereid**',
    '**Nymph**',
    '**Old Dragon**',
    '**Skeleton**',
    '**Slime**',
    '**Sorcerer**',
    '**Teen Dragon**',
    '**Unicorn**',
    '**Wolf**',
    '**Young Dragon**',
    '**Zombie**',
    '**Witch**',
    '**Scaled Baby Dragon**',
    '**Scaled Kid Dragon**',
    '**Scaled Teen Dragon**',
    '**Scaled Adult Dragon**',
    '**Scaled Old Dragon**',
    '**Void Fragment**',
    '**Void Particles**',
    '**Void Shard**',
    '**Abyss Bug**',
    '**Nothing**',
    '**Shadow Hands**',
    '**Corrupted Unicorn**',
    '**Corrupted Wolf**',
    '**Corrupted Zombie**',
    '**Asteroid**',
    '**Neutron Star**',
    '**Flying Saucer**',
    '**Time Alteration**',
    '**Time Interference**',
    '**Time Limitation**',
    '**Elf**',
    '**Christmas Reindeer**',
    '**Snowman**',
    '**Horslime**',
)


TRACKED_COMMANDS = (
    'hunt',
    'work',
    'farm',
    'training',
    'adventure',
    'epic guard'
) # Sorted by cooldown length


EPIC_NPC_NAMES = [
    'EPIC NPC', #English
    'NPC ÉPICO', #Spanish, Portuguese
]


# --- Commands ---
WORK_COMMANDS = (
    'chop',
    'pickaxe',
    'bowsaw',
    'chainsaw',
    'fish',
    'net',
    'bigboat',
    'pickup',
    'ladder',
    'tractor',
    'greenhouse',
    'mine',
    'drill',
    'dynamite',
    'axe',
    'boat',
)

SLASH_COMMANDS = {
    'adventure': '`/adventure`',
    'arena': '`/arena`',
    'axe': '`/axe`',
    'big arena': '`/big arena`',
    'big dice': '`/big dice`',
    'bigboat': '`/bigboat`',
    'blackjack': '`/blackjack`',
    'boat': '`/boat`',
    'bowsaw': '`/bowsaw`',
    'buy': '`/buy`',
    'chainsaw': '`/chainsaw`',
    'chop': '`/chop`',
    'coinflip': '`/coinflip`',
    'cook': '`/cook`',
    'craft': '`/craft`',
    'cups': '`/cups`',
    'daily': '`/daily`',
    'dice': '`/dice`',
    'dismantle': '`/dismantle`',
    'drill': '`/drill`',
    'duel': '`/duel`',
    'dungeon': '`/dungeon`',
    'dynamite': '`/dynamite`',
    'epic quest': '`/epic quest`',
    'farm': '`/farm`',
    'fish': '`/fish`',
    'greenhouse': '`/greenhouse`',
    'guild list': '`/guild list`',
    'guild raid': '`/guild raid`',
    'guild stats': '`/guild stats`',
    'guild upgrade': '`/guild upgrade`',
    'heal': '`/heal`',
    'horse breeding': '`/horse breeding`',
    'horse race': '`/horse race`',
    'hunt': '`/hunt`',
    'ladder': '`/ladder`',
    'lottery': '`/lottery`',
    'megarace': '`/hf megarace start`',
    'mine': '`/mine`',
    'miniboss': '`/miniboss`',
    "minintboss": '`/minintboss`',
    'minirace': '`/hf minirace`',
    'multidice': '`/multidice`',
    'net': '`/net`',
    'pets adventure': '`/pets adventure`',
    'pets claim': '`/pets claim`',
    'pets fusion': '`/pets fusion`',
    'pets list': '`/pets list`',
    'pets tournament': '`/pets tournament`',
    'pickaxe': '`/pickaxe`',
    'pickup': '`/pickup`',
    'quest': '`/quest start`',
    'slots': '`/slots`',
    'tractor': '`/tractor`',
    'trade items': '`/trade items`',
    'training': '`/training`',
    'ultraining': '`/ultraining start`',
    'void areas': '`/void areas`',
    'vote': '`/vote`',
    'weekly': '`/weekly`',
    'wheel': '`/wheel`',
}

SLASH_COMMANDS_NEW = {
    'adventure': '</adventure:961046240420855808>',
    'arena': '</arena:960740633302138920>',
    'axe': '</axe:959162695909781504>',
    'big arena': '</big arena:960362922029252719>',
    'big dice': '</big dice:960362922029252719>',
    'bigboat': '</bigboat:959163596754010162>',
    'blackjack': '</blackjack:959916178149605437>',
    'boat': '</boat:959163596087111780>',
    'bowsaw': '</bowsaw:959162696371146883>',
    'buy': '</buy:964351964651601961>',
    'chainsaw': '</chainsaw:959162697398763590>',
    'chop': '</chop:959162695070928896>',
    'coinflip': '</coinflip:958555800111038495>',
    'cook': '</cook:959915740977315860>',
    'craft': '</craft:960002336372162570>',
    'cups': '</cups:958555799288959016>',
    'daily': '</daily:956658466099982386>',
    'dice': '</dice:957815871902994432>',
    'dismantle': '</dismantle:960002337328496660>',
    'drill': '</drill:959164541206417479>',
    'duel': '</duel:960362921198751784>',
    'dungeon': '</dungeon:966956823032791090>',
    'dynamite': '</dynamite:959164543920132126>',
    'epic quest': '</epic quest:961046236469792810>',
    'farm': '</farm:959915738716598272>',
    'fish': '</fish:959163594665242684>',
    'greenhouse': '</greenhouse:959164279884509194>',
    'guild list': '</guild list:961046237753257994>',
    'guild raid': '</guild raid:961046237753257994>',
    'guild stats': '</guild stats:961046237753257994>',
    'guild upgrade': '</guild upgrade:961046237753257994>',
    'heal': '</heal:959915737777061928>',
    'horse breeding': '</horse breeding:966961638378987540>',
    'horse race': '</horse race:966961638378987540>',
    'hunt': '</hunt:964351961774325770>',
    'ladder': '</ladder:959164278072569936>',
    'lottery': '</lottery:957815874063061072>',
    'megarace': '</hf megarace:1003530661761663087>',
    'mine': '</mine:959164539922952263>',
    'miniboss': '</miniboss:960740632400388146>',
    "minintboss": '</minintboss:960362922813575209>',
    "multidice": '</multidice:958558816818036776>',
    'net': '</net:959163595428618290>',
    'pets adventure': '</pets adventure:961046238613090385>',
    'pets claim': '</pets claim:961046238613090385>',
    'pets fusion': '</pets fusion:961046238613090385>',
    'pets list': '</pets list:961046238613090385>',
    'pets tournament': '</pets tournament:961046238613090385>',
    'pickaxe': '</pickaxe:959164540589842492>',
    'pickup': '</pickup:959164277321768990>',
    'quest': '</quest start:960740627790848041>',
    'slots': '</slots:958555798273925180>',
    'tractor': '</tractor:959164278890463272>',
    'trade items': '</trade items:959915739840647188>',
    'training': '</training:960362923983765545>',
    'ultraining': '</ultraining start:959942194649772112>',
    'void areas': '</void areas:959942192623931442>',
    'vote': '</vote:964351963720478760>',
    'weekly': '</weekly:956658465185603645>',
    'wheel': '</wheel:959916179525341194>',
}


# --- Regex ---
PATTERNS_COOLDOWN_TIMESTRING = [
    "wait at least \*\*(.+?)\*\*...", #English
    "espera al menos \*\*(.+?)\*\*...", #Spanish
    "espere pelo menos \*\*(.+?)\*\*...", #Portuguese
]

REGEX_USER_ID_FROM_ICON_URL = re.compile(r"avatars\/(.+?)\/")
REGEX_USERNAME_FROM_EMBED_AUTHOR = re.compile(r"^(.+?) — ")
REGEX_NAME_FROM_MESSAGE = re.compile(r"\s\*\*(.+?)\*\*\s")
REGEX_NAME_FROM_MESSAGE_START = re.compile(r"^\*\*(.+?)\*\*\s")

REGEX_PREFIX = rf'^(rpg\b\s+|<@!?{settings.EPIC_RPG_ID}>\s+)?'
REGEX_COMMAND_ADVENTURE = re.compile(rf"{REGEX_PREFIX}(?:adv\b|adventure\b)")
REGEX_COMMAND_ARENA = re.compile(rf"{REGEX_PREFIX}arena\b")
REGEX_COMMAND_CLAN_RAID = re.compile(rf"{REGEX_PREFIX}guild\b\s+raid\b")
REGEX_COMMAND_CLAN_RAID_UPGRADE = re.compile(rf"{REGEX_PREFIX}guild\b\s+(?:raid\b|upgrade\b)")
REGEX_COMMAND_CLAN_UPGRADE = re.compile(rf"{REGEX_PREFIX}guild\b\s+upgrade\b")
REGEX_COMMAND_CRAFT_COIN_SWORD = re.compile(rf"{REGEX_PREFIX}craft\b\s+coin\b\s+sword\b")
REGEX_COMMAND_CRAFT_RUBY_ARMOR = re.compile(rf"{REGEX_PREFIX}craft\b\s+ruby\b\s+armor\b")
REGEX_COMMAND_CRAFT_RUBY_SWORD = re.compile(rf"{REGEX_PREFIX}craft\b\s+ruby\b\s+sword\b")
REGEX_COMMAND_COOLDOWNS = re.compile(rf"{REGEX_PREFIX}(?:cd\b|cooldowns\b)")
REGEX_COMMAND_DAILY = re.compile(rf"{REGEX_PREFIX}daily\b")
REGEX_COMMAND_DUEL = re.compile(rf"{REGEX_PREFIX}duel\b")
REGEX_COMMAND_DUNGEON_MINIBOSS = re.compile(rf"{REGEX_PREFIX}(?:dung\b|dungeon\b|miniboss\b)")
REGEX_COMMAND_ENCHANT = re.compile(rf"{REGEX_PREFIX}(?:enchant\b|refine\b|transmute\b|transcend\b)")
REGEX_COMMAND_EPIC_QUEST = re.compile(rf"{REGEX_PREFIX}epic\b\s+quest\b")
REGEX_COMMAND_EVENTS = re.compile(rf"{REGEX_PREFIX}events?\b")
REGEX_COMMAND_FARM = re.compile(rf"{REGEX_PREFIX}farm\b")
REGEX_COMMAND_FORGE_ULTRAEDGY_ARMOR = re.compile(rf"{REGEX_PREFIX}forge\b\s+ultra-edgy\b\s+armor\b")
REGEX_COMMAND_HEAL = re.compile(rf"{REGEX_PREFIX}heal\b")
REGEX_COMMAND_HF_LIGHTSPEED = re.compile(rf"{REGEX_PREFIX}hf\b\s+lightspeed\b")
REGEX_COMMAND_HORSE = re.compile(rf"{REGEX_PREFIX}horse\b\s+(?:breed\b|breeding\b|race\b)")
REGEX_COMMAND_HORSE_RACE = re.compile(rf"{REGEX_PREFIX}horse\b\s+race\b")
REGEX_COMMAND_HUNT = re.compile(rf'{REGEX_PREFIX}hunt\b')
REGEX_COMMAND_HUNT_ADVENTURE = re.compile(rf"{REGEX_PREFIX}(?:hunt\b|adv\b|adventure\b)")
REGEX_COMMAND_INVENTORY = re.compile(rf"{REGEX_PREFIX}(?:i\b|inv\b|inventory\b)")
REGEX_COMMAND_LOOTBOX = re.compile(rf"{REGEX_PREFIX}buy\s+[a-z]+\s+(?:lb\b|lootbox\b)")
REGEX_COMMAND_LOTTERY = re.compile(rf'{REGEX_PREFIX}(?:lottery\b|buy\b\s+lottery\b\s+ticket\b)')
REGEX_COMMAND_NSMB_BIGARENA = re.compile(rf"{REGEX_PREFIX}(?:big\b\s+arena\b|minintboss\b)")
REGEX_COMMAND_OMEGA_HORSE_TOKEN = re.compile(rf"{REGEX_PREFIX}use\b\s+omega\b\s+horse\b\s+token\b")
REGEX_COMMAND_OPEN = re.compile(rf"{REGEX_PREFIX}open\b")
REGEX_COMMAND_PETS_ADVENTURE_CLAIM = re.compile(rf"{REGEX_PREFIX}pets?\s+(?:adv\b|adventure\b)\s+claim\b")
REGEX_COMMAND_PETS_ADVENTURE_START = re.compile(rf"{REGEX_PREFIX}pets?\s+(?:adv\b|adventure\b)\s+(?:find\b|learn\b|drill\b)")
REGEX_COMMAND_PETS_ADVENTURE_CANCEL = re.compile(rf"{REGEX_PREFIX}pets?\s+(?:adv\b|adventure\b)\s+cancel\b")
REGEX_COMMAND_PETS_FUSION = re.compile(rf"{REGEX_PREFIX}pets?\b\s+fusion\b")
REGEX_COMMAND_PETS_TOURNAMENT = re.compile(rf"{REGEX_PREFIX}pets?\b\s+tournament\s+[a-z]+\b")
REGEX_COMMAND_QUEST = re.compile(rf'{REGEX_PREFIX}quest\b')
REGEX_COMMAND_QUEST_EPIC_QUEST = re.compile(rf"{REGEX_PREFIX}(?:epic\b\s+quest\b|quest\b)")
REGEX_COMMAND_PETS = re.compile(rf"{REGEX_PREFIX}pets?\b")
REGEX_COMMAND_SELL_RUBY = re.compile(rf"{REGEX_PREFIX}sell\b\s+ruby\b")
REGEX_COMMAND_SLEEPY_POTION = re.compile(rf"{REGEX_PREFIX}[a-z]+\s+use\b\s+sleepy\b\s+potion\b")
REGEX_COMMAND_TIME_TRAVEL = re.compile(rf"{REGEX_PREFIX}(?:super\b\s+)?time\b\s+travel\b")
REGEX_COMMAND_TRADE_RUBY = re.compile(rf"{REGEX_PREFIX}trade\b\s+[e-f]\b")
REGEX_COMMAND_TRAINING = re.compile(rf"{REGEX_PREFIX}(?:tr\b|training)")
REGEX_COMMAND_TRAINING_ULTRAINING = re.compile(rf"{REGEX_PREFIX}(?:ul)?(?:tr\b|training)")
REGEX_COMMAND_ULTRAINING = re.compile(rf"{REGEX_PREFIX}(?:ultr\b|ultraining)")
REGEX_COMMAND_VOTE = re.compile(rf"{REGEX_PREFIX}vote\b")
REGEX_COMMAND_WEEKLY = re.compile(rf"{REGEX_PREFIX}weekly\b")
REGEX_COMMAND_WORK = rf"{REGEX_PREFIX}(?:"
for command in WORK_COMMANDS:
    REGEX_COMMAND_WORK = fr'{REGEX_COMMAND_WORK}{command}\b|'
REGEX_COMMAND_WORK = re.compile(fr'{REGEX_COMMAND_WORK.strip("|")})')
