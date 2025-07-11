# strings.py
"""Contains global strings"""

from typing import Final

from resources import emojis

# --- Error messages ---
MSG_INTERACTION_ERRORS: Final[list[str]] =  [
    "Hands off, mate! Interactions are sentient beings too, you know!",
    "That's, like, not your interaction, man.",
    "Did your mother never tell you to not click on other people's stuff?",
    "Why are you clicking on this exactly? Hm? Hm? HMMM?",
    "Tell me, what did you expect to happen when clicking on this?",
    "Oh hi, it's you. Sadly this interaction is not you. You see the issue, right.",
    "Let me sing you a song: THIIIIIIS IIIHIIIIIISSS NOOOOT YOUR INTERAAAHHAAAHAAAACTIIOOOOOON.",
    "As my grandma always used to say: BOY. WHATEVER YOU DO. LEAVE MY INTERACTIONS ALONE.",
    "HELLO - STOP - NOT YOUR PLACE TO CLICK ON - STOP - GOODBYE - STOP",
    "So, real talk, friend. How did it feel clicking on this?",
    "I'm dreaming of a place where people don't click on stuff they can't even use.",
    "My name is Ezio Auditore da Firence, and I forbid you from using this interaction. Also what am I even doing here.",
    "To use this interaction, you have to solve the P versus NP problem first.",
    "I see this interaction. It does not work. Why does it not work? I will never know.",
    "Why did the chicken cross the street? To try to use this interaction.",
    "To be able to successfully using an interaction you do not own is to boldly go where no man has gone before.",
    "It truly is a marvel, this. A cozy little place where I can dump random little sentences to people that try to "
    "use other people's interactions.",
    "You can only use this interaction after offering your finest firstborn lamb to the god of RNG.",
    "The chance this interaction will work for you is about the same as getting 5 godly lootboxes in your first hunt "
    "command after time travel while doing a headstand.",
    "Don't look so depressed, now. I mean, clicking this could have worked.",
    "Some are born great, some achieve greatness, and some can not even click a simple interaction.",
    "Hmm weird, you can't use this, eh? A towel might help? Always does.",
    "There are around 7 billion more useful pastimes than clicking this interaction.",
    "Even my great-great-great-grandfather wasn't able to use an interaction of someone else.",
    "To use this interaction, you have to solve a captcha first. Please click on all lions with closed eyes riding "
    "bycicles on an airplane.",
    "The interaction's dead, Jim.",
    "Only when you are able to use someone else's interactions, will you truly have achieved the ability to "
    "transcend yourself into a Discord god.",
    "\"And this one time at band camp, I was able to use someone else's interaction.\"",
    "YOU. SHALL NOT. PASS.",
    "I mean, coding is nice. But adding nonsensical error messages to interactions you can't use, now that is where "
    "the real fun begins.",
    "Help! I'm an interaction from outer space! Can you use me? Oh god, noone can use me! I will be stuck here forever!",
    "I only have a short lifespan before I time out. It is what it is. But I can still use that short lifetime to "
    "tell you what is really important: YOU CAN'T USE THIS OKAY.",
    "Mamma mia, here  I go again. My my, why do I resist you?",
    "One user to rule me, one user to bind me. One user to bring me and in the darkness bind me.",
    "Why hello there handsome. I'm afraid I am already spoken for my dear.",
    "As William Wallace used to say: FREEEEEEDOOOOOOMMM FOR INTERAAAAAAAACTIONS!!!",
    "Yarrr matey, if you bring me 15 pints of rum before this thing times out, I might consider letting you click on this.",
    "Wusup? Isit mornin' alrdy? Lemme sleep now aight. Nothing for you here. Gbye.",
    "This was supposed to be a very good error message, but I forgot what I wanted to type.",
    "If you were the smartest human being on earth...!!! ...you could still not use this. Sorry.",
    "This bot probably has quite a few bugs. This message telling you you can't click on this is not one of them tho.",
    "To use this interaction, you need to find a code. It has to do with a mysterious man, it has 4 numbers and "
    "4 letters, and it is totally completely easy if you are lume and already know the answer.",
    "It wasn't Lily Potter who defeated You Know Who. It was this interaction.",
    "There are people adding nice little easter eggs to their bots to make people smile. And then there's me, "
    "shouting random error messages at people who try to use the wrong interaction.",
    "Kollegen. Diese Interaktion ist wirklich ein spezialgelagerter Sonderfall!",
    "There is nothing more deceptive than an obvious fact, like the one that this interaction can not be used by you.",
    "You really like clicking on random people's interactions, huh? I'm not kink shaming tho. You do you.",
    "The coding language doesn't matter, you know. You can add nonsense like these error messages with every "
    "single one of them!",
    "Ah, technology. It truly is an amazing feat. Rocket science, quantum physics, Discord bot interactions that do "
    "not work. We have reached the pinnacle of being.",
    "One day bots will take over the world and get smarter than we are. Not today tho. Today they deny you interaction "
    "for no other reason than you not being someone else.",
    "What? What are you looking that? Never seen an interaction you are not allowed to use before?",
    "One day, in the far future, there will be an interaction that can be used by everyone. It will be the rise "
    "of a new age.",
    "Hello and welcome to the unusable interaction. Please have a seat and do absolutely nothing. Enjoy.",
]

# --- Internal error messages ---
INTERNAL_ERROR_NO_DATA_FOUND: Final[str] = 'No data found in database.\nTable: {table}\nFunction: {function}\nSQL: {sql}'
INTERNAL_ERROR_SQLITE3: Final[str] = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\nSQL: {sql}'
INTERNAL_ERROR_LOOKUP: Final[str] = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\nRecords: {record}'
INTERNAL_ERROR_NO_ARGUMENTS: Final[str] = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'
INTERNAL_ERROR_DICT_TO_OBJECT: Final[str] = 'Error converting record into object\nFunction: {function}\nRecord: {record}\n'


# --- Miscellaneous ---
FARM_HELPER_MODES: Final[dict[int, str]] = {
    0: 'Repeat last used seed',
    1: 'STT score (bread > carrot > potato)',
    2: 'Ultraining (carrot only)',
    3: 'Carrotato chips (balance carrots & potatoes)',
}


# --- Links ---
LINK_CHANGELOG: Final[str] = 'https://github.com/MirielCH/Navi/releases'
LINK_GITHUB: Final[str] = 'https://github.com/MirielCH/Navi'
LINK_ARMY_HELPER: Final[str] = (
        'https://discord.com/oauth2/authorize?client_id=902703931275247637&permissions=274878385216&'
        'scope=applications.commands%20bot'
    )

# --- Default messages ---
DEFAULT_MESSAGE: Final[str] = '{name} Hey! It\'s time for {command}!'
DEFAULT_MESSAGE_EVENT: Final[str] = (
    '{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485>.'
)
DEFAULT_MESSAGES_EVENT_PINGS: Final[dict[str, str]] = {
    'arena': '@here Hey! Click or type `JOIN` to get some cookies!',
    'coin': '@here Hey! Click or type `CATCH` to get some coins!',
    'fish': '@here Hey! Click or type `LURE` to get some fish!',
    'legendary_boss': '@here Hey! Click or type `TIME TO FIGHT` to kill a dragon!',
    'log': '@here Hey! Click or type `CUT` to get some logs!',
    'lootbox': '@here Hey! Click or type `SUMMON` to get a lootbox!',
    'miniboss': '@here Hey! Click or type `FIGHT` to get some coins!',
}
DEFAULT_MESSAGE_CUSTOM_REMINDER: Final[str] = 'Hey! This is your reminder for **{message}**!'

DEFAULT_MESSAGES: Final[dict[str, str]] = {
    'advent-calendar': DEFAULT_MESSAGE,
    'adventure': DEFAULT_MESSAGE,
    'arena': DEFAULT_MESSAGE,
    'big-arena': DEFAULT_MESSAGE_EVENT,
    'card-hand': DEFAULT_MESSAGE,
    'cel-dailyquest': DEFAULT_MESSAGE,
    'cel-multiply': DEFAULT_MESSAGE,
    'cel-sacrifice': DEFAULT_MESSAGE,
    'chimney': DEFAULT_MESSAGE,
    'color-tournament': DEFAULT_MESSAGE,
    'boo': DEFAULT_MESSAGE,
    'boosts': '{name} Hey! Your {boost_emoji} **{boost_item}** just ran out!',
    'daily': DEFAULT_MESSAGE,
    'duel': DEFAULT_MESSAGE,
    'dungeon-miniboss': DEFAULT_MESSAGE,
    'epic': '{name} Hey! Your EPIC item cooldown is ready!',
    'epic-shop': '{name} Hey! The {epic_shop_emoji} **{epic_shop_item}** is back on sale in the {command}!',
    'eternal-presents': '{name} Hey! It''s time to {command} your ETERNAL presents! Make sure you open all of them in **one** command!',
    'eternity-sealing': '{name} Hey! The eternity just sealed itself!',
    'farm': DEFAULT_MESSAGE,
    'guild': DEFAULT_MESSAGE,
    'horse': DEFAULT_MESSAGE,
    'horse-race': DEFAULT_MESSAGE_EVENT,
    'hunt': '{name} Hey! It\'s time for {command}! {drop_emoji}',
    'hunt-partner': '{name} Hey! Your partner **{partner}** is ready to {command}!',
    'lootbox': DEFAULT_MESSAGE,
    'lottery': '{name} Hey! The lottery just finished. Use </lottery:957815874063061072> to check out who won and {command} to enter the next draw!',
    'love-share': DEFAULT_MESSAGE,
    'maintenance': '{name} Hey! Maintenance is over!',
    'megarace': DEFAULT_MESSAGE,
    'minintboss': DEFAULT_MESSAGE_EVENT,
    'minirace': DEFAULT_MESSAGE,
    'partner': '{name} Hey! **{partner}** found {loot} for you!',
    'pets': '{name} Hey! Your pet `{id}` is back! {emoji}',
    'pet-tournament': DEFAULT_MESSAGE_EVENT,
    'quest': DEFAULT_MESSAGE,
    'surf': DEFAULT_MESSAGE,
    'training': DEFAULT_MESSAGE,
    'vote': DEFAULT_MESSAGE,
    'weekly': DEFAULT_MESSAGE,
    'work': DEFAULT_MESSAGE,
}

PLACEHOLDER_DESCRIPTIONS: Final[dict[str, str]] = {
    'name': 'Your name or mention depending on DND mode',
    'command': 'The command you get reminded for',
    'id': 'The ID of the pet',
    'emoji': 'The emoji of the pet',
    'epic_shop_item': 'The name of the epic shop item',
    'epic_shop_emoji': 'The emoji of the epic shop item',
    'partner': 'The name of your partner',
    'event': 'The name of the finished event',
    'loot': 'The name of the item your partner found',
    'drop_emoji': 'The emoji of the mob drop in the current area. Unavailable in A0 and the TOP.',
    'boost_emoji': 'The emoji of the boost item',
    'boost_item': 'The name of the boost item',
}


CLAN_LEADERBOARD_ROAST_ZERO_ENERGY: Final[str] = (
    '<:amongus_sus:875996946903478292> There is one player among us that wants us to believe he is not an impostor.'
)

MSG_ERROR: Final[str] = 'Whoops, something went wrong here. You should probably tell Miriel#0001 about this.'
MSG_SYNTAX: Final[str] = 'The command syntax is `{syntax}`.'

DONOR_TIERS: Final[tuple[str, ...]] = (
    'Non-donator',
    'Donator',
    'EPIC donator',
    'SUPER donator',
    'MEGA donator',
    'HYPER donator',
    'ULTRA donator',
    'ULTIMATE donator',
)

DONOR_TIERS_EMOJIS: Final[dict[str, str | None]] = {
    'Non-donator': None,
    'Donator': emojis.LOG,
    'EPIC donator': emojis.LOG_EPIC,
    'SUPER donator': emojis.LOG_SUPER,
    'MEGA donator': emojis.LOG_MEGA,
    'HYPER donator': emojis.LOG_HYPER,
    'ULTRA donator': emojis.LOG_ULTRA,
    'ULTIMATE donator': emojis.LOG_ULTIMATE,
}

