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
ACTIVITIES_ALL.sort()
ACTIVITIES_ALL.insert(0, 'all')

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
    'horse-breed': 'horse',
    'horsebreeding': 'horse',
    'horse-breeding': 'horse',
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
    'clan',
    'daily',
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
    '**Yeti**',
    '**Hyper Giant Ice Block**',
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
}


SLASH_COMMANDS_NAVI = {
    'about': '</about:1017853591387656304>',
    'custom-reminder': '</custom-reminder:1017853591387656305>',
    'disable': '</disable:1017853591475724348>',
    'enable': '</enable:1017853591387656311>',
    'leaderboard guild': '</leaderboard guild:1017853591387656302>',
    'help': '</help:1017853591387656303>',
    'list': '</list:1017853591387656306>',
    'off': '</off:1017853591387656309>',
    'on': '</on:1017853591387656308>',
    'ready': '</ready:1017853591387656307>',
    'settings guild': '</settings guild:1017853591387656310>',
    'settings helpers': '</settings helpers:1017853591387656310>',
    'settings messages': '</settings messages:1017853591387656310>',
    'settings partner': '</settings partner:1017853591387656310>',
    'settings ready': '</settings ready:1017853591387656310>',
    'settings reminders': '</settings reminders:1017853591387656310>',
    'settings server': '</settings server:1017853591387656310>',
    'settings user': '</settings user:1017853591387656310>',
    'slashboard': '</slashboard:1026046376527806494>',
    'stats': '</stats:1017853591475724349>',
}


# Auto flex headlines
FLEX_WORK_HYPERLOG = [
    'TIMBER!',
    'Hyperino',
    'Justin, that you?',
    'I swear this happened',
]

FLEX_WORK_ULTRALOG = [
    'It\'s not a dream!',
    'This sounds dangerous',
    'That\'s not how you use a chainsaw',
    'Deforesting in progress',
    'Logging 101',
]

FLEX_WORK_ULTIMATELOG = [
    'Wood you log at that!',
    'What do you even need that stuff for?',
    'Chainsaw master',
    'Blinding logs',
    'Can\'t even dismantle it, lol',
]

FLEX_WORK_SUPERFISH = [
    'How much is the fish?',
    'Goodbye and thank you for the fish',
    'Nice fish, man',
    'Is fishing even allowed here?',
    'Better than an old boot, I guess',
]

FLEX_WORK_WATERMELON = [
    'One in a melon',
    'Rare doesn\'t mean useful, lol',
    'Anyone know what to do with these?',
    'Fruit robbery',
    'Deliciously useless',
]

FLEX_FORGE_COOKIE = [
    'Caution! Hot cookie!',
    'You sure you wanna eat that?',
    'What a weird recipe',
    'Next time just use an oven',
    'Someone say cookie?',
]

FLEX_LB_OMEGA_MULTIPLE = [
    'Caution! T10 horse at work!',
    'Horse power',
    'One wasn\'t enough apparently',
    'Now that\'s just greedy',
    'How is this even fair?',
]

FLEX_LB_OMEGA_NOHARDMODE = [
    'Now this is how you find an OMEGA',
    'Finally some proper lootboxing',
    'Take note, sweat lords',
    'Who even needs harmode?',
    'Hardmode is for losers',
]

FLEX_LB_OMEGA_PARTNER = [
    'Oops, wrong recipient, lol',
    'Mailman, you had one job',
    '"I am so happy for you, dear partner"',
    'WHAT ABOUT ME THO?',
    'Not jealous at all',
]

FLEX_LB_GODLY = [
    'Oh hello, what a nice lootbox',
    'Some heavenly luck right here',
    'Oh hey, how did that happen?',
    'Did someone lose a box?',
    'Oooohh... I\'ll take that, thank you',
]

FLEX_LB_GODLY_PARTNER = [
    'Best gift ever',
    '"Honey... I WANT IT BACK!"',
    '"MAILMAN... WE NEED TO TALK"',
    'True love',
    'Why does this never happen to ME?',
]

FLEX_LB_VOID = [
    'Now this is just hacking',
    'No more luck for you this year',
    'Is this even legal?',
    'Oh hey, it\'s Gladstone Gander',
]

FLEX_LB_VOID_PARTNER = [
    'I don\'t even know what to say',
    'Noone was ever supposed to see this line',
    'That\'s it, there\'s nothing else to achieve',
    'Bloody hell',
]

