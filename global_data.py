# global_data.py

import os

# Get bot directory
bot_dir = os.path.dirname(__file__)

# Databases
dbfile = os.path.join(bot_dir, 'database/navi_db.db')

# Donor tier reductions
donor_cooldowns = (1,0.9,0.8,0.65,)

# Prefix
default_prefix = 'navi '

# Donor tiers
donor_tiers = ['Non-donator','Donator','EPIC donator','SUPER donator','MEGA donator','HYPER donator','ULTRA donator','ULTIMATE donator',]

# All activities
activities = ['all','adventure','daily','hunt','lootbox','lootbox-alert','lottery','pet','quest','training','weekly','work',]

# Bot message timeout
timeout = 10
timeout_longer = 20

# Toggle debug reactions and messages
debug_mode = True

# Default messages
default_message = 'Hey! It\'s time for `%`!'
alert_message = 'Hey! **{user}** found {lootbox} for you!' # Not changeable by user
arena_message = 'Hey! The **big arena** event just finished! You can check the results on the official EPIC RPG server.'
miniboss_message = 'Hey! The **not so "mini" boss** event just finished! You can check the results on the official EPIC RPG server.'
pet_message = 'Hey! Your pet **$** is back!'

# Guild defaults
guild_reset = (5,21,59) # Weekday, hour, minute (UTC, weekday starts from 0)
guild_stealth = 90

# Embed color
color = 0x3abad3

# Set default footer
async def default_footer(prefix):
    footer = f'Hey! Listen!'
    
    return footer

# Error log file
logfile = os.path.join(bot_dir, 'logs/discord.log')