# global_data.py

import os
import logging
import logging.handlers
from dotenv import load_dotenv

# Get bot directory
bot_dir = os.path.dirname(__file__)

# EPIC RPG user ID
epic_rpg_id = 555955826880413696

# Create task dictionary
running_tasks = {}

# Databases
dbfile = os.path.join(bot_dir, 'database/navi_db.db')

# Donor tier reductions
donor_cooldowns = (1,0.9,0.8,0.65,)

# Prefix
default_prefix = 'navi '

# Donor tiers
donor_tiers = ['Non-donator','Donator','EPIC donator','SUPER donator','MEGA donator','HYPER donator','ULTRA donator','ULTIMATE donator',]

# All activities
activities = ['all','adventure','arena','bigarena','daily','duel','dungmb','farm','horse','hunt','lootbox','lootbox-alert','lottery','nsmb','pet','quest','race','training','vote','weekly','work',]

# All activities (cooldowns)
cooldown_activities = ['adventure','arena','daily','farm','guild','hunt','lootbox','miniboss','quest','training','weekly','work',]

# Bot message timeout
timeout = 20
timeout_longer = 30
timeout_longest = 40

# Read the bot token and debug setting from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG_MODE = os.getenv('DEBUG_MODE')

# Default messages
default_message = 'Hey! It\'s time for `%`!'
default_custom_message = 'Hey! This is your reminder for **%**!'
alert_message = 'Hey! **{user}** found {lootbox} for you!' # Not changeable by user
arena_message = 'Hey! The **big arena** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'
miniboss_message = 'Hey! The **not so "mini" boss** event just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'
pet_message = 'Hey! Your pet **$** is back!'
race_message = 'Hey! The **horse race** just finished! You can check the results in <#604410216385085485> on the official EPIC RPG server.'

# Guild defaults
guild_reset = (5,21,59) # Weekday, hour, minute (UTC, weekday starts from 0)
guild_stealth = 90

# Embed color
color = 0x3abad3

# Set default footer
async def default_footer(prefix):
    footer = f'Hey! Listen!'
    return footer

# Open error log file, create if it not exists
logfile = os.path.join(bot_dir, 'logs/discord.log')
if not os.path.isfile(logfile):
    open(logfile, 'a').close()

# Initialize logging
logger = logging.getLogger('discord')
if DEBUG_MODE == 'ON':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(filename=logfile,when='D',interval=1, encoding='utf-8', utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)