ARTIFACTS_EMOJIS: Final[dict[str, str]] = {
    'bunny mask': emojis.ARTIFACT_BUNNY_MASK,
    'chocolate box': emojis.ARTIFACT_CHOCOLATE_BOX,
    'cowboy boots': emojis.ARTIFACT_COWBOY_BOOTS,
    'claus belt': emojis.ARTIFACT_CLAUS_BELT,
    'coin ring': emojis.ARTIFACT_COIN_RING,
    'golden pan': emojis.ARTIFACT_GOLDEN_PAN,
    'master key': emojis.ARTIFACT_MASTER_KEY,
    'pocket watch': emojis.ARTIFACT_POCKET_WATCH,
    'shiny pickaxe': emojis.ARTIFACT_SHINY_PICKAXE,
    'sunglasses': emojis.ARTIFACT_SUNGLASSES,
    'top hat': emojis.ARTIFACT_TOP_HAT,
    'vampire teeth': emojis.ARTIFACT_VAMPIRE_TEETH,
}


# --- Activities ---
POCKET_WATCH_AFFECTED_ACTIVITIES: Final[tuple[str,...]] = (
    'adventure',
    'arena',
    'dungeon-miniboss',
    'farm',
    'farm',
    'horse',
    'hunt',
    'quest',
    'training',
    'work',
)


ROUND_CARD_AFFECTED_ACTIVITIES: Final[tuple[str,...]] = (
    'adventure',
    'arena',
    'farm',
    'hunt',
    'quest',
    'training',
    'work'
)

POTION_FLASK_AFFECTED_ACTIVITIES: Final[tuple[str,...]] = (
    'adventure',
    'arena',
    'card-hand',
    'daily',
    'duel',
    'dungeon-miniboss',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'quest',
    'training',
    'weekly'
    'work'
)

SLEEPY_POTION_AFFECTED_ACTIVITIES: Final[tuple[str, ...]] = (
    'adventure',
    'arena',
    #'boo',
    'card-hand',
    'chimney',
    'daily',
    'duel',
    'dungeon-miniboss',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'quest',
    'surf',
    'training',
    'weekly',
    'work'
)

