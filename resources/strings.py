# strings.py
"""Contains global strings"""

# Internal error messages
INTERNAL_ERROR_NO_DATA_FOUND = 'No data found in database.\nTable: {table}\nFunction: {function}\nSQL: {sql}'
INTERNAL_ERROR_SQLITE3 = 'Error executing SQL.\nError: {error}\nTable: {table}\nFunction: {function}\SQL: {sql}'
INTERNAL_ERROR_LOOKUP = 'Error assigning values.\nError: {error}\nTable: {table}\nFunction: {function}\Records: {record}'
INTERNAL_ERROR_NO_ARGUMENTS = 'You need to specify at least one keyword argument.\nTable: {table}\nFunction: {function}'
INTERNAL_ERROR_DICT_TO_OBJECT = 'Error converting record into object\nFunction: {function}\nRecord: {record}\n'

DEFAULT_MESSAGE = 'Hey! It\'s time for `{command}`!'
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
    'horse': DEFAULT_MESSAGE,
    'horse-race': DEFAULT_MESSAGE_EVENT,
    'hunt': DEFAULT_MESSAGE,
    'lootbox': DEFAULT_MESSAGE,
    'lottery': 'Hey! The lottery just finished. Use `rpg lottery` to check out who won and `{command}` to enter the next draw!',
    'not-so-mini-boss': DEFAULT_MESSAGE_EVENT,
    'partner': '**{user}** found {lootbox} for you!',
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
    '**{username}**, you are not registered as a guild leader. Only guild leaders can do this.\n'
    'If you are a guild leader, run `rpg guild list` first to add or update your guild in my database.'
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
    'horse',
    'horse-race',
    'hunt',
    'lootbox',
    'lottery',
    'not-so-mini-boss',
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

ACTIVITIES_EVENTS = (
    'big-arena',
    'horse-race',
    'lottery',
    'not-so-mini-boss',
    'pet-tournament',
)

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
    'notsominiboss': 'not-so-mini-boss',
    'notsomini': 'not-so-mini-boss',
    'nsmb': 'not-so-mini-boss',
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
    'horse': 'alert_horse_breed',
    'horse-race': 'alert_horse_race',
    'hunt': 'alert_hunt',
    'lootbox': 'alert_lootbox',
    'lottery': 'alert_lottery',
    'not-so-mini-boss': 'alert_not_so_mini_boss',
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
    'hunt',
    'lootbox',
    'dungeon-miniboss',
    'quest',
    'training',
    'weekly',
    'work',
)

WORK_COMMANDS = (
    'chop',
    'axe',
    'bowsaw',
    'chainsaw',
    'fish',
    'net',
    'boat',
    'bigboat',
    'pickup',
    'ladder',
    'tractor',
    'greenhouse',
    'mine',
    'pickaxe',
    'drill',
    'dynamite',
)

MONSTERS_ADVENTURE = (
    'Ancientest Dragon',
    'Yes, As You Expected, Another Hyper Giant Dragon But OP etc',
    'Another Mutant Dragon Like In Area 11 But Stronger',
    'Attack Helicopter',
    'Bunch of Bees',
    'Chimera',
    'Centaur',
    'Cyclops',
    'Dark Knight',
    'Dinosaur',
    'Ent',
    'Even More Ancient Dragon',
    'Giant Spider',
    'Golem',
    'Hydra',
    'Hyper Giant Aeronautical Engine',
    'Hyper Giant Bowl',
    'Hyper Giant Chest',
    'Hyper Giant Door',
    'Hyper Giant Dragon',
    'Hyper Giant Toilet',
    'I Have No More Ideas Dragon',
    'Just Purple Dragon',
    'Kraken',
    'Leviathan',
    'Mammoth',
    'Mutant Book',
    'Mutant Backpack',
    'Mutant Dragon',
    "Mutant 'ESC' Key",
    'Mutantest Dragon',
    'Mutant Shoe',
    'Mutant Water Bottle',
    'Ogre',
    'Titan',
    'Typhon',
    'War Tank',
    'Wyrm',
    'Werewolf',
    'Ancient Dragon',
    'Time Annihilator',
    'Time Devourer',
    'Time Slicer',
    'Black Hole',
    'Supernova',
    'Wormhole',
    'Corrupted Killer Robot',
    'Corrupted Mermaid',
    'Corrupted Dragon',
    'Shadow Creature',
    'Shadow Entity',
    'Abyss Worm',
    'Void Cone',
    'Void Cube',
    'Void Sphere',
)

MONSTERS_HUNT = (
    'Adult Dragon',
    'Baby Demon',
    'Baby Dragon',
    'Baby Robot',
    'Cecaelia',
    'Definitely Not Young Dragon',
    'Demon',
    'Dullahan',
    'Giant Crocodile',
    'Giant Piranha',
    'Giant Scorpion',
    'Ghoul',
    'Ghost',
    'Goblin',
    'Harpy',
    'How Do You Dare Call This Dragon "Young"???',
    'Imp',
    'Kid Dragon',
    'Killer Robot',
    'Manticore',
    'Mermaid',
    'Not So Young Dragon',
    'Not Young At All Dragon',
    'Nereid',
    'Nymph',
    'Old Dragon',
    'Skeleton',
    'Slime',
    'Sorcerer',
    'Teen Dragon',
    'Unicorn',
    'Wolf',
    'Young Dragon',
    'Zombie',
    'Witch',
    'Scaled Baby Dragon',
    'Scaled Kid Dragon',
    'Scaled Teen Dragon',
    'Scaled Adult Dragon',
    'Scaled Old Dragon',
    'Void Fragment',
    'Void Particle',
    'Void Shard',
    'Abyss Bug',
    'Nothing',
    'Shadow Hands',
    'Corrupted Unicorn',
    'Corrupted Wolf',
    'Corrupted Zombie',
    'Asteroid',
    'Neutron Star',
    'Flying Saucer',
    'Time Alteration',
    'Time Interference',
    'Time Limitation',
)

TRACKED_COMMANDS = (
    'hunt',
    'work',
    'farm',
    'training',
    'adventure',
    'epic guard'
) # Sorted by cooldown length