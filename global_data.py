# global_data.py

import os

# Get bot directory
bot_dir = os.path.dirname(__file__)

# Databases
dbfile = os.path.join(bot_dir, 'database/navi_db.db')

# Donor tier reductions
donor_cooldowns = (1,0.9,0.8,0.65,)

# Default message
default_message = 'Hey! It\'s time for %!'

# Prefix
default_prefix = 'navi '

# Embed color
color = 0x3abad3

# Set default footer
async def default_footer(prefix):
    footer = f'Hey! Listen!'
    
    return footer

# Error log file
logfile = os.path.join(bot_dir, 'logs/discord.log')