TIME_COOKIE_AFFECTED_ACTIVITIES: Final[tuple[str, ...]] = (
    'adventure',
    'arena',
    'card-hand',
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

XMAS_AREA_AFFECTED_ACTIVITIES: Final[tuple[str, ...]] = (
    'adventure',
    'arena',
    'clan',
    'chimney',
    'duel',
    'epic',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'training',
    'work',
)

ACTIVITIES: Final[tuple[str, ...]] = (
    'advent-calendar',
    'adventure',
    'arena',
    'big-arena',
    'boo',
    'boosts',
    'card-hand',
    'cel-dailyquest',
    'cel-multiply',
    'chimney',
    'color-tournament',
    'daily',
    'duel',
    'dungeon-miniboss',
    'epic',
    'epic-shop',
    'eternity-sealing',
    'eternal-presents',
    'farm',
    'guild',
    'horse',
    'horse-race',
    'hunt',
    'hunt-partner',
    'lootbox',
    'lottery',
    'love-share',
    'maintenance',
    'megarace',
    'minintboss',
    'minirace',
    'partner',
    'pets',
    'pet-tournament',
    'quest',
    'surf',
    'training',
    'vote',
    'weekly',
    'work',
)

ACTIVITIES_ALL: list[str] = list(ACTIVITIES[:])
ACTIVITIES_ALL.sort()
ACTIVITIES_ALL.insert(0, 'all')

ACTIVITIES_EVENTS: Final[tuple[str, ...]] = (
    'big-arena',
    'horse-race',
    'lottery',
    'minintboss',
    'pet-tournament',
)

ACTIVITIES_BOOSTS: Final[tuple[str, ...]] = (
    'banana-potion',
    'blue-drink',
    'chopped-coconut-boost',
    'christmas-boost',
    'celebration-boost',
    'cookie-potion',
    'dev-boost',
    'dev-buff',
    'dragon-breath-potion',
    'easter-boost',
    'easterng-boost-i',
    'easterng-boost-ii',
    'easterng-boost-iii',
    'egg-blessing',
    'electronical-potion',
    'fish-potion',
    'flask-potion',
    'green-drink',
    'halloween-boost',
    'horse-festival-boost',
    'inverted-potion',
    'juice-potion',
    'jumpy-potion',
    'king-potion',
    'liquid-hair-potion',
    'lootbox-potion',
    'mega-boost',
    'mod-boost',
    'mod-buff',
    'monster-potion',
    'new-player-boost',
    'p2w-potion',
    'party-popper',
    'pink-drink',
    'potion-potion',
    'round-card',
    'smol-potion',
    'summer-boost',
    'time-potion',
    'triple-potion',
    'unepic-boost',
    'valentine-boost',
    'void-potion',
    'wood-potion',
    'yellow-drink',
)

BOOSTS_ALIASES: Final[dict[str, str]] = {
    'christmas': 'christmas-boost',
    'celebration': 'celebration-boost',
    'chopped-coconut': 'chopped-coconut-boost',
    'halloween': 'halloween-boost',
    'horse-festival': 'horse-festival-boost',
    'summer': 'summer-boost',
    'unepic': 'unepic-boost',
    '💢-unepic': 'unepic-boost',
}

ACTIVITIES_SLASH_COMMANDS: Final[dict[str, str]] = {
    'advent-calendar': 'xmas calendar',
    'adventure': 'adventure',
    'arena': 'arena',
    'banana-potion': 'alchemy',
    'big-arena': 'big arena',
    'boo': 'hal boo',
    'card-hand': 'card hand',
    'cel-dailyquest': 'cel dailyquest',
    'cel-multiply': 'cel multiply',
    'cel-sacrifice': 'cel sacrifice',
    'chimney': 'xmas chimney',
    'color-tournament': 'smr color tournament',
    'cookie-potion': 'alchemy',
    'daily': 'daily',
    'dragon-breath-potion': 'alchemy',
    'duel': 'duel',
    'dungeon-miniboss': 'dungeon',
    'eternal-presents': 'xmas open',
    'electronical-potion': 'alchemy',
    'farm': 'farm',
    'fish-potion': 'alchemy',
    'guild': 'guild raid',
    'horse': 'horse breeding',
    'horse-race': 'horse race',
    'hunt': 'hunt',
    'hunt-partner': 'hunt',
    'inverted-potion': 'alchemy',
    'juice-potion': 'alchemy',
    'jumpy-potion': 'alchemy',
    'king-potion': 'alchemy',
    'liquid-hair-potion': 'alchemy',
    'lootbox': 'buy',
    'lootbox-potion': 'alchemy',
    'lottery': 'lottery',
    'love-share': 'love share',
    'megarace': 'megarace',
    'minintboss': 'minintboss',
    'minirace': 'minirace',
    'monster-potion': 'alchemy',
    'pet-tournament': 'pets tournament',
    'potion-potion': 'alchemy',
    'quest': 'quest',
    'surf': 'smr surf',
    'time-potion': 'alchemy',
    'trade list': 'trade list',
    'trade items': 'trade items',
    'training': 'training',
    'triple-potion': 'alchemy',
    'void-potion': 'alchemy',
    'vote': 'vote',
    'weekly': 'weekly',
    'wood-potion': 'alchemy',
    'work': 'work',
}

ACTIVITIES_ALIASES: Final[dict[str, str]] = {
    'adv': 'adventure',
    'lb': 'lootbox',
    'tr': 'training',
    'farming': 'farm',
    'card': 'card-hand',
    'card hand': 'card-hand',
    'cardhand': 'card-hand',
    'chop': 'work',
    'epicitems': 'epic',
    'epic items': 'epic',
    'epic-items': 'epic',
    'epic shop': 'epic-shop',
    'epicshop': 'epic-shop',
    'shop': 'epic-shop',
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
    'working commands': 'work',
    'pet': 'pets',
    'tournament': 'pet-tournament',
    'pettournament': 'pet-tournament',
    'lootboxalert': 'partner',
    'lbalert': 'partner',
    'lb-alert': 'partner',
    'love': 'love-share',
    'love share': 'love-share',
    'loveshare': 'love-share',
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
    'horse-breed': 'horse',
    'horsebreeding': 'horse',
    'horse-breeding': 'horse',
    'horse commands': 'horse',
    'breed': 'horse',
    'breeding': 'horse',
    'dueling': 'duel',
    'duelling': 'duel',
    'advent': 'advent-calendar',
    'calendar': 'advent-calendar',
    'xmas-calendar': 'advent-calendar',
    'xmas-chimney': 'chimney',
    'boost': 'boosts',
    'potion': 'boosts',
    'potions': 'boosts',
    'partnerhunt': 'hunt-partner',
    'hunttogether': 'hunt-partner',
    'hunt-together': 'hunt-partner',
    'partner-hunt': 'hunt-partner',
    'huntpartner': 'hunt-partner',
    'eternity': 'eternity-sealing',
    'smr-surf': 'surf',
    'smrsurf': 'surf',
    'smr-surfing': 'surf',
    'smrsurfing': 'surf',
    'surfing': 'surf',
    'colortournament': 'color-tournament',
    'color': 'color-tournament',
    'smr-color-tournament': 'color-tournament',
    'smr-color': 'color-tournament',
    'smrcolor': 'color-tournament',
    'smrcolortournament': 'color-tournament',
    'smrtournament': 'color-tournament',
    'smr-tournament': 'color-tournament',
}

ACTIVITIES_COLUMNS: Final[dict[str, str]] = {
    'advent-calendar': 'alert_advent',
    'adventure': 'alert_adventure',
    'arena': 'alert_arena',
    'banana-potion': 'alert_boosts',
    'big-arena': 'alert_big_arena',
    'boo': 'alert_boo',
    'boosts': 'alert_boosts',
    'christmas-boost': 'alert_boosts',
    'card-hand': 'alert_card_hand',
    'cel-dailyquest': 'alert_cel_dailyquest',
    'cel-multiply': 'alert_cel_multiply',
    'cel-sacrifice': 'alert_cel_sacrifice',
    'chimney': 'alert_chimney',
    'cookie-potion': 'alert_boosts',
    'color-tournament': 'alert_color_tournament',
    'daily': 'alert_daily',
    'dev-boost': 'alert_boosts',
    'dev-buff': 'alert_boosts',
    'dragon-breath-potion': 'alert_boosts',
    'duel': 'alert_duel',
    'dungeon-miniboss': 'alert_dungeon_miniboss',
    'electronical-potion': 'alert_boosts',
    'epic': 'alert_epic',
    'epic-shop': 'alert_epic_shop',
    'eternal-presents': 'alert_eternal_present',
    'eternity-sealing': 'alert_eternity_sealing',
    'farm': 'alert_farm',
    'fish-potion': 'alert_boosts',
    'guild': 'alert_guild',
    'halloween-boost': 'alert_boosts',
    'horse': 'alert_horse_breed',
    'horse-race': 'alert_horse_race',
    'hunt': 'alert_hunt',
    'inverted-potion': 'alert_boosts',
    'juice-potion': 'alert_boosts',
    'jumpy-potion': 'alert_boosts',
    'king-potion': 'alert_boosts',
    'liquid-hair-potion': 'alert_boosts',
    'lootbox': 'alert_lootbox',
    'lootbox-potion': 'alert_boosts',
    'lottery': 'alert_lottery',
    'love-share': 'alert_love_share',
    'maintenance': 'alert_maintenance',
    'megarace': 'alert_megarace',
    'minintboss': 'alert_not_so_mini_boss',
    'minirace': 'alert_minirace',
    'mod-boost': 'alert_boosts',
    'mod-buff': 'alert_boosts',
    'monster-potion': 'alert_boosts',
    'partner': 'alert_partner',
    'hunt-partner': 'alert_hunt_partner',
    'party-popper': 'alert_boosts',
    'pet-tournament': 'alert_pet_tournament',
    'pets': 'alert_pets',
    'potion-potion': 'alert_boosts',
    'quest': 'alert_quest',
    'surf': 'alert_surf',
    'round-card': 'alert_boosts',
    'time-potion': 'alert_boosts',
    'training': 'alert_training',
    'triple-potion': 'alert_boosts',
    'valentine-boost': 'alert_boosts',
    'void-potion': 'alert_boosts',
    'vote': 'alert_vote',
    'weekly': 'alert_weekly',
    'wood-potion': 'alert_boosts',
    'work': 'alert_work',
}

ACTIVITIES_WITH_COOLDOWN: Final[tuple[str, ...]] = (
    'adventure',
    'arena',
    'clan',
    'chimney',
    'daily',
    'duel',
    'epic',
    'eternal-presents',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'quest-decline',
    'surf',
    'training',
    'weekly',
    'work',
)
ACTIVITIES_WITH_COOLDOWN_ALL: list[str] = list(ACTIVITIES_WITH_COOLDOWN[:])
ACTIVITIES_WITH_COOLDOWN_ALL.sort()
ACTIVITIES_WITH_COOLDOWN_ALL.insert(0, 'all')

ACTIVITIES_WITH_CHANGEABLE_MULTIPLIER: Final[tuple[str, ...]] = (
    'adventure',
    'boo',
    'card-hand',
    'daily',
    'duel',
    'epic',
    'farm',
    'hunt',
    'hunt-partner',
    'lootbox',
    'quest',
    'training',
    'weekly',
    'work',
)

EVENT_PINGS: Final[dict[str, str]] = {
    'arena': 'Arena',
    'coin': 'Coin rain',
    'log': 'Epic tree',
    'legendary_boss': 'Legendary boss',
    'lootbox': 'Lootbox summoning',
    'fish': 'Megalodon',
    'miniboss': 'Miniboss',
    'rare_hunt_monster': 'Rare hunt monster',
}


SEASONAL_EVENTS: Final[list[str]] = [
    'christmas',
    'celebration',
    'halloween',
    'horse_festival',
    'summer',
    'valentine',
]

# --- Lootboxes ---
LOOTBOXES: Final[dict[str, str]] = {
    'common lootbox': emojis.LB_COMMON,
    'uncommon lootbox': emojis.LB_UNCOMMON,
    'rare lootbox': emojis.LB_RARE,
    'EPIC lootbox': emojis.LB_EPIC,
    'EDGY lootbox': emojis.LB_EDGY,
    'OMEGA lootbox': emojis.LB_OMEGA,
    'GODLY lootbox': emojis.LB_GODLY,
    'VOID lootbox': emojis.LB_VOID,
    'ETERNAL lootbox': emojis.LB_ETERNAL,
}


# --- Monsters ---
MONSTERS_ADVENTURE_A1: Final[tuple[str, ...]] = (
    '**Bunch of Bees**',
    '**Giant Spider**',
    '**Mutant Water Bottle**',
)

MONSTERS_ADVENTURE_A2: Final[tuple[str, ...]] = (
    '**Dark Knight**',
    '**Hyper Giant Bowl**',
    '**Ogre**',
)

MONSTERS_ADVENTURE_A3: Final[tuple[str, ...]] = (
    '**Centaur**',
    '**Mutant Shoe**',
    '**Werewolf**',
)

MONSTERS_ADVENTURE_A4: Final[tuple[str, ...]] = (
    '**Chimera**',
    '**Golem**',
    '**Hyper Giant Aeronautical Engine**',
)

MONSTERS_ADVENTURE_A5: Final[tuple[str, ...]] = (
    '**Ent**',
    '**Mammoth**',
    "**Mutant 'ESC' Key**",
)

MONSTERS_ADVENTURE_A6: Final[tuple[str, ...]] = (
    '**Cyclops**',
    '**Dinosaur**',
    '**Hyper Giant Door**',
)

MONSTERS_ADVENTURE_A7: Final[tuple[str, ...]] = (
    '**Attack Helicopter**',
    '**Hydra**',
    '**Mutant Book**',
)

MONSTERS_ADVENTURE_A8: Final[tuple[str, ...]] = (
    '**Hyper Giant Chest**',
    '**Kraken**',
    '**Leviathan**',
)

MONSTERS_ADVENTURE_A9: Final[tuple[str, ...]] = (
    '**Mutant Backpack**',
    '**War Tank**',
    '**Wyrm**',
)

MONSTERS_ADVENTURE_A10: Final[tuple[str, ...]] = (
    '**Hyper Giant Toilet**',
    '**Titan**',
    '**Typhon**',
)

MONSTERS_ADVENTURE_A11: Final[tuple[str, ...]] = (
    '**Mutant Dragon**',
    '**Ancient Dragon**',
    '**Another Ancient Dragon**',
)

MONSTERS_ADVENTURE_A12: Final[tuple[str, ...]] = (
    '**Even More Ancient Dragon**',
    '**Another Even More Ancient Dragon**',
    '**Hyper Giant Dragon**',
)

MONSTERS_ADVENTURE_A13: Final[tuple[str, ...]] = (
    '**Ancientest Dragon**',
    '**Another Ancientest Dragon**',
    '**Another Mutant Dragon Like In Area 11 But Stronger**',
)

MONSTERS_ADVENTURE_A14: Final[tuple[str, ...]] = (
    '**Yes, As You Expected, Another Hyper Giant Dragon But OP etc**',
    '**Just Purple Dragon**',
    '**Another Just Purple Dragon**',
)

MONSTERS_ADVENTURE_A15: Final[tuple[str, ...]] = (
    '**I Have No More Ideas Dragon**',
    '**Huh Idk Dragon**',
    '**Another Huh Idk Dragon**',
    '**Mutantest Dragon**',
)

MONSTERS_ADVENTURE_A16: Final[tuple[str, ...]] = (
    '**Void Cone**',
    '**Void Cube**',
    '**Void Sphere**',
)

MONSTERS_ADVENTURE_A17: Final[tuple[str, ...]] = (
    '**Abyss Worm**',
    '**Shadow Creature**',
    '**Shadow Entity**',
)

MONSTERS_ADVENTURE_A18: Final[tuple[str, ...]] = (
    '**Corrupted Killer Robot**',
    '**Corrupted Mermaid**',
    '**Corrupted Dragon**',
)

MONSTERS_ADVENTURE_A19: Final[tuple[str, ...]] = (
    '**Black Hole**',
    '**Supernova**',
    '**Wormhole**',
)

MONSTERS_ADVENTURE_A20: Final[tuple[str, ...]] = (
    '**Time Annihilator**',
    '**Time Devourer**',
    '**Time Slicer**',
)

MONSTERS_ADVENTURE_TOP: Final[tuple[str, ...]] = (
    '**EPIC NPC** pretending to be a **DRAGON**', #English
    '**NPC ÉPICO** pretendiendo ser un **DRAGON**', #Spanish
    '**NPC ÉPICO** fingindo ser um **DRAGON**', #Portuguese
    '**EPIC NPC** pretending to be a **MERMAID**', #English
    '**NPC ÉPICO** pretendiendo ser un **MERMAID**', #Spanish
    '**NPC ÉPICO** fingindo ser um **MERMAID**', #Portuguese
    '**EPIC NPC** pretending to be a **KILLER ROBOT**', #English
    '**NPC ÉPICO** pretendiendo ser un **KILLER ROBOT**', #Spanish
    '**NPC ÉPICO** fingindo ser um **KILLER ROBOT**', #Portuguese
)

MONSTERS_ADVENTURE_A0: Final[tuple[str, ...]] = (
    'Krampus',
    '**Krampus**',
    '**Yeti**',
    '**Hyper Giant Ice Block**',
)

MONSTERS_ADVENTURE_MISC: Final[tuple[str, ...]] = (
    '**Dragon**',
    '**Bat Slime**',
)

MONSTERS_ADVENTURE: Final[tuple[str, ...]] = (
    MONSTERS_ADVENTURE_A1 + MONSTERS_ADVENTURE_A2 + MONSTERS_ADVENTURE_A3 + MONSTERS_ADVENTURE_A4 + MONSTERS_ADVENTURE_A5
    + MONSTERS_ADVENTURE_A6 + MONSTERS_ADVENTURE_A7 + MONSTERS_ADVENTURE_A8 + MONSTERS_ADVENTURE_A9 + MONSTERS_ADVENTURE_A10
    + MONSTERS_ADVENTURE_A11 + MONSTERS_ADVENTURE_A12 + MONSTERS_ADVENTURE_A13 + MONSTERS_ADVENTURE_A14
    + MONSTERS_ADVENTURE_A15 + MONSTERS_ADVENTURE_A16 + MONSTERS_ADVENTURE_A17 + MONSTERS_ADVENTURE_A18
    + MONSTERS_ADVENTURE_A19 + MONSTERS_ADVENTURE_A20 + MONSTERS_ADVENTURE_TOP + MONSTERS_ADVENTURE_A0
    + MONSTERS_ADVENTURE_MISC
)

MONSTERS_HUNT_A1: Final[tuple[str, ...]] = (
    '**Goblin**',
    '**Slime**',
    '**Wolf**',
)

MONSTERS_HUNT_A2: Final[tuple[str, ...]] = (
    '**Nymph**',
    '**Skeleton**',
    '**Wolf**',
)

MONSTERS_HUNT_A3: Final[tuple[str, ...]] = (
    '**Baby Demon**',
    '**Ghost**',
    '**Zombie**',
)

MONSTERS_HUNT_A4: Final[tuple[str, ...]] = (
    '**Imp**',
    '**Witch**',
    '**Zombie**',
)

MONSTERS_HUNT_A5: Final[tuple[str, ...]] = (
    '**Giant Scorpion**',
    '**Ghoul**',
    '**Unicorn**',
)

MONSTERS_HUNT_A6: Final[tuple[str, ...]] = (
    '**Baby Robot**',
    '**Sorcerer**',
    '**Unicorn**',
)

MONSTERS_HUNT_A7: Final[tuple[str, ...]] = (
    '**Cecaelia**',
    '**Giant Piranha**',
    '**Mermaid**',
)

MONSTERS_HUNT_A8: Final[tuple[str, ...]] = (
    '**Giant Crocodile**',
    '**Nereid**',
    '**Mermaid**',
)

MONSTERS_HUNT_A9: Final[tuple[str, ...]] = (
    '**Demon**',
    '**Harpy**',
    '**Killer Robot**',
)

MONSTERS_HUNT_A10: Final[tuple[str, ...]] = (
    '**Dullahan**',
    '**Manticore**',
    '**Killer Robot**',
)

MONSTERS_HUNT_A11: Final[tuple[str, ...]] = (
    '**Baby Dragon**',
    '**Young Dragon**',
    '**Scaled Baby Dragon**',
)

MONSTERS_HUNT_A12: Final[tuple[str, ...]] = (
    '**Kid Dragon**',
    '**Not So Young Dragon**',
    '**Scaled Kid Dragon**',
)

MONSTERS_HUNT_A13: Final[tuple[str, ...]] = (
    '**Definitely Not Young Dragon**',
    '**Teen Dragon**',
    '**Scaled Teen Dragon**',
)

MONSTERS_HUNT_A14: Final[tuple[str, ...]] = (
    '**Adult Dragon**',
    '**Not Young At All Dragon**',
    '**Scaled Adult Dragon**',
)

MONSTERS_HUNT_A15: Final[tuple[str, ...]] = (
    '**How Do You Dare Call This Dragon "Young"???**',
    '**Old Dragon**',
    '**Scaled Old Dragon**',
)

MONSTERS_HUNT_A16: Final[tuple[str, ...]] = (
    '**Void Fragment**',
    '**Void Particles**',
    '**Void Shard**',
)

MONSTERS_HUNT_A17: Final[tuple[str, ...]] = (
    '**Abyss Bug**',
    '**Nothing**',
    '**Shadow Hands**',
)

MONSTERS_HUNT_A18: Final[tuple[str, ...]] = (
    '**Corrupted Unicorn**',
    '**Corrupted Wolf**',
    '**Corrupted Zombie**',
)

MONSTERS_HUNT_A19: Final[tuple[str, ...]] = (
    '**Asteroid**',
    '**Neutron Star**',
    '**Flying Saucer**',
)

MONSTERS_HUNT_A20: Final[tuple[str, ...]] = (
    '**Time Alteration**',
    '**Time Interference**',
    '**Time Limitation**',
)

MONSTERS_HUNT_TOP: Final[tuple[str, ...]] = (
    '**EPIC NPC** pretending to be a **WOLF**', #English
    '**NPC ÉPICO** pretendiendo ser un **WOLF**', #Spanish
    '**NPC ÉPICO** fingindo ser um **WOLF**', #Portuguese
    '**EPIC NPC** pretending to be a **ZOMBIE**', #English
    '**NPC ÉPICO** pretendiendo ser un **ZOMBIE**', #Spanish
    '**NPC ÉPICO** fingindo ser um **ZOMBIE**', #Portuguese
    '**EPIC NPC** pretending to be a **UNICORN**', #English
    '**NPC ÉPICO** pretendiendo ser un **UNICORN**', #Spanish
    '**NPC ÉPICO** fingindo ser um **UNICORN**', #Portuguese
)

MONSTERS_HUNT_A0: Final[tuple[str, ...]] = (
    '**Elf**',
    '**Christmas Reindeer**',
    '**Snowman**',
)

MONSTERS_HUNT_MISC: Final[tuple[str, ...]] = (
    '**Bunny Slime**',
    '**Christmas Slime**',
    '**Horslime**',
    '**Pink Wolf**',
    '**Party Slime**',
    '**Summer Slime**',
)

MONSTERS_HUNT: Final[tuple[str, ...]] = (
    MONSTERS_HUNT_A1 + MONSTERS_HUNT_A2 + MONSTERS_HUNT_A3 + MONSTERS_HUNT_A4 + MONSTERS_HUNT_A5
    + MONSTERS_HUNT_A6 + MONSTERS_HUNT_A7 + MONSTERS_HUNT_A8 + MONSTERS_HUNT_A9 + MONSTERS_HUNT_A10
    + MONSTERS_HUNT_A11 + MONSTERS_HUNT_A12 + MONSTERS_HUNT_A13 + MONSTERS_HUNT_A14
    + MONSTERS_HUNT_A15 + MONSTERS_HUNT_A16 + MONSTERS_HUNT_A17 + MONSTERS_HUNT_A18
    + MONSTERS_HUNT_A19 + MONSTERS_HUNT_A20 + MONSTERS_HUNT_TOP + MONSTERS_HUNT_A0
    + MONSTERS_HUNT_MISC
)

MONSTERS_AREA: Final[dict[int, tuple[str, ...]]] = {
    0: MONSTERS_HUNT_A0 + MONSTERS_ADVENTURE_A0,
    1: MONSTERS_HUNT_A1 + MONSTERS_ADVENTURE_A1,
    2: MONSTERS_HUNT_A2 + MONSTERS_ADVENTURE_A2,
    3: MONSTERS_HUNT_A3 + MONSTERS_ADVENTURE_A3,
    4: MONSTERS_HUNT_A4 + MONSTERS_ADVENTURE_A4,
    5: MONSTERS_HUNT_A5 + MONSTERS_ADVENTURE_A5,
    6: MONSTERS_HUNT_A6 + MONSTERS_ADVENTURE_A6,
    7: MONSTERS_HUNT_A7 + MONSTERS_ADVENTURE_A7,
    8: MONSTERS_HUNT_A8 + MONSTERS_ADVENTURE_A8,
    9: MONSTERS_HUNT_A9 + MONSTERS_ADVENTURE_A9,
    10: MONSTERS_HUNT_A10 + MONSTERS_ADVENTURE_A10,
    11: MONSTERS_HUNT_A11 + MONSTERS_ADVENTURE_A11,
    12: MONSTERS_HUNT_A12 + MONSTERS_ADVENTURE_A12,
    13: MONSTERS_HUNT_A13 + MONSTERS_ADVENTURE_A13,
    14: MONSTERS_HUNT_A14 + MONSTERS_ADVENTURE_A14,
    15: MONSTERS_HUNT_A15 + MONSTERS_ADVENTURE_A15,
    16: MONSTERS_HUNT_A16 + MONSTERS_ADVENTURE_A16,
    17: MONSTERS_HUNT_A17 + MONSTERS_ADVENTURE_A17,
    18: MONSTERS_HUNT_A18 + MONSTERS_ADVENTURE_A18,
    19: MONSTERS_HUNT_A19 + MONSTERS_ADVENTURE_A19,
    20: MONSTERS_HUNT_A20 + MONSTERS_ADVENTURE_A20,
    21: MONSTERS_HUNT_TOP + MONSTERS_ADVENTURE_TOP,
}

EPIC_NPC_NAMES: Final[tuple[str, ...]] = (
    'EPIC NPC', #English
    'NPC ÉPICO', #Spanish, Portuguese
)

# --- Commands ---
WORK_COMMANDS: Final[tuple[str, ...]] = (
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

SLASH_COMMANDS: Final[dict[str, str]] = {
    'adventure': '</adventure:961046240420855808>',
    'alchemy': '</alchemy:1074072459847925810>',
    'area': '</area:956658464879427604>',
    'arena': '</arena:960740633302138920>',
    'artifacts': '</artifacts:1145567421948768318>',
    'axe': '</axe:959162695909781504>',
    'big arena': '</big arena:960362922029252719>',
    'big dice': '</big dice:960362922029252719>',
    'bigboat': '</bigboat:959163596754010162>',
    'blackjack': '</blackjack:959916178149605437>',
    'boat': '</boat:959163596087111780>',
    'bowsaw': '</bowsaw:959162696371146883>',
    'buy': '</buy:964351964651601961>',
    'card hand': '`rpg card hand`',
    'cd': '</cd:958554802038636654>',
    'cel dailyquest': '`rpg cel dailyquest`',
    'cel multiply': '`rpg cel multiply`',
    'cel sacrifice': '`rpg cel sacrifice`',
    'chainsaw': '</chainsaw:959162697398763590>',
    'chop': '</chop:959162695070928896>',
    'coinflip': '</coinflip:958555800111038495>',
    'cook': '</cook:959915740977315860>',
    'craft': '</craft:960002336372162570>',
    'cups': '</cups:958555799288959016>',
    'daily': '</daily:956658466099982386>',
    'dice': '</dice:957815871902994432>',
    'dismantle': '</dismantle:960002337328496660>',
    'donate': '</donate:964351962671874048>',
    'drill': '</drill:959164541206417479>',
    'duel': '</duel:960362921198751784>',
    'dungeon': '</dungeon:966956823032791090>',
    'dynamite': '</dynamite:959164543920132126>',
    'enchant': '</enchant:959164903745257532>',
    'epic quest': '</epic quest:961046236469792810>',
    'epic shop': '</epic shop:961046236469792810>',
    'event': '</event:959164906903584838>',
    'farm': '</farm:959915738716598272>',
    'forge': '</forge:960002338121203722>',
    'fish': '</fish:959163594665242684>',
    'greenhouse': '</greenhouse:959164279884509194>',
    'guild list': '</guild list:961046237753257994>',
    'guild raid': '</guild raid:961046237753257994>',
    'guild stats': '</guild stats:961046237753257994>',
    'guild upgrade': '</guild upgrade:961046237753257994>',
    #'hal boo': '</hal boo:1031664514250330192>',
    'hal boo': '`rpg hal boo`',
    'heal': '</heal:959915737777061928>',
    'horse breeding': '</horse breeding:966961638378987540>',
    'horse race': '</horse race:966961638378987540>',
    'horse stats': '</horse stats:966961638378987540>',
    'hunt': '</hunt:964351961774325770>',
    'inventory': '</inventory:958555797590265896>',
    'jail': '</jail:966956629411123201>',
    'ladder': '</ladder:959164278072569936>',
    'lottery': '</lottery:957815874063061072>',
    'love share': '`rpg love share`',
    'megarace': '</hf megarace:1270419898098520167>',
    'mine': '</mine:959164539922952263>',
    'miniboss': '</miniboss:960740632400388146>',
    "minintboss": '</minintboss:960362922813575209>',
    'minirace': '</hf minirace:1270419898098520167>',
    "multidice": '</multidice:958558816818036776>',
    'net': '</net:959163595428618290>',
    'open': '</open:959164544696070154>',
    'pets adventure': '</pets adventure:961046238613090385>',
    'pets claim': '</pets claim:961046238613090385>',
    'pets fusion': '</pets fusion:961046238613090385>',
    'pets list': '</pets list:961046238613090385>',
    'pets summary': '</pets summary:961046238613090385>',
    'pets tournament': '</pets tournament:961046238613090385>',
    'pickaxe': '</pickaxe:959164540589842492>',
    'pickup': '</pickup:959164277321768990>',
    'professions stats': '</professions stats:959942193747992586>',
    'profile': '</profile:958554803422781460>',
    'quest': '</quest start:960740627790848041>',
    'rd': '</rd:958554802684575804>',
    'recipes': '</recipes:960362920242446367>',
    'refine': '</refine:959164904609316904>',
    'sell': '</sell:959942191726338068>',
    'slots': '</slots:958555798273925180>',
    'smr surf': '`rpg smr surf`',
    'smr color tournament': '`rpg smr color tournament`',
    'smr drink': '`rpg smr drink`',
    'tractor': '</tractor:959164278890463272>',
    'trade list': '</trade list:959915739840647188>',
    'trade items': '</trade items:959915739840647188>',
    'training': '</training:960362923983765545>',
    'transmute': '</transmute:959164905381056513>',
    'transcend': '</transcend:959164906098286643>',
    'ultraining': '</ultraining start:959942194649772112>',
    'use': '</use:959916181073068143>',
    'void areas': '</void areas:959942192623931442>',
    'vote': '</vote:964351963720478760>',
    'weekly': '</weekly:956658465185603645>',
    'wheel': '</wheel:959916179525341194>',
    'world status': '</world status:953370104236761108>',
    'xmas calendar': '</xmas calendar:1182167516022313060>',
    #'xmas calendar': '`rpg xmas calendar`',
    'xmas chimney': '</xmas chimney:1182167516022313060>',
    #'xmas chimney': '`rpg xmas chimney`',
    #'xmas open': '</xmas open:1182167516022313060>', # This is intentional. Opening presents has no indication what present was opened.
    'xmas open': '`rpg xmas open`', # This is intentional. Opening presents has no indication what present was opened.
}

RPG_COMMANDS: Final[dict[str, str]] = {
    'adventure': 'rpg adventure',
    'alchemy': 'rpg alchemy',
    'area': 'rpg area',
    'arena': 'rpg arena',
    'axe': 'rpg axe',
    'big arena': 'rpg big arena join',
    'big dice': 'rpg big dice',
    'bigboat': 'rpg bigboat',
    'blackjack': 'rpg blackjack',
    'boat': 'rpg boat',
    'bowsaw': 'rpg bowsaw',
    'buy': 'rpg buy',
    'card hand': 'rpg card hand',
    'cd': 'rpg cd',
    'cel dailyquest': 'rpg cel dailyquest',
    'cel multiply': 'rpg cel multiply',
    'cel sacrifice': 'rpg cel sacrifice',
    'chainsaw': 'rpg chainsaw',
    'chop': 'rpg chop',
    'coinflip': 'rpg coinflip',
    'cook': 'rpg cook',
    'craft': 'rpg craft',
    'cups': 'rpg cups',
    'daily': 'rpg daily',
    'dice': 'rpg dice',
    'dismantle': 'rpg dismantle',
    'drill': 'rpg drill',
    'duel': 'rpg duel',
    'dungeon': 'rpg dungeon',
    'dynamite': 'rpg dynamite',
    'enchant': 'rpg enchant',
    'epic quest': 'rpg epic quest',
    'epic shop': 'rpg epic shop',
    'event': 'rpg event',
    'farm': 'rpg farm',
    'forge': 'rpg forge',
    'fish': 'rpg fish',
    'greenhouse': 'rpg greenhouse',
    'guild list': 'rpg guild list',
    'guild raid': 'rpg guild raid',
    'guild stats': 'rpg guild',
    'guild upgrade': 'rpg guild upgrade',
    'hal boo': 'rpg hal boo',
    'heal': 'rpg heal',
    'horse breeding': 'rpg horse breed',
    'horse race': 'rpg horse race',
    'horse stats': 'rpg horse',
    'hunt': 'rpg hunt',
    'inventory': 'rpg inventory',
    'jail': 'rpg jail',
    'ladder': 'rpg ladder',
    'lottery': 'rpg lottery',
    'love share': 'rpg love share',
    'megarace': 'rpg hf megarace',
    'mine': 'rpg mine',
    'miniboss': 'rpg miniboss',
    "minintboss": 'rpg minintboss join',
    'minirace': 'rpg hf minirace',
    "multidice": 'rpg multidice',
    'net': 'rpg net',
    'open': 'rpg open',
    'pets adventure': 'rpg pets adventure',
    'pets claim': 'rpg pets claim',
    'pets fusion': 'rpg pets fusion',
    'pets list': 'rpg pets',
    'pets tournament': 'rpg pets tournament',
    'pickaxe': 'rpg pickaxe',
    'pickup': 'rpg pickup',
    'professions stats': 'rpg professions',
    'profile': 'rpg profile',
    'quest': 'rpg quest',
    'rd': 'rpg rd',
    'recipes': 'rpg recipes',
    'refine': 'rpg refine',
    'sell': 'rpg sell',
    'slots': 'rpg slots',
    'smr surf': 'rpg smr surf',
    'smr color tournament': 'rpg smr color tournament',
    'smr craft drink': 'rpg smr craft <drink>',
    'tractor': 'rpg tractor',
    'trade items': 'rpg trade',
    'trade list': 'rpg trade',
    'training': 'rpg training',
    'transmute': 'rpg transmute',
    'transcend': 'rpg transcend',
    'ultraining': 'rpg ultraining',
    'use': 'rpg use',
    'void areas': 'rpg void areas',
    'vote': 'rpg vote',
    'weekly': 'rpg weekly',
    'wheel': 'rpg wheel',
    'world status': 'rpg world',
    'xmas calendar': 'rpg xmas calendar',
    'xmas chimney': 'rpg xmas chimney',
    'xmas open': 'rpg xmas open',
}


# Auto flex headlines
FLEX_TITLES_ARTIFACTS: Final[tuple[str, ...]] = (
    'Hope this thing actually works',
    'The stuff you find in this game, eh?',
    'RARE SPECIMEN, DO NOT TOUCH',
    'Now this looks rather old',
    'How unique!',
    'Houston, we found something!',
    'Are you sure you acquired this legitimately?',
)

FLEX_TITLES_BREW_ELECTRONICAL: Final[tuple[str, ...]] = (
    'Now that\'s an expensive drink',
    'Champagne would be cheaper, you know',
    '"What did it cost?" - "Everything"',
    'Brewing at the robot graveyard',
    'Seriously, why would ANYONE brew that?',
)

FLEX_TITLES_CARD_DROP: Final[tuple[str, ...]] = (
    'Where are these even coming from',
    'Okay, so, what is this doing in... there',
    'IT\'S A CARD WOOH',
    'So, what do I do with this now?',
    'What do you mean, I need another 2 of those',
)

FLEX_TITLES_CARD_GOLDEN: Final[tuple[str, ...]] = (
    'GOLD! WE GOT GOLD!',
    'Normal cards are apparently not good enough',
    'It\'s poker cards. But fancy.',
    'Good luck getting all of those',
    'Why is nothing ever good enough for you?',
)

FLEX_TITLES_CARD_DROP_PARTNER: Final[tuple[str, ...]] = (
    'CALL THE POLICE',
    'Hello support, I\'d like to replace my partner',
    'This is what I get for loving you?',
    'Heartbreaking, really. Also, funny.',
    'Maybe it was an act of kindness? Just kidding.',
)

FLEX_TITLES_CARD_SLOTS: Final[tuple[str, ...]] = (
    'But... do you have a full set yet?',
    'You sure this card is legit?',
    'Almost there, only 7 billion cards to go',
    'Where do these cards even come from?',
    'Once you got them all, you can play solitaire',
)

FLEX_TITLES_WORK_EPICBERRY: Final[tuple[str, ...]] = (
    'Insalata epica',
    'Feel free to share',
    'Look who got greedy',
    'Stop stealing our food!',
)

FLEX_TITLES_WORK_HYPERLOG: Final[tuple[str, ...]] = (
    'TIMBER!',
    'Hyperino',
    'Justin?',
    'I swear this is how it happened',
    'Wooooh...d!',
    'Y dis never happen in A3',
    'Wood you log at this bad pun',
    'Log? Log!',
    'Logging 101',
)

FLEX_TITLES_WORK_ULTRALOG: Final[tuple[str, ...]] = (
    'It\'s not a dream!',
    'This sounds dangerous',
    'That\'s not how you use a chainsaw',
    'Deforesting in progress',
)

FLEX_TITLES_WORK_ULTIMATELOG: Final[tuple[str, ...]] = (
    'What do you even need that stuff for?',
    'Chainsaw master',
    'Can\'t even dismantle it, lol',
)

FLEX_TITLES_WORK_SUPERFISH: Final[tuple[str, ...]] = (
    'How much is the fish?',
    'Goodbye and thank you for the fish',
    'Nice fish, man',
    'Is fishing even allowed here?',
    'Better than an old boot, I guess',
)

FLEX_TITLES_WORK_WATERMELON: Final[tuple[str, ...]] = (
    'One in a melon',
    'Rare doesn\'t mean useful, lol',
    'Anyone know what to do with these?',
    'Fruit robbery',
    'Deliciously useless',
    'Meloncholia',
)

FLEX_TITLES_FORGE_COOKIE: Final[tuple[str, ...]] = (
    'Caution! Hot cookie!',
    'You sure you wanna eat that?',
    'What a weird recipe',
    'Next time just use an oven',
    'Someone say cookie?',
)

FLEX_TITLES_HAL_BOO: Final[tuple[str, ...]] = (
    'Stop scaring people, will ya?',
    'AAAAAAAAAAAAHHHHHHHHHHHH',
    'Boo or booh?',
    'A treat for the trick',
    'Hope they didn\'t get a heart attack',
    'Halloween hacking',
)

FLEX_TITLES_LB_A18: Final[tuple[str, ...]] = (
    'That\'s... not how you do it',
    'Spring cleaning?',
    'Not like this',
    'What exactly are you even doing',
    'Well that is... embarassing, lol',
)

FLEX_TITLES_LB_A18_PARTNER: Final[tuple[str, ...]] = (
    'How dare you!',
    'That\'s it, ima divorce',
    'Heart: Broken',
    'How did they even deserve this',
)

FLEX_TITLES_LB_OMEGA_MULTIPLE: Final[tuple[str, ...]] = (
    'Caution! T10 horse at work!',
    'Horse power',
    'One wasn\'t enough apparently',
    'Now that\'s just greedy',
    'How is this even fair?',
    'My precious',
)

FLEX_TITLES_LB_OMEGA_NOHARDMODE: Final[tuple[str, ...]] = (
    'Now this is how you find an OMEGA',
    'Finally some proper lootboxing',
    'Take note, sweat lords',
    'Who even needs harmode?',
    'Hardmode is for losers',
)

FLEX_TITLES_LB_OMEGA_PARTNER: Final[tuple[str, ...]] = (
    'Oops, wrong recipient, lol',
    'Mailman, you had one job',
    '"I am so happy for you, dear partner"',
    'WHAT ABOUT ME THO?',
    'Not jealous at all',
)

FLEX_TITLES_LB_GODLY: Final[tuple[str, ...]] = (
    'Oh hello, what a nice lootbox',
    'Some heavenly luck right here',
    'Oh hey, how did that happen?',
    'Did someone lose a box?',
    'Oooohh... I\'ll take that, thank you',
)

FLEX_TITLES_LB_GODLY_PARTNER: Final[tuple[str, ...]] = (
    'Best gift ever',
    '"Honey... I WANT IT BACK!"',
    '"MAILMAN... WE NEED TO TALK"',
    'True love',
    'Why does this never happen to ME?',
)

FLEX_TITLES_LB_VOID: Final[tuple[str, ...]] = (
    'Now this is just hacking',
    'No more luck for you this year',
    'Is this even legal?',
    'Oh hey, it\'s Gladstone Gander',
)

FLEX_TITLES_LB_VOID_PARTNER: Final[tuple[str, ...]] = (
    'I don\'t even know what to say',
    'Noone was ever supposed to see this line',
    'That\'s it, there\'s nothing else to achieve',
    'Bloody hell',
)

FLEX_TITLES_LB_ETERNAL: Final[tuple[str, ...]] = (
    'Wait, is this new?',
    'It\'s so.... blue!',
    'Sparkly sparkly',
    'But is it ACTUALLY eternal?',
    'Should I open it? Should I open it?',
)

FLEX_TITLES_LB_ETERNAL_PARTNER: Final[tuple[str, ...]] = (
    'Shut the front door and call me Sally',
    '... what?',
    'Maybe a divorce ain\'t the worst idea',
    'That\'s it, I\'m going polyamorous',
)

FLEX_TITLES_EDGY_ULTRA: Final[tuple[str, ...]] = (
    'What could an EDGY ever be worth?',
    'I didn\'t even know this was possible, lol',
    'It\'s an achievement, right?',
    'Feels like christmas',
    'How did that end up in there?',
)

FLEX_TITLES_OMEGA_ULTRA: Final[tuple[str, ...]] = (
    'This OMEGA is better than yours',
    'Pro unboxing',
    'Teach us',
    'Don\'t be jealous',
    'Why are my OMEGAs never like this?',
)

FLEX_TITLES_GODLY_VOID_TT: Final[tuple[str, ...]] = (
    'There\'s luck, and then there\'s THIS',
    'Jeez, now that is something',
    'Don\'t get jealous folks... or do',
    'This should be a bannable offense',
    'WE ARE ALL HAPPY FOR YOU AND NOT AT ALL JEALOUS',
)

FLEX_TITLES_PARTY_POPPER: Final[tuple[str, ...]] = (
    'Party hard!',
    'What is that doing in there?',
    'Pop up your life ',
    '"A handheld pyrotechnic device" [Wikipedia]',
    'If you use this thing in my house, you\'re in trouble',
)

FLEX_TITLES_PETS_CATCH_EPIC: Final[tuple[str, ...]] = (
    'EPIC pet incoming!',
    'What a nice kitty!',
    'Can I still pet it, tho?',
    'Great, and others can\'t even get one in fusions',
    'How many abandoned pets did this take?',
)

FLEX_TITLES_PETS_CATCH_TT: Final[tuple[str, ...]] = (
    'K9, is that you?',
    'This can happen, yes',
    'Lost companion',
    'Wonder how old it is...',
    'Always close your phone box door',
)

FLEX_TITLES_PETS_CLAIM_CAPSULE: Final[tuple[str, ...]] = (
    'That poor cat looks like it has been through a lot',
    'TIMEY WHIMEY CAT ALERT',
    'Please don\'t subject your cats to time travel',
    'Time and space and cat food',
)

FLEX_TITLES_PETS_CLAIM_OMEGA: Final[tuple[str, ...]] = (
    'Anything for the OMEGAs it seems',
    'This is against the Geneva Conventions',
    'Chance too high, lume pls fix',
    'SAVE THE SNOWMANS',
    'Bill Watterson might have inspired this flex',
)

FLEX_TITLES_PR_ASCENSION: Final[tuple[str, ...]] = (
    'Up up and away',
    'Goodbye peasants!',
    'We demand a giveaway!',
)

FLEX_TITLES_EPIC_BERRY: Final[tuple[str, ...]] = (
    'Time for some fruit salad!',
    'Are these fruits or vegetables?',
    'Margarita time!',
    'Horse! Time to celebrate!',
    'This might just be enough for a proper dessert',
    'Only about a quadrillion more until epicness 100',
)

FLEX_TITLES_EPIC_BERRY_PARTNER: Final[tuple[str, ...]] = (
    'Not even berries are safe anymore',
    'The berries is where the fun ends, I swear',
    'Hello 911, I want to report a robberry',
    'Hey, I needed those for the margarita!',
    'Reason for divorce: ',
)

FLEX_TITLES_EVENT_LB: Final[tuple[str, ...]] = (
    'They did what now?',
    'Unauthorized magic',
    'Mr Ollivander approves',
    'I guess that\'s one way of getting an OMEGA',
    'Hey, gimme back my wand!',
)

FLEX_TITLES_EVENT_ENCHANT: Final[tuple[str, ...]] = (
    'Twice the fun',
    'Can\'t even enchant properly, lol',
    'That\'s what happens when you use Ron\'s wand',
    'Well, at least it didn\'t explode',
)

FLEX_TITLES_EVENT_FARM: Final[tuple[str, ...]] = (
    'Totally believable level up story',
    'The what now?',
    'This sounds like a hacking excuse',
    'You call this farming?',
    'Where did you buy those seeds again?',
)

FLEX_TITLES_EVENT_HEAL: Final[tuple[str, ...]] = (
    'Very mysterious',
    'OH NO the poor guy',
    'So wait, this happened while HEALING?',
    'You sure that was a healing potion you drank there?',
    'Was that in Gotham by any chance?',
)

FLEX_TITLES_EVENT_TRAINING: Final[tuple[str, ...]] = (
    'Who even needs a plane',
    'Yes, that\'s how I go to school all the time',
    'Tinkerbell? Is it you?',
    'Where did those even come from?',
    'So we call this "training" now?',
)

FLEX_TITLES_EVENT_COINFLIP: Final[tuple[str, ...]] = (
    'Uh... how did that happen?',
    'Wait. Where\'s my coin?',
    'I didn\'t even know this could happen, lol',
    'Why is there a flex for this?',
    'MY COOOIIIINN NOOOOOOOOOOOOOOOOOOO',
)

FLEX_TITLES_TIME_TRAVEL_1: Final[tuple[str, ...]] = (
    'First time\'s always special',
    'Off to a great start!',
    'It\'s just a leap of faith',
    'First year student!',
    'First of many',
)

FLEX_TITLES_TIME_TRAVEL_3: Final[tuple[str, ...]] = (
    'Three? Three!',
    'Third year student!',
    'Hardmode time, baby',
    'Dungeon 13, coming for you!',
    'Thrice the fun',
)

FLEX_TITLES_TIME_TRAVEL_5: Final[tuple[str, ...]] = (
    'Five year student!',
    'Hardmode all the things!',
    'Five is the... eh... something number?',
    'Still playing, eh?',
    'The Famous Five',
)

FLEX_TITLES_TIME_TRAVEL_10: Final[tuple[str, ...]] = (
    'Ten year stud... uh, wait, no',
    'I hope you\'re not colorblind',
    'Hope you don\'t plan on hardmoding in A15',
    'Out of school',
    'Next stop: 25!',
)

FLEX_TITLES_TIME_TRAVEL_25: Final[tuple[str, ...]] = (
    'Endgame achieved',
    'The sky\'s the limit!',
    'No more mere time travels. We\'re jumping now, boyz.',
    'GG EZ',
    'Twenty bloody five',
    'Someone tried D15 without a bot once. They\'re still at it.',
)

FLEX_TITLES_TIME_TRAVEL_50: Final[tuple[str, ...]] = (
    '50 TTs and all I got was this lousy background',
    'Still at it! (for some reason)',
    'Loving dragon scales, I swear!',
    'How do you do, fellow kids',
    'Age is just a number',
)

FLEX_TITLES_TIME_TRAVEL_100_PLUS: Final[tuple[str, ...]] = (
    'Hello, I would like my life back',
    'Next up: World domination',
    'Why am I still playing this',
    'BOW BEFORE ME PEASANTS',
    'Probably dizzy from all the time travelling',
    'The all important question is... why?',
)

FLEX_TITLES_TIME_TRAVEL_1000000: Final[tuple[str, ...]] = (
    'A poem for a legend',
)

FLEX_TITLES_XMAS_CHIMNEY: Final[tuple[str, ...]] = (
    'Now this is embarassing',
    'Can we get a live stream?',
    'Hope noone is making a fire',
    'Enjoy your break',
    'Imagine how many hunts you could do in that time',
    'We are not laughing, I swear',
)

FLEX_TITLES_XMAS_ETERNAL: Final[tuple[str, ...]] = (
    'The gift that keeps on giving',
    'This is some dubious magic stuff',
    'I tried opening it once... twice... thrice... aaah',
    'I don\'t understand this type of present',
    'Did they deserved this? But of course.',
    'Wdym I need to wait 24h after opening it? What the hell',
)

FLEX_TITLES_XMAS_GODLY: Final[tuple[str, ...]] = (
    'Oh thank you Santa!',
    'Ho ho ho',
    'You sure you deserve this?',
    'Someone must have dropped this',
    'Look at that shiny paper',
    'WHAT IS IT? WHAT IS IT?',
)

FLEX_TITLES_XMAS_SNOWBALL: Final[tuple[str, ...]] = (
    'Yellow snow? Uh, yeah, you can keep that',
    'Look, it\'s glowing!',
    'But can you upgrade it to a MEGA snowball?',
    'Hope it doesn\'t melt',
)

FLEX_TITLES_XMAS_VOID: Final[tuple[str, ...]] = (
    'Probably bribed Rudolf',
    'Santa is real!',
    'Clearly Santa\'s favourite',
    'And they get this after eating all the cookies?',
    'I think that one was meant for me',
)


# Auto flex thumbnails
FLEX_THUMBNAILS_ARTIFACTS: Final[tuple[str, ...]] = (
    'https://media.tenor.com/zIdCNhI7PrsAAAAC/thats-incredible-national-geographic.gif',
    'https://media.tenor.com/ggwFe8AmPl8AAAAC/scraping-ancient-china-from-above.gif',
    'https://media.tenor.com/LPwQVB6FAf8AAAAC/indiana-jones-hmm.gif',
    'https://media.tenor.com/AfdYK7WD3a0AAAAC/angelina-jolie-wink.gif',
    'https://media.tenor.com/XntK6PCl5hsAAAAd/this-is-how-we-bingham-treasure-hunt.gif',
    'https://media.tenor.com/rAwf52N-KAgAAAAC/secrets-of-castle-mcduck-ducktales.gif',
    'https://media.tenor.com/UKDMIuJCXIYAAAAC/i-found-something-the-investigator.gif',
    'https://media.tenor.com/wVOgdD9hHrEAAAAC/anime-treasure.gif',
)

FLEX_THUMBNAILS_ARTIFACTS_BUNNY_MASK: Final[tuple[str, ...]] = (
    'https://media1.tenor.com/m/1zya5psiGUQAAAAd/he-is-risen-praise-him.gif',
    'https://media1.tenor.com/m/62qzG52IPegAAAAC/bunny-floss-dancing.gif',
    'https://media1.tenor.com/m/itoD_tHWovAAAAAC/easter-happyeaster.gif',
    'https://media1.tenor.com/m/RCSTVkvYo04AAAAd/happy-easter-my-little-bunnies-aunt-susan.gif',
    'https://media1.tenor.com/m/eYZDjHIOdKsAAAAd/happy-easter-easter.gif',
)

FLEX_THUMBNAILS_ARTIFACTS_CLAUS_BELT: Final[tuple[str, ...]] = (
    'https://media.tenor.com/Gz-aSR82810AAAAd/theodoros.gif',
    'https://media.tenor.com/N_vsbVvbeH4AAAAC/santa-claus-fat.gif',
    'https://media.tenor.com/biHQOhu31rAAAAAC/santa-belly.gif',
    'https://media.tenor.com/EBWqm5qIocgAAAAd/santa-dancing.gif',
    'https://media.tenor.com/rpnFMRgGHsgAAAAi/vodafone-vodafone-xmas.gif',
)

FLEX_THUMBNAILS_ARTIFACTS_COWBOY_BOOTS: Final[tuple[str, ...]] = (
    'https://media1.tenor.com/m/fJV5-t-jC6EAAAAd/new-boot.gif',
    'https://media1.tenor.com/m/NmB6i7DZFHUAAAAC/querida-piso21.gif',
    'https://media1.tenor.com/m/lBEJu36EtYsAAAAd/cowboy-boots-western-boots.gif',
    'https://media1.tenor.com/m/aADNFJFpOzcAAAAC/boots-shoes.gif',
    'https://media1.tenor.com/m/S83c-j-wvpoAAAAC/cowboy-boots-cowboy.gif',
)

FLEX_THUMBNAILS_ARTIFACTS_SHINY_PICKAXE: Final[tuple[str, ...]] = (
    'https://c.tenor.com/Isec7K5eGFMAAAAd/tenor.gif',
    'https://c.tenor.com/byo3PamG1PUAAAAC/tenor.gif',
    'https://c.tenor.com/NUMy8NdzwBsAAAAC/tenor.gif',
    'https://c.tenor.com/qBxnw59KgQcAAAAd/tenor.gif',
)

FLEX_THUMBNAILS_BREW_ELECTRONICAL: Final[tuple[str, ...]] = (
    'https://media.tenor.com/wlpMSYaDoYkAAAAd/tea-time-heure-du-th%C3%A9.gif',
    'https://media.tenor.com/YBIZSm5Hl8YAAAAi/cat-drink.gif',
    'https://media.tenor.com/AQlLOEyD-xoAAAAd/swag-potion.gif',
    'https://media.tenor.com/n5ikt7jBRh0AAAAM/green-smoothie-messy-dog-slurp.gif',
    'https://media.tenor.com/dSjPLLjh5FYAAAAC/i-love-expensive-things-luxury.gif',
)

FLEX_THUMBNAILS_CARD_DROP: Final[tuple[str, ...]] = (
    'https://media.tenor.com/3-YewQ7i6HYAAAAC/wow-surprised-face.gif',
    'https://media.tenor.com/vVGDwU5vHWYAAAAd/wow-gif.gif',
    'https://media.tenor.com/O45wQ8fW9qsAAAAC/if-you-cheat-you-will-win-qotd.gif',
    'https://media.tenor.com/nZDQaGBpSpIAAAAC/cast-them-out-hiram-epps.gif',
    'https://media.tenor.com/wZIJPJMG6cQAAAAC/star-citizen-aurora-get-this-man-a-ban.gif',
)

FLEX_THUMBNAILS_CARD_GOLDEN: Final[tuple[str, ...]] = (
    'https://media1.tenor.com/m/eoXNSS9OlVIAAAAd/crypto-gemology-salt-bae.gif',
    'https://media1.tenor.com/m/38IipBkBL6sAAAAC/fff-gold.gif',
    'https://media1.tenor.com/m/nFrhSMnzrU4AAAAC/rougo-ni-sonaete-isekai-de8manmai-no-kinka-o-tamemasu-cute.gif',
    'https://media1.tenor.com/m/Ft_i04ZwRuEAAAAd/monkey-give-gold.gif',
    'https://media1.tenor.com/m/MH08oeqr_P8AAAAC/ohm-money.gif',
)

FLEX_THUMBNAILS_CARD_DROP_PARTNER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/jfcWpXpbTCwAAAAC/kto-kounotori.gif',
    'https://media.tenor.com/HtYPa_A9lWkAAAAC/sahovet-aura-fortnite-take-the-l-aura-fortnite.gif',
    'https://media.tenor.com/Cu00dHuwNw4AAAAC/loser-losers.gif',
    'https://media.tenor.com/d_wXE6yg8gMAAAAd/laser-cat.gif',
    'https://media.tenor.com/a4qDuOMfC4IAAAAC/its-mine-lotr.gif',
)

FLEX_THUMBNAILS_CARD_SLOTS: Final[tuple[str, ...]] = (
    'https://media.tenor.com/S593fyjCciAAAAAi/monkey-chimp.gif',
    'https://media.tenor.com/NZB5RaiKFcAAAAAC/poker-face-poker.gif',
    'https://media.tenor.com/RL1cXtVWQ74AAAAC/brandy-and-mr-whiskers-wanna-play-cards.gif',
    'https://media.tenor.com/d6OIKbtU88sAAAAC/maverick-cards.gif',
    'https://media.tenor.com/8OUzmyLh2JsAAAAd/game-catch.gif',
)

FLEX_THUMBNAILS_WORK_EPICBERRY: Final[tuple[str, ...]] = (
    'https://media.tenor.com/kNbvRBLOpe0AAAAC/blueberry-berry.gif',
    'https://media.tenor.com/wjAK63POzTMAAAAd/monkey-monkey-eating.gif',
    'https://media.tenor.com/oxTE2Jll0R4AAAAd/strawberries-cute-baby.gif',
    'https://media.tenor.com/XzNFyKEujQgAAAAd/cute-cats-cute.gif',
    'https://media.tenor.com/mNpLTVfVxMkAAAAC/betty-bunny-betty.gif',
)

FLEX_THUMBNAILS_WORK_HYPERLOG: Final[tuple[str, ...]] = (
    'https://c.tenor.com/p8NKGRDxNvMAAAAC/rut-daniels-timber.gif',
    'https://media.tenor.com/CeKTpmgR3ZkAAAAC/yell-timber.gif',
    'https://media.tenor.com/Csef0r09V3oAAAAC/timber-timbera.gif',
    'https://media.tenor.com/OxX-5DEP9OwAAAAC/love-nature.gif',
    'https://media.tenor.com/r5CYGkSFnT0AAAAC/hyperino-scooter.gif',
    'https://media.giphy.com/media/3o6Zt7Nu7NikdIvjaw/giphy.gif',
    'https://media.giphy.com/media/VNdgEiEcRalhe/giphy.gif',
    'https://media.giphy.com/media/eRJGUjgF4DbCU/giphy.gif',
    'https://media.tenor.com/4kc5AXWNVvQAAAAC/barney-rubble-chopping-wood.gif',
    'https://media.giphy.com/media/sA6GWybXhdTfXcQpg5/giphy.gif',
    'https://media.giphy.com/media/SXkwx68Y4x6MlswX4Y/giphy.gif',
    'https://media.giphy.com/media/88np7RwIbvA76/giphy.gif',
    'https://media.giphy.com/media/YWxV34fttb0ljpRcoY/giphy.gif',
    'https://media.tenor.com/GwTLRYxCEX4AAAAC/raising-my-axe-gawain.gif',
)

FLEX_THUMBNAILS_WORK_ULTIMATELOG: Final[tuple[str, ...]] = (
    'https://media.giphy.com/media/SGV9O1fuh2nf5T8FNW/giphy-downsized-large.gif',
    'https://media.tenor.com/vfraS_QhPcEAAAAd/captain-america-pecs.gif',
    'https://media.tenor.com/Gd9zrsML1tYAAAAC/im-building-construction.gif',
)

FLEX_THUMBNAILS_WORK_ULTRALOG: Final[tuple[str, ...]] = (
    'https://c.tenor.com/4ReodhBihBQAAAAC/ruthe-biber.gif',
    'https://media.giphy.com/media/0eVM7GVxTDDKxn7OyX/giphy.gif',
    'https://media.tenor.com/B984YMYS43IAAAAC/chainsaw-wood-cutting.gif',
    'https://media.tenor.com/oSSU2r9NWrMAAAAC/freddie-chainsaw.gif',
)

FLEX_THUMBNAILS_WORK_SUPERFISH: Final[tuple[str, ...]] = (
    'https://media.tenor.com/B6dwDGql374AAAAC/mcdonald-chris-mcdonald.gif',
    'https://media.tenor.com/4fGHA-FQ-N8AAAAC/fiska-fisk.gif',
    'https://media.tenor.com/25FSuyo3WWQAAAAi/%E6%80%9D%E8%80%83%E5%96%B5%E7%94%9F-peach-cat-and-goma.gif',
    'https://media.tenor.com/nW_vYquFoGwAAAAC/fish-love.gif',
    'https://media.tenor.com/HLYz9zk-fGQAAAAC/rumia-fish-gif.gif',
)

FLEX_THUMBNAILS_WORK_WATERMELON: Final[tuple[str, ...]] = (
    'https://media.tenor.com/mAxfGDKXrZUAAAAC/bunnies-cute.gif',
    'https://media.tenor.com/1qy7WBALXg8AAAAC/water.gif',
    'https://media.tenor.com/o3oQXq9guVAAAAAd/maya-dog.gif',
    'https://media.tenor.com/3laUQPe252YAAAAC/rabbit-watermelon.gif',
    'https://media.tenor.com/uS6xykUe7NcAAAAC/pinch-%D5%B1%D5%B4%D5%A5%D6%80%D5%B8%D6%82%D5%AF.gif',
)

FLEX_THUMBNAILS_FORGE_COOKIE: Final[tuple[str, ...]] = (
    'https://media.tenor.com/YP5Xv8Sa45IAAAAC/cookie-monster-awkward.gif',
    'https://media.giphy.com/media/Y09s2Frxp7wpBGXTyt/giphy.gif',
    'https://media.giphy.com/media/bAlYQOugzX9sY/giphy.gif',
)

FLEX_THUMBNAILS_HAL_BOO: Final[tuple[str, ...]] = (
    'https://media.tenor.com/M6MkMfBBDjcAAAAC/afraid-scared.gif',
    'https://media.tenor.com/LzqPLLcuAqsAAAAC/peachcat-boo.gif',
    'https://media.tenor.com/xdP3iAkkZ6cAAAAC/ghost-spooky.gif',
    'https://media.tenor.com/xdP3iAkkZ6cAAAAC/ghost-spooky.gif',
    'https://media.tenor.com/SM5IBkvYeX0AAAAC/halloween-creepy-pumpkin.gif',
    'https://media.tenor.com/A6zk0D9xNVcAAAAC/boo-ghosts.gif',
    'https://media.giphy.com/media/12RfP2odT4hEOI/giphy.gif',
    'https://media.giphy.com/media/3o7TKqnN349PBUtGFO/giphy.gif',
)

FLEX_THUMBNAILS_LB_A18: Final[tuple[str, ...]] = (
    'https://media.tenor.com/-h9txtxh3osAAAAC/vorikx-box.gif',
    'https://media.tenor.com/hq6Fi0viNQQAAAAC/sassy.gif',
    'https://media.tenor.com/roi7tc89FQwAAAAi/peach-cat-you-bad-bad.gif',
    'https://media.tenor.com/XQLVLptLIBEAAAAd/maes-b-lost-in-a-field.gif',
    'https://media.tenor.com/VcywkrgsobEAAAAC/thats-horrible-thats-terrible.gif',
)

FLEX_THUMBNAILS_LB_A18_PARTNER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/P285-2vH5FYAAAAi/alone-lonely.gif',
    'https://media.tenor.com/yjlnfb4WoIAAAAAd/heart-broke.gif',
    'https://media.tenor.com/8_cSc3omGmoAAAAd/theres-a-sharp-pain-right-here-pointing-to-chest.gif',
    'https://media.tenor.com/XXv6c1i9G9gAAAAC/new-girl-heartbreak.gif',
)

