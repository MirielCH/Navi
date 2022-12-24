# strings.py
"""Contains global strings"""

# --- Error messages ---
MSG_INTERACTION_ERROR = 'You are not allowed to use this interaction.'


# --- Internal error messages ---
INTERNAL_ERROR_NO_DATA_FOUND = 'No data found in database.\nTable: {table}\nFunction: {function}\nSQL: {sql}'
INTERNAL_ERROR_SQLITE3 = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\SQL: {sql}'
INTERNAL_ERROR_LOOKUP = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\Records: {record}'
INTERNAL_ERROR_NO_ARGUMENTS = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'
INTERNAL_ERROR_DICT_TO_OBJECT = 'Error converting record into object\nFunction: {function}\nRecord: {record}\n'


# Links
LINK_GITHUB = 'https://github.com/Miriel-py/Navi'
LINK_PRIVACY_POLICY = 'https://github.com/Miriel-py/Navi/blob/master/PRIVACY.md'

# --- Default messages ---
DEFAULT_MESSAGE = '{name} Hey! It\'s time for {command}!'
DEFAULT_MESSAGE_EVENT = (
    '{name} Hey! The **{event}** event just finished! You can check the results in <#604410216385085485> on the '
    f'official EPIC RPG server.'
)
DEFAULT_MESSAGE_CUSTOM_REMINDER = 'Hey! This is your reminder for **{message}**!'

