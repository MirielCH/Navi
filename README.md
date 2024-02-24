# Navi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python: 3.8](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/) [![Database: SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://www.sqlite.org/index.html)

Reminder / Helper for EPIC RPG.  

## Setup

• Install python 3.8 or higher. I recommend the newest version (3.11).  
• Install all third party libraries mentioned in `requirements.txt`.  
• Create a Discord application with a bot user, activate the required intents (see below) and generate a bot token.  
• Rename `default.env` to `.env` and set all required variables mentioned in the file.  
• Rename `database/default_db.db` to `database/navi_db.db`.  
• Upload all emojis in `images/emojis` to private servers.  
• Change all emojis in `resources/emojis.py` to the ones you uploaded.  
• Run `bot.py`.  
• Invite Navi to all your emoji servers and all other servers you want to use it. Note the required permissions below.  

## Updating the bot

• Merge your old `resources/emojis.py` with the new one, so you have the new code but keep your own emoji IDs.  
• Replace all other `.py` files with the new ones.  
• Upload new emojis (if any) and change their ID in `resources/emojis.py`.  
• Restart the bot.  

## Required intents

• guilds  
• members  
• message_content  
• messages  

## Required permissions

• Send Messages  
• Embed Links  
• Add Reactions  
• Use External Emoji  
• Read Message History  

## Commands

Navi uses slash commands but also supports some text commands.  
Default prefix for text commands is `navi ` and is changeable in `/settings server`.  
Use `/help` for an overview.  

## Dev commands

These commands provide bot admin level functionality and are restricted as follows:  
• They can only be used by users set in DEV_IDS.
• They are not registered globally and only show up in the servers set in DEV_GUILDS.  
• They are not listed in `/help`.  
**Do not change this behaviour. Some of them would expose data, others would allow users to mess with your Navi.**  


The following commands are available:  

### `/dev cache`  

Shows the size of the local message cache. All user messages containing a mention of epic rpg or starting with "rpg " are cached for 1 minute to speed up command detection.  

### `/dev consolidate`  

Manually triggers the tracking consolidation. This runs daily at 00:00 UTC, so you probably won't need this.  

### `/dev event-reductions`  

Manages global event reductions. If there is a global reduction (e.g. 25% on New Year event), you can set this here.  
Always check what is actually affected before changing this, it's never all commands even when lume says otherwise. `guild`, `daily` and `weekly` are almost never included for example.  

### `/dev leave-server`  

Makes Navi leave the discord server with the provided ID. You can see server IDs in `/dev server-list`. You don't have to be in a server yourself for this to work.  
### `/dev post-message`  

Allows you to send a custom message via Navi to a channel. I use this to post Navi updates.  

### `/dev reload`  

Allows reloading of cogs and modules on the fly.  
Note that you should always restart the bot when there is a breaking change, no matter what.  

It's not possible to reload the following files:  
• Cogs with slash command definitions. Due to Discord restrictions, you need to restart the whole thing if you change slash commands.  
• The file `bot.py` as this is the main file that is running.  
• The file `tasks.py`. I had mixed results with this, just restart instead.  

To reload files in subfolders, use `folder.file` (e.g. `resources.settings`). Cogs don't need that, the filename is enough (e.g. `adventure`).  

### `/dev server-list`  

Lists all servers Navi is in by name.  

### `/dev shutdown`  

Shuts down the bot. Note that if the bot is registered as a systemctl or systemd service, it will of course automatically restart.  

### `/dev support`  

Shows a link to the dev support server (see below).  

Ignore other dev commands, they are my own test commands and might even mess up something for you.  

## Dev support server

• If you find bugs, have issues running Navi or something else, feel free to join the [dev support server](https://discord.gg/Kz2Vz2K4gy).  
