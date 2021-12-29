# bot.py

from resources import settings, system


bot = system.bot

EXTENSIONS = [
    'cogs.adventure',
    'cogs.arena',
    'cogs.buy',
    'cogs.cooldowns',
    'cogs.custom-reminders',
    'cogs.daily',
    'cogs.duel',
    'cogs.dungeon-miniboss',
    'cogs.events',
    'cogs.farm',
    'cogs.clan',
    'cogs.horse',
    'cogs.hunt',
    'cogs.inventory',
    'cogs.lottery',
    'cogs.nsmb-bigarena',
    'cogs.open',
    'cogs.pets',
    'cogs.quest',
    'cogs.sleepypotion',
    'cogs.trade',
    'cogs.training',
    'cogs.weekly',
    'cogs.work',
    'cogs.dev',
    'cogs.main',
    'cogs.settings_user',
    'cogs.settings_guild',
    'cogs.settings_partner',
    'cogs.settings_clan',
    'cogs.fun'
]

if __name__ == '__main__':
    for extension in EXTENSIONS:
        bot.load_extension(extension)


bot.run(settings.TOKEN)