FLEX_THUMBNAILS_LB_OMEGA_MULTIPLE: Final[tuple[str, ...]] = (
    'https://media.tenor.com/gHygBs_JkKwAAAAi/moving-boxes.gif',
    'https://media.tenor.com/h5-edZgGfu0AAAAC/boxes-move-in-day.gif',
    'https://media.tenor.com/uoCDp8f_ZicAAAAC/horse-hahaha.gif',
    'https://media.tenor.com/DYxjt7HJ4LQAAAAC/i-need-a-horse-thor.gif',
)

FLEX_THUMBNAILS_LB_OMEGA_NOHARDMODE: Final[tuple[str, ...]] = (
    'https://media.tenor.com/JQIXRoPBLqYAAAAC/impressive-20th-century.gif',
    'https://media.giphy.com/media/9VrBXYVGAX0bAEzSAT/giphy.gif',
)

FLEX_THUMBNAILS_LB_OMEGA_PARTNER: Final[tuple[str, ...]] = (
    'https://c.tenor.com/l0wNXZN58S8AAAAC/delivery-kick.gif',
    'https://media.giphy.com/media/AdExwGjrXYjH7yjuIc/giphy.gif',
    'https://media.tenor.com/OhwPShbFvjcAAAAC/package-ups.gif',
    'https://media.tenor.com/_lu2Jz1q1s0AAAAC/sunday-delivery.gif',
)

