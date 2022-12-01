[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python: 3.8](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/) [![Database: SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://www.sqlite.org/index.html)
# Navi

Reminder / Helper for EPIC RPG.  

# Setup
• Install python 3.8, 3.9 or 3.10. Note that python 3.11+ is untested. It might run, or it might not.  
• Install the third party libraries mentioned in `requirements.txt`.  
• Create a Discord application with a bot user, activate the required intents and generate a bot token.  
• Rename `default.env` to `.env` and set all required variables mentioned in the file.  
• Rename `database/default_db.db` to `database/navi_db.db`.  
• Upload all emojis in `images/emojis` to a private server Navi can see.  
• Change all emojis in `resources/emojis.py` to the ones you uploaded.  
• Change `DEV_IDS` and `DEV_GUILDS` in `resources/settings.py` to your liking.  
• Run `bot.py`.  
• Invite Navi to your server(s). Note the required permissions below.  

# Updating the bot
• Replace all `.py` files.  
• Restart the bot.  
• If the bot requires database changes, it will not start and tell you so. In that case, turn off the bot, BACKUP YOUR DATABASE and run `database/update_database.py`.  

# Required intents
• guilds  
• members  
• message_content  
• messages  

# Required permissions
• Send Messages  
• Embed Links  
• Add Reactions  
• Use External Emoji  
• Read Message History  

# Commands
• Navi uses slash commands but also supports some legacy commands.  
• Default prefix for legacy commands is `navi ` and is changeable in `/settings server`.  
• Use `/help` for an overview.  

# Dev commands
 • The dev commands are not listed in `/help`.  
 • These can be used to set event reductions, change default cooldowns, reload code, shutdown the bot, etc.  
 • Dev commands are not registered globally and only show up in the servers set in DEV_GUILDS (see `Setup` part).  

# Dev support server
• If you find bugs, have issues running Navi or something else, feel free to join the dev support server: https://discord.gg/Kz2Vz2K4gy  