FLEX_EDGY_ULTRA = [
    'What could an EDGY ever be worth?',
    'I didn\'t even know this was possible, lol',
    'It\'s an achievement, right?',
    'Feels like christmas',
    'How did that end up in there?',
]

FLEX_GODLY_TT = [
    'There\'s luck, and then there\'s THIS',
    'Jeez, now that is something',
    'Don\'t get jealous folks... or do',
    'This should be a bannable offense',
    'WE ARE ALL HAPPY FOR YOU AND NOT AT ALL JEALOUS',
]

FLEX_PETS_CATCH_EPIC = [
    'EPIC pet incoming!',
    'What a nice kitty!',
    'Can I still pet it, tho?',
    'Great, and others can\'t even get one in fusions',
    'How many abandoned pets did this take?',
]

FLEX_PETS_CATCH_TT = [
    'K9, is that you?',
    'This can happen, yes',
    'Lost companion',
    'Wonder how old it is...',
    'Always close your phone box door',
]

FLEX_PR_ASCENSION = [
    'Up up and away',
    'Goodbye peasants!',
    'We demand a giveaway!',
]

FLEX_EVENT_LB = [
    'They did what now?',
    'Unauthorized magic',
    'Mr Ollivander approves',
    'I guess that\'s one way of getting an OMEGA',
    'Hey, gimme back my wand!',
]

FLEX_EVENT_ENCHANT = [
    'Twice the fun',
    'Can\'t even enchant properly, lol',
    'That\'s what happens when you use Ron\'s wand',
    'Well, at least it didn\'t explode',
]

FLEX_EVENT_FARM = [
    'Totally believable level up story',
    'The what now?',
    'This sounds like a hacking excuse',
    'You call this farming?',
    'Where did you buy those seeds again?',
]

FLEX_EVENT_HEAL = [
    'Very mysterious',
    'OH NO the poor guy',
    'So wait, this happened while HEALING?',
    'You sure that was a healing potion you drank there?',
    'Was that in Gotham by any chance?',
]

FLEX_EVENT_TRAINING = [
    'Who even needs a plane',
    'Yes, that\'s how I go to school all the time',
    'Tinkerbell? Is it you?',
    'Where did those even come from?',
    'So we call this "training" now?',
]

FLEX_COINFLIP_EVENT = [
    'Uh... how did that happen?',
    'Wait. Where\'s my coin?',
    'I didn\'t even know this could happen, lol',
    'Why is there a flex for this?',
    'MY COOOIIIINN NOOOOOOOOOOOOOOOOOOO',
]

FLEX_TIME_TRAVEL_1 = [
    'First time\'s always special',
    'Off to a great start!',
    'It\'s just a leap of faith',
    'First year student!',
    'First of many',
]

FLEX_TIME_TRAVEL_3 = [
    'Three? Three!',
    'Third year student!',
    'Hardmode time, baby',
    'Dungeon 13, coming for you!',
    'Thrice the fun',
]

FLEX_TIME_TRAVEL_5 = [
    'Five year student!',
    'Hardmode all the things!',
    'Five is the... eh... something number?',
    'Still playing, eh?',
    'The Famous Five',
]

FLEX_TIME_TRAVEL_10 = [
    'Ten year stud... uh, wait, no',
    'I hope you\'re not colorblind',
    'Hope you don\'t plan on hardmoding in A15',
    'Someone tried D15 without a bot once. They\'re still at it.',
    'Out of school',
    'Next stop: 25!',
]

FLEX_TIME_TRAVEL_25 = [
    'Endgame achieved',
    'The sky\'s the limit!',
    'No more mere time travels. We\'re jumping now, boyz.',
    'GG EZ',
    'Twenty bloody five',
]

FLEX_TIME_TRAVEL_50 = [
    '50 TTs and all I got was this lousy background',
    'Still at it! (for some reason)',
    'Loving dragon scales, I swear!',
    'How do you do, fellow kids',
    'Age is just a number',
]

FLEX_TIME_TRAVEL_100 = [
    'Hello, I would like my life back',
    'Next up: World domination',
    'Another beautiful profile background, oh thank you',
    'Why am I still playing this',
    'BOW BEFORE ME PEASANTS',
]