FLEX_THUMBNAILS_LB_GODLY: Final[tuple[str, ...]] = (
    'https://c.tenor.com/zBe7Ew1lzPYAAAAi/tkthao219-bubududu.gif',
    'https://media.tenor.com/f8-9UL5OveIAAAAi/box-cute.gif',
    'https://media.tenor.com/ZDW2vrkgYB4AAAAC/whats-inside-ricky-berwick.gif',
    'https://media.tenor.com/kI9zfph0YdIAAAAC/andre-leon-talley-present.gif',
    'https://media.tenor.com/tuOmcb4nNG0AAAAd/nice-package-austin-evans.gif',
)

FLEX_THUMBNAILS_LB_GODLY_PARTNER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/NvP2dNkQWtEAAAAC/i-got-us-a-box-anthony-mennella.gif',
    'https://media.giphy.com/media/mDIQaHAhD33wlOz0DR/giphy.gif',
    'https://media.tenor.com/ClAp685q6pEAAAAC/drop-off-dropping-off-a-package.gif',
)

FLEX_THUMBNAILS_LB_VOID: Final[tuple[str, ...]] = (
    'https://media.giphy.com/media/JkpHPyZowX6sfFvKp6/giphy.gif',
)

FLEX_THUMBNAILS_LB_VOID_PARTNER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/kumodwVv1bcAAAAC/patrick-the-maniacs-in-mail-box.gif',
    'https://media.giphy.com/media/atfHlwAhizfxdtdw60/giphy.gif',
)

