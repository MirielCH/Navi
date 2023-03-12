# Navi Privacy Policy

This policy is effective as of 15 August 2022 and was last updated on 12 March 2023.  

## User information the bot collects

Navi does neither collect nor store any personal user data.  

## Command tracking

When you turn on the bot, Navi starts tracking some of your EPIC RPG commands. The term “tracking” refers to the name of these commands and the time when they were used.  
This information is used to calculate how many commands you used in `/stats`.  
You will get a warning that you enabled this when you use `/on`.

Important things to note:  
• Tracking is only active if you manually activate Navi using `/on` first (opt-in).  
• You can opt-out at any time by turning off tracking in `/settings user`. Disabling this feature does not impact any of the other functions of the bot.  
• If you use `/off`, tracking - like everything else - will be disabled.

## Message content access

Navi has access to the content of all messages it can see. This access is necessary to create reminders.  
Navi reads EPIC RPG messages and also reads the commands you issue to trigger said messages (e.g. if a hunt message is detected, it will also read your `/hunt` slash command or your `rpg hunt` message).  
This data does usually not get stored and is immediately discarded.  

## Storing message data

The bot caches all messages sent by users that either mention the EPIC RPG bot or start with `rpg `. They are used to reduce API calls and increase performance. These messages are discarded after 2 minutes and not stored permanently.  

If there is an error, the following data is stored permanently in the error log:  
• Content of the **EPIC RPG** message that couldn’t get processed correctly (but never messages by **you**).  
• A message link to the **EPIC RPG** message that couldn’t get processed correctly. If the error happened in a private channel, I do not have access to that channel, as the stored message link will **not** work.  

## Limits of this policy

Please be aware that I have no control over the code and policies of forks and other projects that use Navi’s source code and cannot accept responsibility or liability for their respective privacy practices.  

This policy therefore only applies to:  
• The code in the [main repository](https://github.com/Miriel-py/Navi), maintained by myself.  
• The bot instance with the username `Navi#4692`, hosted by myself. This bot instance is only available in RPG Army, Charivari Headquarters and a few private servers which are not accessible to the public. If you encounter Navi on any server not listed here, it is outside of the scope of this privacy policy.  

The bot may also link to external sites that are not operated by me. The same limits apply to those sites.

## Changes to this policy

At my discretion, I may change my privacy policy to reflect updates. If I decide to change this privacy policy, I will post the changes here at the same link by which you are accessing this privacy policy.

## Contact me

For any questions or concerns regarding this policy, you may contact me (Miriel#0001) on Discord directly.
