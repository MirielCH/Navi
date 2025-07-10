# Navi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python: 3.12](https://img.shields.io/badge/Python-3.12-brightgreen.svg)](https://www.python.org/) [![Database: SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://www.sqlite.org/index.html)

Reminder / Helper for EPIC RPG.  

## How to invite Navi

If you don't want to run Navi yourself, you can invite [Navi Lite](https://canary.discord.com/api/oauth2/authorize?client_id=1213487623688167494&permissions=378944&scope=bot). This is a global version hosted by me. To prevent rate limit issues, it has the following limitations:  
• Reactions are permanently disabled.  
• Auto-ready frequency is fixed to `after hunt only`.  

## How to run Navi

• Install python 3.12.  
• Install all third party libraries mentioned in `requirements.txt` (`python3.12 -m pip install -r requirements.txt`).  
• Create a Discord application with a bot user, activate the required intents (see below) and generate a bot token.  
• Rename `database/default_db.db` to `database/navi_db.db`.  
• Upload all emojis in `images/emojis` to private Discord servers. **DO NOT CHANGE THEIR NAMES**.  
• Rename `default.env` to `.env` and set all variables as explained in the file.  
• Run the bot by running `bot.py` (`python3.12 bot.py`).  
• Invite Navi to all your emoji servers and all other servers you want to use it. Note the required permissions below.  
• Run the command `/dev emoji-update` to update the emojis in the code to your uploaded ones.  
• Run the command `/dev emoji-check` to make sure all emojis are present.  

## How to update Navi

• Replace all other `.py` files with the new ones.  
• Upload new emojis (if any) in `images/emojis` to your emoji servers. **DO NOT CHANGE THEIR NAMES**.  
• Run the command `/dev emoji-update` to update the emojis in the code to your uploaded ones.  
• Run the command `/dev emoji-check` to make sure all emojis are present.  
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
• Attach files  

## Commands

Navi uses both slash and text commands. Use `/help` for an overview.  
Default prefix for text commands is `navi ` and is changeable in `/settings server`.  

## Dev commands

These commands provide bot admin level functionality and are restricted as follows:  
• They can only be used by users set in DEV_IDS.
• They are not registered globally and only show up in the servers set in DEV_GUILDS.  
• They are not listed in `/help`.  
**Do not change this behaviour. Some of them would expose data, others would allow users to mess with your Navi.**  

The following commands are available:  

### `/dev cache`, `navi dev cache`  

Shows the size of the local message cache. All user messages containing a mention of epic rpg or starting with "rpg " are cached for 1 minute to speed up command detection.  

### `/dev consolidate`, `navi dev consolidate`  

Manually triggers the tracking consolidation. This runs daily at 00:00 UTC, so you probably won't need this.  

### `/dev emoji-check`, `navi dev emoji-check`  

Checks if alle emojis Navi needs are uploaded and present.  

### `/dev event-reductions`, `navi dev er`  

Manages global event reductions. If there is a global reduction (e.g. 25% on New Year event), you can set this here.  
Always check what is actually affected before changing this, it's never all commands even when lume says otherwise. `guild`, `daily` and `weekly` are almost never included for example.  

### `/dev leave-server`, `navi dev leave-server`  

Makes Navi leave the discord server with the provided ID. You can see server IDs in `/dev server-list`. You don't have to be in a server yourself for this to work.  

### `/dev post-message`, `navi dev pm <message id> <channel id> <embed title>`  

Allows you to send a custom message via Navi to a channel. I use this to post Navi updates.  

### `/dev reload`, `navi dev reload <modules>`  

Allows reloading of cogs and modules on the fly.  
Note that you should always restart the bot when there is a breaking change, no matter what.  

It's not possible to reload the following files:  
• Cogs with slash command definitions. Due to Discord restrictions, you need to restart the whole thing if you change slash commands.  
• The file `bot.py` as this is the main file that is running.  
• The file `tasks.py`. I had mixed results with this, just restart instead.  

To reload files in subfolders, use `folder.file` (e.g. `resources.settings`). Cogs don't need that, the filename is enough (e.g. `adventure`).  

### `/dev server-list`, `navi dev server-list`  

Lists all servers Navi is in by name.  

### `/dev shutdown`, `navi dev shutdown`  

Shuts down the bot. Note that if the bot is registered as a systemctl or systemd service, it will of course automatically restart.  

### `/dev support`, `navi dev support`  

Shows a link to the dev support server (see below).  

Ignore other dev commands, they are my own test commands and might even mess up something for you.  

## Support server

• If you find bugs, have issues running Navi or something else, feel free to join the [support server](https://discord.gg/Kz2Vz2K4gy).  