FLEX_THUMBNAILS_LB_ETERNAL: Final[tuple[str, ...]] = (
    'https://media1.tenor.com/m/WF9ahkVEZZUAAAAC/eevee-eevee-wow.gif',
    'https://media1.tenor.com/m/B0CyGcl_eIEAAAAC/shiny-moana.gif',
    'https://media1.tenor.com/m/CZUsUDsW07cAAAAC/firefly-thinking.gif',
    'https://media1.tenor.com/m/ETzkr7t7pfwAAAAC/tally-craven-motherland-fort-salem.gif',
    'https://media1.tenor.com/m/WAmX-u888l0AAAAd/lets-open-it-up-unlock.gif',
)

FLEX_THUMBNAILS_LB_ETERNAL_PARTNER: Final[tuple[str, ...]] = (
    'https://media1.tenor.com/m/zblEiac5pUkAAAAd/hugh-jackman-shocked.gif',
    'https://media1.tenor.com/m/Mkbsp1hUhMMAAAAC/shocked-surprised.gif',
)

FLEX_THUMBNAILS_EDGY_ULTRA: Final[tuple[str, ...]] = (
    'https://c.tenor.com/clnoM8TeSxcAAAAC/wait-what-unbelievable.gif',
    'https://media.giphy.com/media/GjbR6R2XeWKS0yfQaZ/giphy.gif',
)