DEFAULT_MESSAGES = {
    'advent-calendar': DEFAULT_MESSAGE,
    'adventure': DEFAULT_MESSAGE,
    'arena': DEFAULT_MESSAGE,
    'big-arena': DEFAULT_MESSAGE_EVENT,
    'chimney': DEFAULT_MESSAGE,
    #'boo': DEFAULT_MESSAGE,
    'daily': DEFAULT_MESSAGE,
    'duel': DEFAULT_MESSAGE,
    'dungeon-miniboss': DEFAULT_MESSAGE,
    'epic': '{name} Hey! Your EPIC item cooldown is ready!',
    'farm': DEFAULT_MESSAGE,
    'guild': DEFAULT_MESSAGE,
    'horse': DEFAULT_MESSAGE,
    'horse-race': DEFAULT_MESSAGE_EVENT,
    'hunt': DEFAULT_MESSAGE,
    'lootbox': DEFAULT_MESSAGE,
    'lottery': '{name} Hey! The lottery just finished. Use </lottery:957815874063061072> to check out who won and {command} to enter the next draw!',
    'minintboss': DEFAULT_MESSAGE_EVENT,
    'partner': '{name} **{partner}** found {loot} for you!',
    'pets': '{name} Hey! Your pet `{id}` is back! {emoji}',
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

MSG_ERROR = 'Whoops, something went wrong here. You should probably tell Miriel#0001 about this.'
MSG_SYNTAX = 'The command syntax is `{syntax}`.'

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
    #'boo',
    'chimney',
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

TIME_COOKIE_AFFECTED_ACTIVITIES = (
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
    'advent-calendar',
    'adventure',
    'arena',
    'big-arena',
    #'boo',
    'chimney',
    'daily',
    'duel',
    'dungeon-miniboss',
    'epic',
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
ACTIVITIES_ALL.sort()
ACTIVITIES_ALL.insert(0, 'all')

ACTIVITIES_COMMANDS = (
    'advent-calendar',
    'adventure',
    'arena',
    #'boo',
    'chimney',
    'daily',
    'duel',
    'dungeon-miniboss',
    'epic',
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
    'advent-calendar': 'xmas calendar',
    'adventure': 'adventure',
    'arena': 'arena',
    'big-arena': 'big arena',
    'boo': 'hal boo',
    'chimney': 'xmas chimney',
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
    'working commands': 'work',
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
    'horse-breed': 'horse',
    'horsebreeding': 'horse',
    'horse-breeding': 'horse',
    'horse commands': 'horse',
    'breed': 'horse',
    'breeding': 'horse',
    'dueling': 'duel',
    'duelling': 'duel',
}

ACTIVITIES_COLUMNS = {
    'advent-calendar': 'alert_advent',
    'adventure': 'alert_adventure',
    'arena': 'alert_arena',
    'big-arena': 'alert_big_arena',
    'boo': 'alert_boo',
    'chimney': 'alert_chimney',
    'daily': 'alert_daily',
    'duel': 'alert_duel',
    'dungeon-miniboss': 'alert_dungeon_miniboss',
    'epic': 'alert_epic',
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
    'clan',
    'chimney',
    'daily',
    'epic',
    'farm',
    'horse',
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'training',
    'weekly',
    'work',
)
ACTIVITIES_WITH_COOLDOWN_ALL = list(ACTIVITIES_WITH_COOLDOWN[:])
ACTIVITIES_WITH_COOLDOWN_ALL.sort()
ACTIVITIES_WITH_COOLDOWN_ALL.insert(0, 'all')

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
    '**Krampus**',
    '**Yeti**',
    '**Hyper Giant Ice Block**',
    '**Bat Slime**',
)

MONSTERS_ADVENTURE_TOP = (
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
    '**Christmas Slime**',
)

MONSTERS_HUNT_TOP = (
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
    'cd': '</cd:958554802038636654>',
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
    'enchant': '</enchant:959164903745257532>',
    'epic quest': '</epic quest:961046236469792810>',
    'event': '</event:959164906903584838>',
    'farm': '</farm:959915738716598272>',
    'forge': '</forge:960002338121203722>',
    'fish': '</fish:959163594665242684>',
    'greenhouse': '</greenhouse:959164279884509194>',
    'guild list': '</guild list:961046237753257994>',
    'guild raid': '</guild raid:961046237753257994>',
    'guild stats': '</guild stats:961046237753257994>',
    'guild upgrade': '</guild upgrade:961046237753257994>',
    'hal boo': '</hal boo:1031664514250330192>',
    'heal': '</heal:959915737777061928>',
    'horse breeding': '</horse breeding:966961638378987540>',
    'horse race': '</horse race:966961638378987540>',
    'horse stats': '</horse stats:966961638378987540>',
    'hunt': '</hunt:964351961774325770>',
    'inventory': '</inventory:958555797590265896>',
    'jail': '</jail:966956629411123201>',
    'ladder': '</ladder:959164278072569936>',
    'lottery': '</lottery:957815874063061072>',
    'megarace': '</hf megarace:1003530661761663087>',
    'mine': '</mine:959164539922952263>',
    'miniboss': '</miniboss:960740632400388146>',
    "minintboss": '</minintboss:960362922813575209>',
    "multidice": '</multidice:958558816818036776>',
    'net': '</net:959163595428618290>',
    'open': '</open:959164544696070154>',
    'pets adventure': '</pets adventure:961046238613090385>',
    'pets claim': '</pets claim:961046238613090385>',
    'pets fusion': '</pets fusion:961046238613090385>',
    'pets list': '</pets list:961046238613090385>',
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
    'tractor': '</tractor:959164278890463272>',
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
    'xmas calendar': '</xmas calendar:1048310047865852005>',
    'xmas chimney': '</xmas chimney:1048310047865852005>',
}

RPG_COMMANDS = {
    'adventure': 'rpg adventure',
    'arena': 'rpg arena',
    'axe': 'rpg axe',
    'big arena': 'rpg big arena join',
    'big dice': 'rpg big dice',
    'bigboat': 'rpg bigboat',
    'blackjack': 'rpg blackjack',
    'boat': 'rpg boat',
    'bowsaw': 'rpg bowsaw',
    'buy': 'rpg buy',
    'cd': 'rpg cd',
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
    'megarace': 'rpg hf megarace',
    'mine': 'rpg mine',
    'miniboss': 'rpg miniboss',
    "minintboss": 'rpg minintboss join',
    "multidice": 'rpg multidice',
    'net': 'rpg net',
    'open': 'rpg open',
    'pets adventure': 'rpg pets adventure',
    'pets claim': 'rpg pets adventure claim',
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
    'tractor': 'rpg tractor',
    'trade items': 'rpg trade',
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
}


# Auto flex headlines
FLEX_TITLES_WORK_HYPERLOG = [
    'TIMBER!',
    'Hyperino',
    'Justin?',
    'I swear this is how it happened',
    'Wooooh...d!',
    'Y dis never happen in A3',
    'Wood you log at this bad pun',
    'Log? Log!',
    'Logging 101',
]

FLEX_TITLES_WORK_ULTRALOG = [
    'It\'s not a dream!',
    'This sounds dangerous',
    'That\'s not how you use a chainsaw',
    'Deforesting in progress',
]

FLEX_TITLES_WORK_ULTIMATELOG = [
    'What do you even need that stuff for?',
    'Chainsaw master',
    'Can\'t even dismantle it, lol',
]

FLEX_TITLES_WORK_SUPERFISH = [
    'How much is the fish?',
    'Goodbye and thank you for the fish',
    'Nice fish, man',
    'Is fishing even allowed here?',
    'Better than an old boot, I guess',
]

FLEX_TITLES_WORK_WATERMELON = [
    'One in a melon',
    'Rare doesn\'t mean useful, lol',
    'Anyone know what to do with these?',
    'Fruit robbery',
    'Deliciously useless',
    'Meloncholia',
]

FLEX_TITLES_FORGE_COOKIE = [
    'Caution! Hot cookie!',
    'You sure you wanna eat that?',
    'What a weird recipe',
    'Next time just use an oven',
    'Someone say cookie?',
]

FLEX_TITLES_HAL_BOO = [
    'Stop scaring people, will ya?',
    'AAAAAAAAAAAAHHHHHHHHHHHH',
    'Boo or booh?',
    'A treat for the trick',
    'Hope they didn\'t get a heart attack',
    'Halloween hacking',
]

FLEX_TITLES_LB_OMEGA_MULTIPLE = [
    'Caution! T10 horse at work!',
    'Horse power',
    'One wasn\'t enough apparently',
    'Now that\'s just greedy',
    'How is this even fair?',
    'My precious',
]

FLEX_TITLES_LB_OMEGA_NOHARDMODE = [
    'Now this is how you find an OMEGA',
    'Finally some proper lootboxing',
    'Take note, sweat lords',
    'Who even needs harmode?',
    'Hardmode is for losers',
]

FLEX_TITLES_LB_OMEGA_PARTNER = [
    'Oops, wrong recipient, lol',
    'Mailman, you had one job',
    '"I am so happy for you, dear partner"',
    'WHAT ABOUT ME THO?',
    'Not jealous at all',
]

FLEX_TITLES_LB_GODLY = [
    'Oh hello, what a nice lootbox',
    'Some heavenly luck right here',
    'Oh hey, how did that happen?',
    'Did someone lose a box?',
    'Oooohh... I\'ll take that, thank you',
]

FLEX_TITLES_LB_GODLY_PARTNER = [
    'Best gift ever',
    '"Honey... I WANT IT BACK!"',
    '"MAILMAN... WE NEED TO TALK"',
    'True love',
    'Why does this never happen to ME?',
]

FLEX_TITLES_LB_VOID = [
    'Now this is just hacking',
    'No more luck for you this year',
    'Is this even legal?',
    'Oh hey, it\'s Gladstone Gander',
]

FLEX_TITLES_LB_VOID_PARTNER = [
    'I don\'t even know what to say',
    'Noone was ever supposed to see this line',
    'That\'s it, there\'s nothing else to achieve',
    'Bloody hell',
]

FLEX_TITLES_EDGY_ULTRA = [
    'What could an EDGY ever be worth?',
    'I didn\'t even know this was possible, lol',
    'It\'s an achievement, right?',
    'Feels like christmas',
    'How did that end up in there?',
]

FLEX_TITLES_OMEGA_ULTRA = [
    'This OMEGA is better than yours',
    'Pro unboxing',
    'Teach us',
    'Don\'t be jealous',
    'Why are my OMEGAs never like this?',
]

FLEX_TITLES_GODLY_TT = [
    'There\'s luck, and then there\'s THIS',
    'Jeez, now that is something',
    'Don\'t get jealous folks... or do',
    'This should be a bannable offense',
    'WE ARE ALL HAPPY FOR YOU AND NOT AT ALL JEALOUS',
]

FLEX_TITLES_PETS_CATCH_EPIC = [
    'EPIC pet incoming!',
    'What a nice kitty!',
    'Can I still pet it, tho?',
    'Great, and others can\'t even get one in fusions',
    'How many abandoned pets did this take?',
]

FLEX_TITLES_PETS_CATCH_TT = [
    'K9, is that you?',
    'This can happen, yes',
    'Lost companion',
    'Wonder how old it is...',
    'Always close your phone box door',
]

FLEX_TITLES_PR_ASCENSION = [
    'Up up and away',
    'Goodbye peasants!',
    'We demand a giveaway!',
]

FLEX_TITLES_EVENT_LB = [
    'They did what now?',
    'Unauthorized magic',
    'Mr Ollivander approves',
    'I guess that\'s one way of getting an OMEGA',
    'Hey, gimme back my wand!',
]

FLEX_TITLES_EVENT_ENCHANT = [
    'Twice the fun',
    'Can\'t even enchant properly, lol',
    'That\'s what happens when you use Ron\'s wand',
    'Well, at least it didn\'t explode',
]

FLEX_TITLES_EVENT_FARM = [
    'Totally believable level up story',
    'The what now?',
    'This sounds like a hacking excuse',
    'You call this farming?',
    'Where did you buy those seeds again?',
]

FLEX_TITLES_EVENT_HEAL = [
    'Very mysterious',
    'OH NO the poor guy',
    'So wait, this happened while HEALING?',
    'You sure that was a healing potion you drank there?',
    'Was that in Gotham by any chance?',
]

FLEX_TITLES_EVENT_TRAINING = [
    'Who even needs a plane',
    'Yes, that\'s how I go to school all the time',
    'Tinkerbell? Is it you?',
    'Where did those even come from?',
    'So we call this "training" now?',
]

FLEX_TITLES_COINFLIP_EVENT = [
    'Uh... how did that happen?',
    'Wait. Where\'s my coin?',
    'I didn\'t even know this could happen, lol',
    'Why is there a flex for this?',
    'MY COOOIIIINN NOOOOOOOOOOOOOOOOOOO',
]

FLEX_TITLES_TIME_TRAVEL_1 = [
    'First time\'s always special',
    'Off to a great start!',
    'It\'s just a leap of faith',
    'First year student!',
    'First of many',
]

FLEX_TITLES_TIME_TRAVEL_3 = [
    'Three? Three!',
    'Third year student!',
    'Hardmode time, baby',
    'Dungeon 13, coming for you!',
    'Thrice the fun',
]

FLEX_TITLES_TIME_TRAVEL_5 = [
    'Five year student!',
    'Hardmode all the things!',
    'Five is the... eh... something number?',
    'Still playing, eh?',
    'The Famous Five',
]

FLEX_TITLES_TIME_TRAVEL_10 = [
    'Ten year stud... uh, wait, no',
    'I hope you\'re not colorblind',
    'Hope you don\'t plan on hardmoding in A15',
    'Someone tried D15 without a bot once. They\'re still at it.',
    'Out of school',
    'Next stop: 25!',
]

FLEX_TITLES_TIME_TRAVEL_25 = [
    'Endgame achieved',
    'The sky\'s the limit!',
    'No more mere time travels. We\'re jumping now, boyz.',
    'GG EZ',
    'Twenty bloody five',
]

FLEX_TITLES_TIME_TRAVEL_50 = [
    '50 TTs and all I got was this lousy background',
    'Still at it! (for some reason)',
    'Loving dragon scales, I swear!',
    'How do you do, fellow kids',
    'Age is just a number',
]

FLEX_TITLES_TIME_TRAVEL_100 = [
    'Hello, I would like my life back',
    'Next up: World domination',
    'Another beautiful profile background, oh thank you',
    'Why am I still playing this',
    'BOW BEFORE ME PEASANTS',
]

FLEX_TITLES_XMAS_CHIMNEY = [
    'Now this is embarassing',
    'Can we get a live stream?',
    'Hope noone is making a fire',
    'Enjoy your break',
    'Imagine how many hunts you could do in that time',
    'We are not laughing, I swear',
]

FLEX_TITLES_XMAS_GODLY = [
    'Oh thank you Santa!',
    'Ho ho ho',
    'You sure you deserve this?',
    'Someone must have dropped this',
    'Look at that shiny paper',
    'WHAT IS IT? WHAT IS IT?',
]

FLEX_TITLES_XMAS_SNOWBALL = [
    'Yellow snow? Uh, yeah, you can keep that',
    'Look, it\'s glowing!',
    'But can you upgrade it to a MEGA snowball?',
    'Hope it doesn\'t melt',
]

FLEX_TITLES_XMAS_VOID = [
    'Probably bribed Rudolf',
    'Santa is real!',
    'Clearly Santa\'s favourite',
    'And they get this after eating all the cookies?',
    'I think that one was meant for me',
]


# Auto flex thumbnails
FLEX_THUMBNAILS_WORK_HYPERLOG = [
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
]

FLEX_THUMBNAILS_WORK_ULTIMATELOG = [
    'https://media.giphy.com/media/SGV9O1fuh2nf5T8FNW/giphy-downsized-large.gif',
    'https://media.tenor.com/vfraS_QhPcEAAAAd/captain-america-pecs.gif',
    'https://media.tenor.com/Gd9zrsML1tYAAAAC/im-building-construction.gif',
]

FLEX_THUMBNAILS_WORK_ULTRALOG = [
    'https://c.tenor.com/4ReodhBihBQAAAAC/ruthe-biber.gif',
    'https://media.giphy.com/media/0eVM7GVxTDDKxn7OyX/giphy.gif',
    'https://media.tenor.com/B984YMYS43IAAAAC/chainsaw-wood-cutting.gif',
    'https://media.tenor.com/oSSU2r9NWrMAAAAC/freddie-chainsaw.gif',
]

FLEX_THUMBNAILS_WORK_SUPERFISH = [
    'https://media.tenor.com/B6dwDGql374AAAAC/mcdonald-chris-mcdonald.gif',
    'https://media.tenor.com/4fGHA-FQ-N8AAAAC/fiska-fisk.gif',
    'https://media.tenor.com/25FSuyo3WWQAAAAi/%E6%80%9D%E8%80%83%E5%96%B5%E7%94%9F-peach-cat-and-goma.gif',
    'https://media.tenor.com/nW_vYquFoGwAAAAC/fish-love.gif',
    'https://media.tenor.com/HLYz9zk-fGQAAAAC/rumia-fish-gif.gif',
]

FLEX_THUMBNAILS_WORK_WATERMELON = [
    'https://media.tenor.com/mAxfGDKXrZUAAAAC/bunnies-cute.gif',
    'https://media.tenor.com/1qy7WBALXg8AAAAC/water.gif',
    'https://media.tenor.com/o3oQXq9guVAAAAAd/maya-dog.gif',
    'https://media.tenor.com/3laUQPe252YAAAAC/rabbit-watermelon.gif',
    'https://media.tenor.com/uS6xykUe7NcAAAAC/pinch-%D5%B1%D5%B4%D5%A5%D6%80%D5%B8%D6%82%D5%AF.gif',
]

FLEX_THUMBNAILS_FORGE_COOKIE = [
    'https://media.tenor.com/YP5Xv8Sa45IAAAAC/cookie-monster-awkward.gif',
    'https://media.giphy.com/media/Y09s2Frxp7wpBGXTyt/giphy.gif',
    'https://media.giphy.com/media/bAlYQOugzX9sY/giphy.gif',
]

FLEX_THUMBNAILS_HAL_BOO = [
    'https://media.tenor.com/M6MkMfBBDjcAAAAC/afraid-scared.gif',
    'https://media.tenor.com/LzqPLLcuAqsAAAAC/peachcat-boo.gif',
    'https://media.tenor.com/xdP3iAkkZ6cAAAAC/ghost-spooky.gif',
    'https://media.tenor.com/xdP3iAkkZ6cAAAAC/ghost-spooky.gif',
    'https://media.tenor.com/SM5IBkvYeX0AAAAC/halloween-creepy-pumpkin.gif',
    'https://media.tenor.com/A6zk0D9xNVcAAAAC/boo-ghosts.gif',
    'https://media.giphy.com/media/12RfP2odT4hEOI/giphy.gif',
    'https://media.giphy.com/media/3o7TKqnN349PBUtGFO/giphy.gif',
]

FLEX_THUMBNAILS_LB_OMEGA_MULTIPLE = [
    'https://media.tenor.com/gHygBs_JkKwAAAAi/moving-boxes.gif',
    'https://media.tenor.com/h5-edZgGfu0AAAAC/boxes-move-in-day.gif',
    'https://media.tenor.com/uoCDp8f_ZicAAAAC/horse-hahaha.gif',
    'https://media.tenor.com/DYxjt7HJ4LQAAAAC/i-need-a-horse-thor.gif',
]

FLEX_THUMBNAILS_LB_OMEGA_NOHARDMODE = [
    'https://media.tenor.com/JQIXRoPBLqYAAAAC/impressive-20th-century.gif',
    'https://media.giphy.com/media/9VrBXYVGAX0bAEzSAT/giphy.gif',
]

FLEX_THUMBNAILS_LB_OMEGA_PARTNER = [
    'https://c.tenor.com/l0wNXZN58S8AAAAC/delivery-kick.gif',
    'https://media.giphy.com/media/AdExwGjrXYjH7yjuIc/giphy.gif',
    'https://media.tenor.com/OhwPShbFvjcAAAAC/package-ups.gif',
    'https://media.tenor.com/_lu2Jz1q1s0AAAAC/sunday-delivery.gif',
]

FLEX_THUMBNAILS_LB_GODLY = [
    'https://c.tenor.com/zBe7Ew1lzPYAAAAi/tkthao219-bubududu.gif',
    'https://media.tenor.com/f8-9UL5OveIAAAAi/box-cute.gif',
    'https://media.tenor.com/ZDW2vrkgYB4AAAAC/whats-inside-ricky-berwick.gif',
    'https://media.tenor.com/kI9zfph0YdIAAAAC/andre-leon-talley-present.gif',
    'https://media.tenor.com/GXVWyf8jBgsAAAAd/dancing-box-happy-box.gif',
]

FLEX_THUMBNAILS_LB_GODLY_PARTNER = [
    'https://media.tenor.com/NvP2dNkQWtEAAAAC/i-got-us-a-box-anthony-mennella.gif',
    'https://media.giphy.com/media/mDIQaHAhD33wlOz0DR/giphy.gif',
    'https://media.tenor.com/ClAp685q6pEAAAAC/drop-off-dropping-off-a-package.gif',
]

FLEX_THUMBNAILS_LB_VOID = [
    'https://media.giphy.com/media/JkpHPyZowX6sfFvKp6/giphy.gif',
]

FLEX_THUMBNAILS_LB_VOID_PARTNER = [
    'https://media.tenor.com/kumodwVv1bcAAAAC/patrick-the-maniacs-in-mail-box.gif',
    'https://media.giphy.com/media/atfHlwAhizfxdtdw60/giphy.gif',
]

FLEX_THUMBNAILS_EDGY_ULTRA = [
    'https://c.tenor.com/clnoM8TeSxcAAAAC/wait-what-unbelievable.gif',
    'https://media.giphy.com/media/GjbR6R2XeWKS0yfQaZ/giphy.gif',
]

FLEX_THUMBNAILS_OMEGA_ULTRA = [
    'https://media.tenor.com/Dmr7SzwDii0AAAAC/andy-office.gif',
    'https://media.tenor.com/kJNvpynpU3sAAAAi/boxy-kitten-peek-a-boo.gif',
    'https://media.giphy.com/media/Q9Clm1DwDR0WWF7Qr4/giphy.gif',
    'https://media.giphy.com/media/xUOxf8sb4pizGFkBJm/giphy.gif',
    'https://media.giphy.com/media/5Y2bU7FqLOuzK/giphy.gif',
    'https://media.giphy.com/media/M9CoztwchmOdSRGH2m/giphy.gif',
    'https://media.giphy.com/media/3KXd872FGuIO0u0e7h/giphy.gif',
    'https://media.tenor.com/TukiL_LftA0AAAAC/loz-botw.gif',
]

FLEX_THUMBNAILS_GODLY_TT = [
    'https://c.tenor.com/-BVQhBulOmAAAAAC/bruce-almighty-morgan-freeman.gif',
    'https://media.giphy.com/media/jltuIcAMViLHYaz9bN/giphy.gif',
]

FLEX_THUMBNAILS_PETS_CATCH_EPIC = [
    'https://media.tenor.com/WnprYvrvNp8AAAAC/cat-kitty.gif',
    'https://media.giphy.com/media/xUOxf8izqVvHEBhRO8/giphy-downsized-large.gif',
    'https://media.giphy.com/media/QQPpBZs31y2fijvNzo/giphy.gif',
    'https://media.giphy.com/media/7dwrVhuNR1rPi/giphy.gif',
]

FLEX_THUMBNAILS_PETS_CATCH_TT = [
    'https://media.tenor.com/7LMaSfhq9TIAAAAC/flying-omw.gif',
    'https://media.giphy.com/media/3qsCqrKYjq5DkANgBE/giphy.gif',
    'https://media.giphy.com/media/5E7vDOIamcWlzg97TG/giphy.gif',
    'https://media.giphy.com/media/U7JM6ChJMrFnXfFHvE/giphy.gif',
]

FLEX_THUMBNAILS_PR_ASCENSION = [
    'https://media.tenor.com/wfma4CqwxCwAAAAC/railgun-misaka-mikoto.gif',
    'https://media.tenor.com/NF5dnWvoaN8AAAAC/glameow-purugly.gif',
    'https://media.tenor.com/EoCQm0KsqP8AAAAC/pokemon-anime.gif',
]

FLEX_THUMBNAILS_EVENT_LB = [
    'https://media.tenor.com/wn2_Qq6flogAAAAC/magical-magic.gif',
    'https://media.giphy.com/media/mz1kJeDVueKC4/giphy.gif',
    'https://media.giphy.com/media/MePp78CYbOaYh3iNBZ/giphy-downsized-large.gif',
    'https://media.giphy.com/media/LR5UmQvLDDRqp9BI9x/giphy.gif',
]

FLEX_THUMBNAILS_EVENT_ENCHANT = [
    'https://c.tenor.com/gAuPzxRCVw8AAAAC/link-dancing.gif',
    'https://media.giphy.com/media/ef4gyEAxktrF3cWO5g/giphy.gif',
    'https://media.tenor.com/oTpEgUkQjngAAAAC/vibing-dancing.gif',
    'https://media.tenor.com/9-b0gUv-HokAAAAC/enchanted-sword-enchanted-iron-sword.gif',
    'https://media.tenor.com/Z3mgGQaNQt4AAAAC/legendofzelda-navi.gif',
]

FLEX_THUMBNAILS_EVENT_FARM = [
    'https://media.tenor.com/z1ru-IqnJFoAAAAC/earthquake-four-arms.gif',
    'https://media.giphy.com/media/apvx5lPCPsjN6/giphy.gif',
    'https://media.giphy.com/media/h4Z6RfuQycdiM/giphy.gif',
    'https://media.giphy.com/media/2SZeeNMm456NO/giphy.gif',
]

FLEX_THUMBNAILS_EVENT_HEAL = [
    'https://media.tenor.com/lh60y7i9SeQAAAAC/peachmad-peachandgoma.gif',
    'https://media.tenor.com/gaHlo3VAWrwAAAAd/invisible-friends-crime-scene.gif',
    'https://media.tenor.com/gs7Wpi7iJBQAAAAC/tmm-the-mystery-man.gif',
    'https://media.tenor.com/yST82xLuBOQAAAAd/standing-still-jake-lyon.gif',
]

FLEX_THUMBNAILS_EVENT_TRAINING = [
    'https://media.tenor.com/YAaId6OVgFUAAAAC/baby-up.gif',
    'https://media.giphy.com/media/B5BP3OYgVN5ss/giphy.gif',
    'https://media.giphy.com/media/yXBqba0Zx8S4/giphy.gif',
    'https://media.tenor.com/C_YenjB3niUAAAAC/tinkerbell-happy.gif',
]

FLEX_THUMBNAILS_COINFLIP_EVENT = [
    'https://media.tenor.com/Adg8-XpUrEIAAAAd/john-travolta-confused.gif',
    'https://media.giphy.com/media/JQG2I0rQejbRQiDMQZ/giphy.gif',
    'https://media.tenor.com/8yBy9hKYpBkAAAAC/where-is-it-melody-pedras.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_1 = [
    'https://media.tenor.com/7n7-MMKE8HUAAAAC/im-a-time-traveler-time-traveler.gif',
    'https://media.tenor.com/EYMfaM_5e7wAAAAC/hulk-endgame.gif',
    'https://media.tenor.com/VVKQ2r1T5n0AAAAd/its-time-travel-sam-hart.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_3 = [
    'https://media.tenor.com/XATWkMEOrZIAAAAC/doctor-dance-doctor-who-dances.gif',
    'https://media.tenor.com/XO52a0Voe2AAAAAC/fantastic-doctor-who.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_5 = [
    'https://media.tenor.com/GctGuDyWlOMAAAAC/back-to-the-future-back-to-the-past.gif',
    'https://media.tenor.com/xXXrBidPuPEAAAAC/back-to-the-future-doc-brown.gif',
    'https://media.tenor.com/SD-TxYTh3scAAAAd/precisely-on-schedule-right-on-schedule.gif',
    'https://media.tenor.com/K84SJ6-ycMUAAAAC/msmbttf-bttf.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_10 = [
    'https://media.tenor.com/pDdh_ISRzZIAAAAC/doctor-who-dr-who.gif',
    'https://media.tenor.com/ZIUSH-XNatEAAAAC/doctorwho-tardis.gif',
    'https://media.tenor.com/dSLlCYF7vikAAAAC/tardis-doctor.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_25 = [
    'https://media.tenor.com/mh75FCw3VpoAAAAC/avengers-end-game-black-widow.gif',
    'https://media.tenor.com/FK0u5g5qQUcAAAAd/dr-strange-doctor-strange.gif',
    'https://media.tenor.com/o3S8K00A2CQAAAAC/the-end-game-welcome-to-the-end-game.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_50 = [
    'https://media.tenor.com/n-vLx1Q_QBQAAAAC/fn2187.gif',
    'https://media.tenor.com/P3iWMO_GKksAAAAC/abstract-art.gif',
    'https://media.tenor.com/U5DTTODnuTcAAAAC/trippy-tripping.gif',
]

FLEX_THUMBNAILS_TIME_TRAVEL_100 = [
    'https://media.tenor.com/J82kuX8dFysAAAAC/blue-spiral.gif',
    'https://media.tenor.com/_Ep8uvjeSHQAAAAC/moon-digibyte.gif',
    'https://media.giphy.com/media/xT39CTrFW4nHLdBPpu/giphy-downsized-large.gif',
]

FLEX_THUMBNAILS_XMAS_CHIMNEY = [
    'https://media.tenor.com/RNBD-BUVb3cAAAAi/chimney-santa.gif',
    'https://media.tenor.com/scEtOL9oeMoAAAAi/sumikko-gurashi-chimney-santa.gif',
    'https://media.tenor.com/7Hh1I-SmB3cAAAAi/playmobil-christmas.gif',
    'https://media.tenor.com/54bt7hOcqdsAAAAi/christmas-red.gif',
    'https://media.tenor.com/MCn_GMSSqAsAAAAd/lol-laughing-hysterically.gif',
    'https://media.tenor.com/lr8W5AadieAAAAAd/smile-laughing.gif',
    'https://media.tenor.com/REqgDts8CVgAAAAC/futurenostlgia-laughing.gif',
    'https://media.tenor.com/Lot4htkwha8AAAAd/adventures-of-oliver-twist-stuck.gif',
]

FLEX_THUMBNAILS_XMAS_GODLY = [
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
]

FLEX_THUMBNAILS_XMAS_SNOWBALL = [
    'https://media.tenor.com/3vTclQPPOI8AAAAi/xheistmas-christmas.gif',
    'https://media.tenor.com/6YSQJKI2ZzMAAAAC/snowman-headstand.gif',
    'https://media.tenor.com/FTwJeB7qt_wAAAAC/frio-frozen.gif',
    'https://media.tenor.com/yoFePFtaN6IAAAAC/olafs-frozen-adventure-olaf.gif',
    'https://media.tenor.com/4q8uuszspWkAAAAC/caught-in-snowball-piu-piu.gif',
]

FLEX_THUMBNAILS_XMAS_VOID = [
    'https://media.tenor.com/IOdo6UKRfFEAAAAC/sora-kingdom-of-hearts.gif',
    'https://media.tenor.com/ZaSWJ7UW2JwAAAAC/ramadan-gift-eid-mubarak.gif',
    'https://media.tenor.com/ZmjNi_RIGfwAAAAC/black-friday-neon.gif',
    'https://media.giphy.com/media/rguWB3fUxRu5wMIFWB/giphy.gif',
    'https://media.tenor.com/Vfo2miCXT9kAAAAd/holiday-holidays.gif',
]