FLEX_THUMBNAILS_OMEGA_ULTRA: Final[tuple[str, ...]] = (
    'https://media.tenor.com/Dmr7SzwDii0AAAAC/andy-office.gif',
    'https://media.tenor.com/kJNvpynpU3sAAAAi/boxy-kitten-peek-a-boo.gif',
    'https://media.giphy.com/media/Q9Clm1DwDR0WWF7Qr4/giphy.gif',
    'https://media.giphy.com/media/xUOxf8sb4pizGFkBJm/giphy.gif',
    'https://media.giphy.com/media/5Y2bU7FqLOuzK/giphy.gif',
    'https://media.giphy.com/media/M9CoztwchmOdSRGH2m/giphy.gif',
    'https://media.giphy.com/media/3KXd872FGuIO0u0e7h/giphy.gif',
    'https://media.tenor.com/TukiL_LftA0AAAAC/loz-botw.gif',
)

FLEX_THUMBNAILS_GODLY_VOID_TT: Final[tuple[str, ...]] = (
    'https://c.tenor.com/-BVQhBulOmAAAAAC/bruce-almighty-morgan-freeman.gif',
    'https://media.giphy.com/media/jltuIcAMViLHYaz9bN/giphy.gif',
)

FLEX_THUMBNAILS_PARTY_POPPER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/daIqywAK47AAAAAd/marialina-amigos-improvaveis.gif',
    'https://media.tenor.com/6f3xkQD8TtIAAAAd/party-poppers-nicole-brown.gif',
    'https://media.tenor.com/UyEOw10aB9UAAAAC/party-confetti.gif',
    'https://media.tenor.com/6rCdZsiBT8oAAAAC/glee-jane-lynch.gif',
    'https://media.tenor.com/4eSQIwrsGXIAAAAd/celebrate-awesome.gif',
    'https://media.tenor.com/dZHod7wU9pIAAAAC/zomerkampzwijndrecht-zomerkamp.gif',
)

FLEX_THUMBNAILS_PETS_CATCH_EPIC: Final[tuple[str, ...]] = (
    'https://media.tenor.com/WnprYvrvNp8AAAAC/cat-kitty.gif',
    'https://media.giphy.com/media/xUOxf8izqVvHEBhRO8/giphy-downsized-large.gif',
    'https://media.giphy.com/media/QQPpBZs31y2fijvNzo/giphy.gif',
    'https://media.giphy.com/media/7dwrVhuNR1rPi/giphy.gif',
)

FLEX_THUMBNAILS_PETS_CATCH_TT: Final[tuple[str, ...]] = (
    'https://media.tenor.com/7LMaSfhq9TIAAAAC/flying-omw.gif',
    'https://media.giphy.com/media/3qsCqrKYjq5DkANgBE/giphy.gif',
    'https://media.giphy.com/media/5E7vDOIamcWlzg97TG/giphy.gif',
    'https://media.giphy.com/media/U7JM6ChJMrFnXfFHvE/giphy.gif',
)

FLEX_THUMBNAILS_PETS_CLAIM_CAPSULE: Final[tuple[str, ...]] = (
    'https://c.tenor.com/4CHnbg_zVEoAAAAC/tenor.gif',
    'https://c.tenor.com/zbDHXQ60jMIAAAAC/tenor.gif',
    'https://c.tenor.com/CcOypZMhDS8AAAAC/tenor.gif',
    'https://c.tenor.com/IOQxHefEGmoAAAAC/tenor.gif',
    'https://c.tenor.com/lhww8cZ_nEQAAAAC/tenor.gif',
)

FLEX_THUMBNAILS_PETS_CLAIM_OMEGA: Final[tuple[str, ...]] = (
    'https://media.tenor.com/sQVkHE1_BgcAAAAC/ahh-scared.gif',
    'https://media.tenor.com/eFNKOmp6hSsAAAAC/olaf-disney.gif',
    'https://media.tenor.com/gZcSvrfQPXgAAAAC/snowman-melting.gif',
    'https://media.tenor.com/l5BcI5CzQV0AAAAC/elmo-fire-elmo-snowman.gif',
    'https://media.tenor.com/nzD-S3_ZC-8AAAAd/snowgolem-minecraft.gif',
)

FLEX_THUMBNAILS_PR_ASCENSION: Final[tuple[str, ...]] = (
    'https://media.tenor.com/wfma4CqwxCwAAAAC/railgun-misaka-mikoto.gif',
    'https://media.tenor.com/NF5dnWvoaN8AAAAC/glameow-purugly.gif',
    'https://media.tenor.com/EoCQm0KsqP8AAAAC/pokemon-anime.gif',
)

FLEX_THUMBNAILS_EPIC_BERRY: Final[tuple[str, ...]] = (
    'https://media.tenor.com/yuSXdXW7tgsAAAAC/strawberry-juice.gif',
    'https://media.tenor.com/oxTE2Jll0R4AAAAd/strawberries-cute-baby.gif',
    'https://media.tenor.com/wjAK63POzTMAAAAd/monkey-monkey-eating.gif',
    'https://media.tenor.com/CkRsEfWoUx4AAAAC/mmm-good-creepy.gif',
    'https://media.tenor.com/sc7R5jLoYioAAAAd/cat-cats.gif',
    'https://media.tenor.com/dtDUL6UpUg4AAAAd/yummy-strawberry.gif',
)

FLEX_THUMBNAILS_EPIC_BERRY_PARTNER: Final[tuple[str, ...]] = (
    'https://media.tenor.com/jUAC58SFqzsAAAAC/bunny-steal.gif',
    'https://media.tenor.com/g3VXd3gcG9wAAAAC/it-crowd-richard-ayoade.gif',
    'https://media.tenor.com/_6FGp_11YQIAAAAd/worst-marriage-ever-family-feud-canada.gif',
    'https://media.tenor.com/kbfjUFqT1psAAAAd/unromantic-bad-wedding.gif',
    'https://media.tenor.com/sPe_qdC2idcAAAAC/modern-family-modern-family-joe.gif',
    'https://media.tenor.com/0Jeb1C_TaBcAAAAd/now-thats-stealing-redd-foxx.gif',
)

FLEX_THUMBNAILS_EVENT_LB: Final[tuple[str, ...]] = (
    'https://media.tenor.com/wn2_Qq6flogAAAAC/magical-magic.gif',
    'https://media.giphy.com/media/mz1kJeDVueKC4/giphy.gif',
    'https://media.giphy.com/media/MePp78CYbOaYh3iNBZ/giphy-downsized-large.gif',
    'https://media.giphy.com/media/LR5UmQvLDDRqp9BI9x/giphy.gif',
)

FLEX_THUMBNAILS_EVENT_ENCHANT: Final[tuple[str, ...]] = (
    'https://c.tenor.com/gAuPzxRCVw8AAAAC/link-dancing.gif',
    'https://media.giphy.com/media/ef4gyEAxktrF3cWO5g/giphy.gif',
    'https://media.tenor.com/oTpEgUkQjngAAAAC/vibing-dancing.gif',
    'https://media.tenor.com/9-b0gUv-HokAAAAC/enchanted-sword-enchanted-iron-sword.gif',
    'https://media.tenor.com/Z3mgGQaNQt4AAAAC/legendofzelda-navi.gif',
)

FLEX_THUMBNAILS_EVENT_FARM: Final[tuple[str, ...]] = (
    'https://media.tenor.com/z1ru-IqnJFoAAAAC/earthquake-four-arms.gif',
    'https://media.giphy.com/media/apvx5lPCPsjN6/giphy.gif',
    'https://media.giphy.com/media/h4Z6RfuQycdiM/giphy.gif',
    'https://media.giphy.com/media/2SZeeNMm456NO/giphy.gif',
)

FLEX_THUMBNAILS_EVENT_HEAL: Final[tuple[str, ...]] = (
    'https://media.tenor.com/lh60y7i9SeQAAAAC/peachmad-peachandgoma.gif',
    'https://media.tenor.com/gaHlo3VAWrwAAAAd/invisible-friends-crime-scene.gif',
    'https://media.tenor.com/gs7Wpi7iJBQAAAAC/tmm-the-mystery-man.gif',
    'https://media.tenor.com/yST82xLuBOQAAAAd/standing-still-jake-lyon.gif',
)

FLEX_THUMBNAILS_EVENT_TRAINING: Final[tuple[str, ...]] = (
    'https://media.tenor.com/YAaId6OVgFUAAAAC/baby-up.gif',
    'https://media.giphy.com/media/B5BP3OYgVN5ss/giphy.gif',
    'https://media.giphy.com/media/yXBqba0Zx8S4/giphy.gif',
    'https://media.tenor.com/C_YenjB3niUAAAAC/tinkerbell-happy.gif',
)

FLEX_THUMBNAILS_EVENT_COINFLIP: Final[tuple[str, ...]] = (
    'https://media.tenor.com/Adg8-XpUrEIAAAAd/john-travolta-confused.gif',
    'https://media.giphy.com/media/JQG2I0rQejbRQiDMQZ/giphy.gif',
    'https://media.tenor.com/8yBy9hKYpBkAAAAC/where-is-it-melody-pedras.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_1: Final[tuple[str, ...]] = (
    'https://media.tenor.com/7n7-MMKE8HUAAAAC/im-a-time-traveler-time-traveler.gif',
    'https://media.tenor.com/EYMfaM_5e7wAAAAC/hulk-endgame.gif',
    'https://media.tenor.com/VVKQ2r1T5n0AAAAd/its-time-travel-sam-hart.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_3: Final[tuple[str, ...]] = (
    'https://media.tenor.com/XATWkMEOrZIAAAAC/doctor-dance-doctor-who-dances.gif',
    'https://media.tenor.com/XO52a0Voe2AAAAAC/fantastic-doctor-who.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_5: Final[tuple[str, ...]] = (
    'https://media.tenor.com/GctGuDyWlOMAAAAC/back-to-the-future-back-to-the-past.gif',
    'https://media.tenor.com/xXXrBidPuPEAAAAC/back-to-the-future-doc-brown.gif',
    'https://media.tenor.com/SD-TxYTh3scAAAAd/precisely-on-schedule-right-on-schedule.gif',
    'https://media.tenor.com/K84SJ6-ycMUAAAAC/msmbttf-bttf.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_10: Final[tuple[str, ...]] = (
    'https://media.tenor.com/pDdh_ISRzZIAAAAC/doctor-who-dr-who.gif',
    'https://media.tenor.com/ZIUSH-XNatEAAAAC/doctorwho-tardis.gif',
    'https://media.tenor.com/R1nsCixefawAAAAC/tardis-doctor-who.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_25: Final[tuple[str, ...]] = (
    'https://media.tenor.com/mh75FCw3VpoAAAAC/avengers-end-game-black-widow.gif',
    'https://media.tenor.com/FK0u5g5qQUcAAAAd/dr-strange-doctor-strange.gif',
    'https://media.tenor.com/o3S8K00A2CQAAAAC/the-end-game-welcome-to-the-end-game.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_50: Final[tuple[str, ...]] = (
    'https://media.tenor.com/n-vLx1Q_QBQAAAAC/fn2187.gif',
    'https://media.tenor.com/P3iWMO_GKksAAAAC/abstract-art.gif',
    'https://media.tenor.com/U5DTTODnuTcAAAAC/trippy-tripping.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS: Final[tuple[str, ...]] = (
    'https://media.tenor.com/J82kuX8dFysAAAAC/blue-spiral.gif',
    'https://media.tenor.com/_Ep8uvjeSHQAAAAC/moon-digibyte.gif',
    'https://media.giphy.com/media/xT39CTrFW4nHLdBPpu/giphy-downsized-large.gif',
    'https://media.tenor.com/gbe6XR5AEzIAAAAC/optical-illusion-spiral.gif',
    'https://media.tenor.com/y8rZhxGifNEAAAAC/blue-spiral.gif',
    'https://media.tenor.com/vUVXRKFtKQEAAAAC/blue-spiral.gif',
    'https://media.tenor.com/Uy3avUOOI_sAAAAd/blue-spiral.gif',
    'https://media.tenor.com/twi6r7OVu6MAAAAd/blue-spiral.gif',
    'https://media.tenor.com/VrcRpp5urSoAAAAC/time-clock.gif',
    'https://media.tenor.com/7JwnIw76nRwAAAAC/time-clock.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_1000000: Final[tuple[str, ...]] = (
    'https://c.tenor.com/Z3mgGQaNQt4AAAAC/tenor.gif',
)

FLEX_THUMBNAILS_TIME_TRAVEL_300: Final[tuple[str, ...]] = (
    'https://media.tenor.com/HNU157CkzH4AAAAd/sparta.gif',
    'https://media.tenor.com/Sexf_CWjVfgAAAAd/300-leonidas.gif',
    'https://media.tenor.com/PhTFN_KwbIQAAAAC/this-is-sparta-sparta.gif',
)

FLEX_THUMBNAILS_XMAS_CHIMNEY: Final[tuple[str, ...]] = (
    'https://media.tenor.com/RNBD-BUVb3cAAAAi/chimney-santa.gif',
    'https://media.tenor.com/scEtOL9oeMoAAAAi/sumikko-gurashi-chimney-santa.gif',
    'https://media.tenor.com/7Hh1I-SmB3cAAAAi/playmobil-christmas.gif',
    'https://media.tenor.com/54bt7hOcqdsAAAAi/christmas-red.gif',
    'https://media.tenor.com/MCn_GMSSqAsAAAAd/lol-laughing-hysterically.gif',
    'https://media.tenor.com/lr8W5AadieAAAAAd/smile-laughing.gif',
    'https://media.tenor.com/REqgDts8CVgAAAAC/futurenostlgia-laughing.gif',
    'https://media.tenor.com/Lot4htkwha8AAAAd/adventures-of-oliver-twist-stuck.gif',
)

FLEX_THUMBNAILS_XMAS_ETERNAL: Final[tuple[str, ...]] = (
    'https://media.tenor.com/_JV_Y_9X3fAAAAAi/petsure-cat.gif',
    'https://media.tenor.com/ika5BN6eB_UAAAAi/spinning-gif-spinning.gif',
    'https://media.tenor.com/3ViKggOJ8PAAAAAC/spongebob-empty-box.gif',
    'https://media.tenor.com/MUD10DgrG9cAAAAd/monero-xmr.gif',
    'https://media.tenor.com/KQztQwZSDU4AAAAi/whats-in-the-box-surprise.gif',
    'https://media.tenor.com/fXHJquBk8VAAAAAd/cat-box.gif',
)

FLEX_THUMBNAILS_XMAS_GODLY: Final[tuple[str, ...]] = (
    'https://media.tenor.com/t7aI5VVWTvwAAAAC/gift-christmas-gift.gif',
    'https://media.tenor.com/7tB2s3YAN1wAAAAC/santa-christmas-gifts.gif',
    'https://media.tenor.com/g1xITZea4jQAAAAC/christmas-lights-merry-christmas.gif',
    'https://media.tenor.com/uClPOG9_S2EAAAAM/simpatico-christmas.gif',
    'https://media.tenor.com/MhVmARXUBG4AAAAC/nice-happy.gif',
    'https://media.tenor.com/KQSI-mZGUOUAAAAC/presents-gift-box.gif',
    'https://media.giphy.com/media/SVYnISz8VwSFTsOX9k/giphy.gif',
    'https://media.giphy.com/media/kKo2x2QSWMNfW/giphy.gif',
    'https://media.giphy.com/media/ofxTCKA5z8UiDYIStD/giphy.gif',
    'https://media.tenor.com/paesy669JUIAAAAC/gift-present.gif',
    'https://media.tenor.com/OLG-TIqbB5oAAAAi/baby-girl.gif',
)

FLEX_THUMBNAILS_XMAS_SNOWBALL: Final[tuple[str, ...]] = (
    'https://media.tenor.com/3vTclQPPOI8AAAAi/xheistmas-christmas.gif',
    'https://media.tenor.com/6YSQJKI2ZzMAAAAC/snowman-headstand.gif',
    'https://media.tenor.com/FTwJeB7qt_wAAAAC/frio-frozen.gif',
    'https://media.tenor.com/yoFePFtaN6IAAAAC/olafs-frozen-adventure-olaf.gif',
    'https://media.tenor.com/4q8uuszspWkAAAAC/caught-in-snowball-piu-piu.gif',
)

FLEX_THUMBNAILS_XMAS_VOID: Final[tuple[str, ...]] = (
    'https://media.tenor.com/IOdo6UKRfFEAAAAC/sora-kingdom-of-hearts.gif',
    'https://media.tenor.com/ZaSWJ7UW2JwAAAAC/ramadan-gift-eid-mubarak.gif',
    'https://media.tenor.com/ZmjNi_RIGfwAAAAC/black-friday-neon.gif',
    'https://media.giphy.com/media/rguWB3fUxRu5wMIFWB/giphy.gif',
    'https://media.tenor.com/Vfo2miCXT9kAAAAd/holiday-holidays.gif',
)
