# auto_flex.py

from math import floor
import random
import re

import discord
from discord.ext import bridge, commands

from cache import messages
from database import errors, guilds, users
from resources import emojis, exceptions, functions, regex, settings, strings


FLEX_TITLES = {
    'artifacts': strings.FLEX_TITLES_ARTIFACTS,
    'artifacts_bunny_mask': strings.FLEX_TITLES_ARTIFACTS,
    'artifacts_claus_belt': strings.FLEX_TITLES_ARTIFACTS,
    'artifacts_cowboy_boots': strings.FLEX_TITLES_ARTIFACTS,
    'artifacts_shiny_pickaxe': strings.FLEX_TITLES_ARTIFACTS,
    'brew_electronical': strings.FLEX_TITLES_BREW_ELECTRONICAL,
    'card_drop': strings.FLEX_TITLES_CARD_DROP,
    'card_drop_partner': strings.FLEX_TITLES_CARD_DROP_PARTNER,
    'card_golden': strings.FLEX_TITLES_CARD_GOLDEN,
    'card_slots': strings.FLEX_TITLES_CARD_SLOTS,
    'epic_berry': strings.FLEX_TITLES_EPIC_BERRY,
    'epic_berry_partner': strings.FLEX_TITLES_EPIC_BERRY_PARTNER,
    'event_coinflip': strings.FLEX_TITLES_EVENT_COINFLIP,
    'event_enchant': strings.FLEX_TITLES_EVENT_ENCHANT,
    'event_farm': strings.FLEX_TITLES_EVENT_FARM,
    'event_heal': strings.FLEX_TITLES_EVENT_HEAL,
    'event_lb': strings.FLEX_TITLES_EVENT_LB,
    'event_training': strings.FLEX_TITLES_EVENT_TRAINING,
    'forge_cookie': strings.FLEX_TITLES_FORGE_COOKIE,
    'hal_boo': strings.FLEX_TITLES_HAL_BOO,
    'lb_a18': strings.FLEX_TITLES_LB_A18,
    'lb_a18_partner': strings.FLEX_TITLES_LB_A18_PARTNER,
    'lb_edgy_ultra': strings.FLEX_TITLES_EDGY_ULTRA,
    'lb_eternal': strings.FLEX_TITLES_LB_ETERNAL,
    'lb_eternal_partner': strings.FLEX_TITLES_LB_ETERNAL_PARTNER,
    'lb_godly': strings.FLEX_TITLES_LB_GODLY,
    'lb_godly_partner': strings.FLEX_TITLES_LB_GODLY_PARTNER,
    'lb_godly_tt': strings.FLEX_TITLES_GODLY_VOID_TT,
    'lb_void_tt': strings.FLEX_TITLES_GODLY_VOID_TT,
    'lb_eternal_tt': strings.FLEX_TITLES_GODLY_VOID_TT,
    'lb_omega_multiple': strings.FLEX_TITLES_LB_OMEGA_MULTIPLE,
    'lb_omega_no_hardmode': strings.FLEX_TITLES_LB_OMEGA_NOHARDMODE,
    'lb_omega_partner': strings.FLEX_TITLES_LB_OMEGA_PARTNER,
    'lb_omega_ultra': strings.FLEX_TITLES_OMEGA_ULTRA,
    'lb_party_popper': strings.FLEX_TITLES_PARTY_POPPER,
    'lb_void': strings.FLEX_TITLES_LB_VOID,
    'lb_void_partner': strings.FLEX_TITLES_LB_VOID_PARTNER,
    'pets_catch_epic': strings.FLEX_TITLES_PETS_CATCH_EPIC,
    'pets_catch_tt': strings.FLEX_TITLES_PETS_CATCH_TT,
    'pets_claim_capsule': strings.FLEX_TITLES_PETS_CLAIM_CAPSULE,
    'pets_claim_omega': strings.FLEX_TITLES_PETS_CLAIM_OMEGA,
    'pr_ascension': strings.FLEX_TITLES_PR_ASCENSION,
    'time_travel_1': strings.FLEX_TITLES_TIME_TRAVEL_1,
    'time_travel_3': strings.FLEX_TITLES_TIME_TRAVEL_3,
    'time_travel_5': strings.FLEX_TITLES_TIME_TRAVEL_5,
    'time_travel_10': strings.FLEX_TITLES_TIME_TRAVEL_10,
    'time_travel_25': strings.FLEX_TITLES_TIME_TRAVEL_25,
    'time_travel_50': strings.FLEX_TITLES_TIME_TRAVEL_50,
    'time_travel_100': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_150': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_200': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_300': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_400': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_420': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_500': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_600': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_700': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_800': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_900': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_999': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1100': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1200': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1300': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1400': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1500': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1600': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1700': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1800': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1900': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_2000': strings.FLEX_TITLES_TIME_TRAVEL_100_PLUS,
    'time_travel_1000000': strings.FLEX_TITLES_TIME_TRAVEL_1000000,
    'work_epicberry': strings.FLEX_TITLES_WORK_EPICBERRY,
    'work_hyperlog': strings.FLEX_TITLES_WORK_HYPERLOG,
    'work_ultimatelog': strings.FLEX_TITLES_WORK_ULTIMATELOG,
    'work_ultralog': strings.FLEX_TITLES_WORK_ULTRALOG,
    'work_superfish': strings.FLEX_TITLES_WORK_SUPERFISH,
    'work_watermelon': strings.FLEX_TITLES_WORK_WATERMELON,
    'xmas_chimney': strings.FLEX_TITLES_XMAS_CHIMNEY,
    'xmas_eternal': strings.FLEX_TITLES_XMAS_ETERNAL,
    'xmas_godly': strings.FLEX_TITLES_XMAS_GODLY,
    'xmas_snowball': strings.FLEX_TITLES_XMAS_SNOWBALL,
    'xmas_void': strings.FLEX_TITLES_XMAS_VOID,
}

FLEX_THUMBNAILS = {
    'artifacts': strings.FLEX_THUMBNAILS_ARTIFACTS,
    'artifacts_bunny_mask': strings.FLEX_THUMBNAILS_ARTIFACTS_BUNNY_MASK,
    'artifacts_claus_belt': strings.FLEX_THUMBNAILS_ARTIFACTS_CLAUS_BELT,
    'artifacts_cowboy_boots': strings.FLEX_THUMBNAILS_ARTIFACTS_COWBOY_BOOTS,
    'artifacts_shiny_pickaxe': strings.FLEX_THUMBNAILS_ARTIFACTS_SHINY_PICKAXE,
    'brew_electronical': strings.FLEX_THUMBNAILS_BREW_ELECTRONICAL,
    'card_drop': strings.FLEX_THUMBNAILS_CARD_DROP,
    'card_drop_partner': strings.FLEX_THUMBNAILS_CARD_DROP_PARTNER,
    'card_golden': strings.FLEX_THUMBNAILS_CARD_GOLDEN,
    'card_slots': strings.FLEX_THUMBNAILS_CARD_SLOTS,
    'epic_berry': strings.FLEX_THUMBNAILS_EPIC_BERRY,
    'epic_berry_partner': strings.FLEX_THUMBNAILS_EPIC_BERRY_PARTNER,
    'event_coinflip': strings.FLEX_THUMBNAILS_EVENT_COINFLIP,
    'event_enchant': strings.FLEX_THUMBNAILS_EVENT_ENCHANT,
    'event_farm': strings.FLEX_THUMBNAILS_EVENT_FARM,
    'event_heal': strings.FLEX_THUMBNAILS_EVENT_HEAL,
    'event_lb': strings.FLEX_THUMBNAILS_EVENT_LB,
    'event_training': strings.FLEX_THUMBNAILS_EVENT_TRAINING,
    'forge_cookie': strings.FLEX_THUMBNAILS_FORGE_COOKIE,
    'hal_boo': strings.FLEX_THUMBNAILS_HAL_BOO,
    'lb_a18': strings.FLEX_THUMBNAILS_LB_A18,
    'lb_a18_partner': strings.FLEX_THUMBNAILS_LB_A18_PARTNER,
    'lb_edgy_ultra': strings.FLEX_THUMBNAILS_EDGY_ULTRA,
    'lb_eternal': strings.FLEX_THUMBNAILS_LB_ETERNAL,
    'lb_eternal_partner': strings.FLEX_THUMBNAILS_LB_ETERNAL_PARTNER,
    'lb_godly': strings.FLEX_THUMBNAILS_LB_GODLY,
    'lb_godly_partner': strings.FLEX_THUMBNAILS_LB_GODLY_PARTNER,
    'lb_godly_tt': strings.FLEX_THUMBNAILS_GODLY_VOID_TT,
    'lb_void_tt': strings.FLEX_THUMBNAILS_GODLY_VOID_TT,
    'lb_eternal_tt': strings.FLEX_THUMBNAILS_GODLY_VOID_TT,
    'lb_omega_multiple': strings.FLEX_THUMBNAILS_LB_OMEGA_MULTIPLE,
    'lb_omega_no_hardmode': strings.FLEX_THUMBNAILS_LB_OMEGA_NOHARDMODE,
    'lb_omega_partner': strings.FLEX_THUMBNAILS_LB_OMEGA_PARTNER,
    'lb_omega_ultra': strings.FLEX_THUMBNAILS_OMEGA_ULTRA,
    'lb_party_popper': strings.FLEX_THUMBNAILS_PARTY_POPPER,
    'lb_void': strings.FLEX_THUMBNAILS_LB_VOID,
    'lb_void_partner': strings.FLEX_THUMBNAILS_LB_VOID_PARTNER,
    'pets_catch_epic': strings.FLEX_THUMBNAILS_PETS_CATCH_EPIC,
    'pets_catch_tt': strings.FLEX_THUMBNAILS_PETS_CATCH_TT,
    'pets_claim_capsule': strings.FLEX_THUMBNAILS_PETS_CLAIM_CAPSULE,
    'pets_claim_omega': strings.FLEX_THUMBNAILS_PETS_CLAIM_OMEGA,
    'pr_ascension': strings.FLEX_THUMBNAILS_PR_ASCENSION,
    'time_travel_1': strings.FLEX_THUMBNAILS_TIME_TRAVEL_1,
    'time_travel_3': strings.FLEX_THUMBNAILS_TIME_TRAVEL_3,
    'time_travel_5': strings.FLEX_THUMBNAILS_TIME_TRAVEL_5,
    'time_travel_10': strings.FLEX_THUMBNAILS_TIME_TRAVEL_10,
    'time_travel_25': strings.FLEX_THUMBNAILS_TIME_TRAVEL_25,
    'time_travel_50': strings.FLEX_THUMBNAILS_TIME_TRAVEL_50,
    'time_travel_100': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_150': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_200': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_300': strings.FLEX_THUMBNAILS_TIME_TRAVEL_300,
    'time_travel_400': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_420': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_500': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_600': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_700': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_800': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_900': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_999': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1100': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1200': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1300': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1400': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1500': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1600': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1700': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1800': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1900': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_2000': strings.FLEX_THUMBNAILS_TIME_TRAVEL_100_PLUS,
    'time_travel_1000000': strings.FLEX_THUMBNAILS_TIME_TRAVEL_1000000,
    'work_epicberry': strings.FLEX_THUMBNAILS_WORK_EPICBERRY,
    'work_hyperlog': strings.FLEX_THUMBNAILS_WORK_HYPERLOG,
    'work_ultimatelog': strings.FLEX_THUMBNAILS_WORK_ULTIMATELOG,
    'work_ultralog': strings.FLEX_THUMBNAILS_WORK_ULTRALOG,
    'work_superfish': strings.FLEX_THUMBNAILS_WORK_SUPERFISH,
    'work_watermelon': strings.FLEX_THUMBNAILS_WORK_WATERMELON,
    'xmas_chimney': strings.FLEX_THUMBNAILS_XMAS_CHIMNEY,
    'xmas_eternal': strings.FLEX_THUMBNAILS_XMAS_ETERNAL,
    'xmas_godly': strings.FLEX_THUMBNAILS_XMAS_GODLY,
    'xmas_snowball': strings.FLEX_THUMBNAILS_XMAS_SNOWBALL,
    'xmas_void': strings.FLEX_THUMBNAILS_XMAS_VOID,
}

# Auto flexes that have a column name that differs from the event name
FLEX_COLUMNS = {
    'artifacts_bunny_mask': 'artifacts',
    'artifacts_claus_belt': 'artifacts',
    'artifacts_cowboy_boots': 'artifacts',
    'artifacts_shiny_pickaxe': 'artifacts',
    'card_drop_partner': 'card_drop',
    'epic_berry_partner': 'epic_berry',
    'lb_a18_partner': 'lb_a18',
    'lb_eternal_partner': 'lb_eternal',
    'lb_eternal_tt': 'lb_godly_tt',
    'lb_godly_partner': 'lb_godly',
    'lb_omega_multiple': 'lb_omega',
    'lb_omega_no_hardmode': 'lb_omega',
    'lb_omega_partner': 'lb_omega',
    'lb_void_partner': 'lb_void',
    'lb_void_tt': 'lb_godly_tt',
    'pets_claim_capsule': 'pets_claim_omega',
    'time_travel_1': 'time_travel',
    'time_travel_3': 'time_travel',
    'time_travel_5': 'time_travel',
    'time_travel_10': 'time_travel',
    'time_travel_25': 'time_travel',
    'time_travel_50': 'time_travel',
    'time_travel_100': 'time_travel',
    'time_travel_150': 'time_travel',
    'time_travel_200': 'time_travel',
    'time_travel_300': 'time_travel',
    'time_travel_400': 'time_travel',
    'time_travel_420': 'time_travel',
    'time_travel_500': 'time_travel',
    'time_travel_600': 'time_travel',
    'time_travel_700': 'time_travel',
    'time_travel_800': 'time_travel',
    'time_travel_900': 'time_travel',
    'time_travel_999': 'time_travel',
    'time_travel_1100': 'time_travel',
    'time_travel_1200': 'time_travel',
    'time_travel_1300': 'time_travel',
    'time_travel_1400': 'time_travel',
    'time_travel_1500': 'time_travel',
    'time_travel_1600': 'time_travel',
    'time_travel_1700': 'time_travel',
    'time_travel_1800': 'time_travel',
    'time_travel_1900': 'time_travel',
    'time_travel_2000': 'time_travel',
    'time_travel_1000000': 'time_travel',
}

TIME_TRAVEL_DESCRIPTIONS = {
    'time_travel_1': (
            f'**{{user_name}}** just reached their very **first** {emojis.TIME_TRAVEL} **time travel**!\n'
            f'Congratulations, we are expecting great things of you!'
        ),
    'time_travel_3': (
            f'**{{user_name}}** did it again (and again) and just reached {emojis.TIME_TRAVEL} **TT 3**!\n'
            f'I think they\'re getting addicted.'
        ),
    'time_travel_5': (
            f'**{{user_name}}** is getting serious. {emojis.TIME_TRAVEL} **TT 10** achieved!\n'
            f'Hope you\'re not colorblind. Also I hope you don\'t expect to survive in A15.'
        ),
    'time_travel_10': (
            f'**{{user_name}}** is getting serious. {emojis.TIME_TRAVEL} **TT 10** achieved!\n'
            f'Hope you\'re not colorblind. Also I hope you don\'t expect to survive in A15.'
        ),
    'time_travel_25': (
            f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **TT 25**!\n'
            f'Good news: Welcome to the endgame!\n'
            f'Bad news: Hope you like dragon scale farming.'
        ),
    'time_travel_50': (
            f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **TT 50**!\n'
            f'Sadly they went blind after seeing the profile background they got as a reward.'
        ),
    'time_travel_100': (
            f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **TT 100**!\n'
            f'Damn, you must really like this game. I just hope you still remember your family.\n'
            f'Nothing more I can teach you anyway. Wdym I never taught you anything? Ungrateful brat.'
        ),
    'time_travel_150': (
            f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **TT 150**!\n'
            f'I\'m starting to question your life choices.\n'
            f'You can stop playing now btw, there will be no more backgrounds.\n'
        ),
    'time_travel_200': (
            f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **TT 200**!\n'
            f'What on earth made you do this 200 times? You mad?\n'
        ),
    'time_travel_300': f'**{{user_name}}** reached {emojis.TIME_TRAVEL} **SPARTA**!\n',
    'time_travel_400': (
            f'Public Service Alert! **{{user_name}}** traveled in time **400** times {emojis.TIME_TRAVEL}!\n'
            f'As to why tho... I couldn\'t say.'
        ),
    'time_travel_420': f'**4:20 {{user_name}}**. The usual place.',
    'time_travel_500': (
            f'Did you see that? It\'s **{{user_name}}** plopping through time. For the freaking **500**th time.\n'
            f'{emojis.TIME_TRAVEL}\n'
        ),
    'time_travel_600': (
            f'Pretty sury **{{user_name}}** forgot by now which time they actually belong to after '
            f'**600** {emojis.TIME_TRAVEL} time travels.\n'
        ),
    'time_travel_700': (
            f'Did you know that there is such a thing as playing a game too much? **{{user_name}}** can.\n'
            f'They just reached **700** {emojis.TIME_TRAVEL} time travels, and it scares me.\n'
        ),
    'time_travel_800': (
            f'**800** {emojis.TIME_TRAVEL} time travels. It\'s rather crazy. But I get it now - '
            f'**{{user_name}}** is probably training for the time olympics on Galifrey.'
        ),
    'time_travel_900': (
            f'Ted just called **{{user_name}}** and wanted his phone booth back. After learning it was '
            f'used for **900** {emojis.TIME_TRAVEL} time travels, he was too scared to take it back tho.'
        ),
    'time_travel_999': (
            f'**{{user_name}}** traveled in time **999** times and thus broke Epic RPG Guide. Good job.\n'
            f'Hope you\'re proud. Damn it.'
        ),
    'time_travel_1100': (
            f'**{{user_name}}** needs therapy. I mean... they time traveled **1,100** times.'
        ),
    'time_travel_1200': f'**{{user_name}}** time traveled **1,200** times which makes them rather smol if you ask me.',
    'time_travel_1300': (
            f'**{{user_name}}** is increasing their time travel count to **1,300**.\n'
            f'Now, some people would call a doctor at this point. Maybe even **the** doctor.'
        ),
    'time_travel_1400': (
            f'La laaa laaaah, dee daaaahh, running out of ideas, shoo beee dooo...\n'
            f'What happened, you ask? Well, **{{user_name}}** reached TT **1,400**. The usual.'
        ),
    'time_travel_1500': (
            f'One thousand five hundred time travels.\n'
            f'**{{user_name}}** seems to quite mad.'
        ),
    'time_travel_1600': (
            f'Ah. Time. A beautiful concept. Some even travel through it.\n'
            f'And then there\'s **{{user_name}}**, doing it freaking **1,600** times.'
        ),
    'time_travel_1700': (
            f'Did you hear that? I think some fuse blew.\n'
            f'Ah yes. Must be **{{user_name}}**\'s time machine, it finally broke after **1,700** time travels.'
        ),
    'time_travel_1800': (
            f'Let me introduce you to **{{user_name}}**, the person who time traveled **1,800** times.\n'
            f'I\'m afraid they got quite a few screws loose.'
        ),
    'time_travel_1900': (
            f'If you see this, then someone triggered it. **{{user_name}}**, to be exact.\n'
            f'The problem is, it requires **1,900** time travels to trigger this.\n'
            f'Make of that what you will.'
        ),
    'time_travel_2000': (
            f'Once upon a time, **{{user_name}}** found a game called EPIC RPG.\n'
            f'It was quite a nice little game, so they decided to play a bit, maybe even TT once or thrice.\n'
            f'They happened to like it, so they kept going a bit longer.\n'
            f'They kept going.\n'
            f'And going.\n'
            f'They grew older.\n'
            f'Still going.\n'
            f'Jesus, why don\'t they stop.\n'
            f'Call an ambulance.\n'
            f'Is this normal?\n'
            f'SOMEONE HELP THEM.\n'
            f'Oh lord.\n'
            f'STILL GOING.\n'
            f'Oh god. They reached **2,000** time travels.\n'
            f'Stawp.'
    ),
    'time_travel_1000000': (
            f'In pixel\'d dusk and neon dawn,\n'
            f'Through areas past and futures gone,\n'
            f'**{{user_name}}** rewrote the threads of fate—\n'
            f'A **million times**, reset the slate.\n\n'
            f'With ruby sword and golden pan,\n'
            f'They fought beneath a fractured sun.\n'
            f'Each timeline twisted, torn, betrayed,\n'
            f'Yet on they marched, undismayed.\n\n'
            f'The endgame bunch now knows their name,\n'
            f'In every guild, it\'s carved in flame.\n'
            f'From scrawny wolf to EPIC mob,\n'
            f'They danced through eternity and the top.\n\n'
            f'The King of Void, Eternal Lord,\n'
            f'With every jump, a fate restored.\n'
            f'They ate the cookies, drank the milk,\n'
            f'Killed their own self — smooth as silk.\n\n'
            f'The NPC just shakes his head,\n'
            f'"Didn\'t I kill you twice?" he said.\n'
            f'But bug or God, who really knows?\n'
            f'Time bends for those who choose their prose.\n\n'
            f'So raise your flask in fractured time,\n'
            f'To looping tales and lore sublime.\n'
            f'For not all heroes age or fall—\n'
            f'Some just time jump and know it all.'
    ),
}


class AutoFlexCog(commands.Cog):
    """Cog that contains the auto flex detection"""
    def __init__(self, bot: bridge.AutoShardedBot):
        self.bot = bot

    async def send_auto_flex_message(self, message: discord.Message, guild_settings: guilds.Guild,
                                     user_settings: users.User, user: discord.User, event: str,
                                     description: str) -> None:
        """Sends a flex embed to the auto flex channel"""
        event_column = FLEX_COLUMNS[event] if event in FLEX_COLUMNS else event
        auto_flex_setting = getattr(guild_settings, f'auto_flex_{event_column}_enabled', None)
        if auto_flex_setting is None:
            await functions.add_warning_reaction(message)
            await errors.log_error(f'Couldn\'t find auto flex setting for event "{event}"', message)
            return
        if not auto_flex_setting: return
        description = f'{description}\n\n[Check it out]({message.jump_url})'
        embed = discord.Embed(
            color = settings.EMBED_COLOR,
            title = random.choice(FLEX_TITLES[event]),
            description = description,
        )
        if 'ascension' in event:
            author = f'{user.name} is advancing!'
        elif 'chimney' in event:
            author = f'{user.name} got stuck!'
        elif 'time_travel' in event:
            author = f'{user.name} is traveling in time!'
        elif 'a18_partner' in event:
            author = f'{user.name} is being mean!'
        elif 'a18' in event:
            author = f'{user.name} is losing their stuff!'
        elif 'partner' in event:
            author = f'{user.name} got robbed!'
        else:
            author = f'{user.name} got lucky!'
        embed.set_author(icon_url=user.display_avatar.url, name=author)
        embed.set_thumbnail(url=random.choice(FLEX_THUMBNAILS[event]))
        embed.set_footer(text='Use \'/settings user\' to enable or disable auto flex.')
        content = None
        if user_settings.auto_flex_ping_enabled:
            content = f'<@{user_settings.user_id}>'
        auto_flex_channel = await functions.get_discord_channel(self.bot, guild_settings.auto_flex_channel_id)
        if auto_flex_channel is None:
            await functions.add_warning_reaction(message)
            await errors.log_error('Couldn\'t find auto flex channel.', message)
            return
        await auto_flex_channel.send(content=content, embed=embed)
        if user_settings.reactions_enabled: await message.add_reaction(emojis.PANDA_LUCKY)
        if not user_settings.auto_flex_tip_read:
            await message.channel.send(
                f'{user.mention} Nice! You just did something flex worthy. Because you have auto flex enabled, '
                f'this was automatically posted to the channel <#{guild_settings.auto_flex_channel_id}>.\n'
                f'If you don\'t like this, you can disable auto flex and/or auto flex pings in '
                f'{await functions.get_navi_slash_command(self.bot, "settings user")}.'
            )
            await user_settings.update(auto_flex_tip_read=True)

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message) -> None:
        """Runs when a message is edited in a channel."""
        if message_before.pinned != message_after.pinned: return
        allow_disabled_components = False
        embed_data_before = await functions.parse_embed(message_before)
        embed_data_after = await functions.parse_embed(message_after)
        if (message_before.content == message_after.content and embed_data_before == embed_data_after
            and message_before.components == message_after.components): return
        """
        if message_after.embeds:
            if message_after.embeds[0].author is not None:
                if 'card hand' in message_after.embeds[0].author.name.lower():
                    allow_disabled_components = True
        """
        if not allow_disabled_components:
            row: discord.Component
            for row in message_after.components:
                if isinstance(row, discord.ActionRow):
                    for component in row.children:
                        if isinstance(component, (discord.Button, discord.SelectMenu)):
                            if component.disabled:
                                return
        await self.on_message(message_after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Runs when a message is sent in a channel."""
        if message.author.id not in [settings.EPIC_RPG_ID, settings.TESTY_ID]: return
        if message.embeds:
            embed: discord.Embed = message.embeds[0]
            embed_description = embed_title = embed_field0_name = embed_field0_value = embed_autor = icon_url = ''
            embed_field1_value = embed_field1_name = embed_fields = ''
            if embed.description is not None: embed_description = embed.description
            if embed.title is not None: embed_title = embed.title
            if embed.fields:
                for field in embed.fields:
                    embed_fields = f'{embed_fields}\n{field.value}'
                embed_field0_name = embed.fields[0].name
                embed_field0_value = embed.fields[0].value
            if len(embed.fields) > 1:
                embed_field1_name = embed.fields[1].name
                embed_field1_value = embed.fields[1].value
            if embed.author is not None:
                embed_autor = embed.author.name
                icon_url = embed.author.icon_url

            # Rare loot from lootboxes
            search_strings = [
                "— lootbox", #All languages
            ]
            if any(search_string in embed_autor.lower() for search_string in search_strings):
                if 'edgy lootbox' in embed_field0_name.lower() and '<:ultralog' in embed_field0_value.lower():
                    event = 'lb_edgy_ultra'
                elif 'omega lootbox' in embed_field0_name.lower() and '<:ultralog' in embed_field0_value.lower():
                    event = 'lb_omega_ultra'
                elif 'godly lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_godly_tt'
                elif 'void lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_void_tt'
                elif 'eternal lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_eternal_tt'
                elif 'void lootbox' in embed_field0_name.lower() and '<:timecapsule' in embed_field0_value.lower():
                    event = 'lb_void_tt'
                elif '<:partypopper' in embed_field0_value.lower():
                    event = 'lb_party_popper'
                else:
                    return
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_OPEN, user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex lootbox message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if event == 'lb_edgy_ultra':
                    match = re.search(r'\+(.+?) (.+?) ultra log', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('ULTRA log amount not found in auto flex edgy lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Look at **{user.name}**, opening that {emojis.LB_EDGY} EDGY lootbox like it\'s worth '
                        f'anything, haha.\n'
                        f'See, all they got is **{amount}** lousy **{emojis.LOG_ULTRA} ULTRA log**!\n\n'
                        f'_**Wait...**_'
                    )
                elif event == 'lb_omega_ultra':
                    match = re.search(r'\+(.+?) (.+?) ultra log', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('ULTRA log amount not found in auto flex omega lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Never get ULTRAs out of {emojis.LB_OMEGA} **OMEGA lootboxes**?\n'
                        f'**{user.name}** can teach you how it works. They just hacked **{amount}** {emojis.LOG_ULTRA} '
                        f'**ULTRA logs** out of theirs.'
                    )
                elif event == 'lb_godly_tt':
                    match = re.search(r'\+(.+?) (.+?) time capsule', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time capsule amount not found in auto flex godly lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'So.\n**{user.name}** opened a {emojis.LB_GODLY} GODLY lootbox. I mean that\'s cool.\n'
                        f'__BUT__. For some reason they found **{amount}** {emojis.TIME_CAPSULE} **time capsule** in there.\n'
                        f'This hasn\'t happened often yet, so expect to get blacklisted from the game.'
                    )
                elif event == 'lb_void_tt':
                    match = re.search(r'\+(.+?) (.+?) time capsule', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time capsule amount not found in auto flex void lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'**{user.name}** decided to not contribue their {emojis.LB_VOID} VOID lootbox and open it.\n'
                        f'They should be ashamed.\n'
                        f'Okay, they probably are not, because they got **{amount}** {emojis.TIME_CAPSULE} **time capsule** as a reward for their deceit.'
                    )
                elif event == 'lb_eternal_tt':
                    match = re.search(r'\+(.+?) (.+?) time capsule', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Time capsule amount not found in auto flex eternal lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'Others would be happy with even finding one, but **{user.name}** decided to take it a notch higher '
                        f'and get **{amount}** bloody {emojis.TIME_CAPSULE} **time capsule** from their {emojis.LB_ETERNAL} ETERNAL lootbox.\n'
                        f'Time to call the EPIC guard.'
                    )
                elif event == 'lb_party_popper':
                    match = re.search(r'\+(.+?) (.+?) party popper', embed_field0_value.lower())
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Party popper amount not found in auto flex godly lootbox message.', message)
                        return
                    amount = match.group(1)
                    description = (
                        f'**{user.name}** opened a lootbox and found **{amount}**, uh... {emojis.PARTY_POPPER} **party popper**?\n'
                        f'I\'m not exactly sure what this is doing in a lootbox, but I hear it\'s rare, so GG I guess?'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Ascension
            search_strings = [
                "unlocked the ascended skill", #English
            ]
            if any(search_string in embed_field0_name.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\*', embed_field0_name)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_PROFESSIONS_ASCEND,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in auto flex ascension message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** just **ascended**.\n\n'
                    f'Yep, just like that! Congratulations!!\n\n'
                    f'Too bad the `ascended` command is gone, it was so much fun...'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'pr_ascension', description)

            # Pets catch
            search_strings = [
                "**dog** is now following", #English, dog
                "**cat** is now following", #English, cat
                "**dragon** is now following", #English, dragon
            ]
            if (any(search_string in embed_field0_value.lower() for search_string in search_strings)
                and ('epic**' in embed_field0_value.lower() or 'time traveler**' in embed_field0_value.lower())):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(\w+?)\*\* is now following \*\*(.+?)\*\*!', #English
                ]
                pet_data_match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not pet_data_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Pet type or user name not found in auto flex pets catch message.',
                                            message)
                    return
                pet_type = pet_data_match.group(1)
                user_name = pet_data_match.group(2)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found for auto flex pets catch message.',
                                                message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if 'time traveler' in embed_field0_value.lower():
                    event = 'pets_catch_tt'
                    description = (
                        f'**{user.name}** took a stroll when a {emojis.SKILL_TIME_TRAVELER} **time traveler** '
                        f'{pet_type.lower()} popped out of nothingness.\n'
                        f'Wonder if the doctor will come after it?'
                    )
                else:
                    event = 'pets_catch_epic'
                    description = (
                        f'**{user.name}** caught a {pet_type.lower()}.\n'
                        f'What? Not very exciting? HA, but this was an {emojis.SKILL_EPIC} **EPIC** {pet_type.lower()}!\n'
                        f'What do you say now?'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Pet adventure rewards
            search_strings = [
                'pet adventure rewards', #English 1
                'reward summary', #English 2
                'recompensas de pet adventure', #Spanish, Portuguese 1
                'resumen de recompensas', #Spanish 2
                'resumo de recompensas', #Portuguese 2
            ]
            search_strings_items = [
                'omega lootbox',
                'time capsule',
            ]
            if (any(search_string in embed_title.lower() for search_string in search_strings)
                and (
                    any(search_string in embed_fields.lower() for search_string in search_strings_items)
                    or any(search_string in embed_description.lower() for search_string in search_strings_items)
                    )
                ):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user_id = user_name = user_command_message = None
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_PETS_CLAIM)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in autoflex pet claim message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if 'time capsule' in embed_fields.lower():
                    description = (
                        f'**{user.name}** sent a **caternal** through time and space. It got so terribly confused it '
                        f'came back with a {emojis.TIME_CAPSULE} **time capsule** it stole who knows where.'
                    )
                    event = 'pets_claim_capsule'
                else:
                    description = (
                        f'**{user.name}** threatened a poor **snowman** pet with a hair dryer and forced him to bring back '
                        f'an {emojis.LB_OMEGA} **OMEGA lootbox**.\n'
                        f'Calvin would be proud.'
                    )
                    event = 'pets_claim_omega'
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Coinflip event
            search_strings = [
                "where is the coin?", #English
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_COINFLIP,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex coinflip message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                if user_settings.current_area == 19: return
                description = (
                    f'**{user.name}** did some coinflipping and **lost the coin**.\n'
                    f'I mean, how hard can it be, seriously? That\'s just embarassing!'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_coinflip',
                                                  description)

            # Update time travel count from time travel message
            search_strings = [
                "— time travel", #All languages
                "— super time travel", #All languages
                "— time jump", #All languages
            ]
            if any(search_string in embed_autor.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
                                                            user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                search_patterns = [
                    'this will be your time travel #(.+?)\n', #English
                    'esta será sua viagem no tempo #(.+?)$', #Spanish, Portuguese
                ]
                tt_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                if tt_match:
                    time_travel_count = int(tt_match.group(1)) - 1
                if not tt_match:
                    search_strings = [
                        'are you sure you want to **time travel**?', #English
                        'estás seguro que quieres **viajar en el tiempo**?', #Spanish
                        'tem certeza de que deseja **viajar no tempo**?', #Portuguese
                    ]
                    if any(search_string in embed_description.lower() for search_string in search_strings):
                        next_tt = True
                    else:
                        next_tt = False
                    search_patterns = [
                        r'time travels\*\*: (.+?)\n', #English
                        r'extra pet slots\*\*: (.+?)\n', #English
                        r'viajes en el tiempo\*\*: (.+?)\n', #Spanish
                        r'espacio adicional para mascotas\*\*: (.+?)\n', #Spanish
                        r'viagem no tempo\*\*: (.+?)\n', #Portuguese
                        r'espaços extras para pets\*\*: (.+?)\n', #Portuguese
                    ]
                    tt_match = await functions.get_match_from_patterns(search_patterns, embed_description)
                    if tt_match:
                        time_travel_count = int(tt_match.group(1))
                        if next_tt: time_travel_count -= 1
                    else:
                        return
                trade_daily_total = floor(100 * (time_travel_count + 1) ** 1.35)
                await user_settings.update(time_travel_count=time_travel_count, trade_daily_total=trade_daily_total)

            # Time travel
            search_strings = [
                "has traveled in time", #English
                'viajou no tempo', #Spanish
                'tempo de viagem', #Portuguese
            ]
            if any(search_string in embed_description.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\* has', embed_description)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TIME_TRAVEL,
                                                        user_name=user_name)
                        )
                    if not user_name_match or user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User not found in auto flex time travel message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.auto_flex_enabled
                    or user_settings.time_travel_count is None): return
                added_tts = 1
                search_strings = [
                    r'managed to jump out', #English
                    r'managed to jump out', #TODO: Spanish
                    r'managed to jump out', #TODO: Portuguese
                ]
                if any(search_string in embed_description.lower() for search_string in search_strings):
                    added_tts += 1
                extra_tt_match = re.search(r'\+(\d+?) <', embed_description)
                if extra_tt_match: added_tts += int(extra_tt_match.group(1))
                time_travel_count_old = user_settings.time_travel_count
                time_travel_count_new = time_travel_count_old + added_tts
                trade_daily_total = floor(100 * (time_travel_count_new + 1) ** 1.35)
                await user_settings.update(time_travel_count=time_travel_count_new, trade_daily_total=trade_daily_total)
                if time_travel_count_old < 1 and time_travel_count_new >= 1:
                    time_travel_flex_count = 1
                elif time_travel_count_old < 3 and time_travel_count_new >= 3:
                    time_travel_flex_count = 3
                elif time_travel_count_old < 5 and time_travel_count_new >= 5:
                    time_travel_flex_count = 5
                elif time_travel_count_old < 10 and time_travel_count_new >= 10:
                    time_travel_flex_count = 10
                elif time_travel_count_old < 25 and time_travel_count_new >= 25:
                    time_travel_flex_count = 25
                elif time_travel_count_old < 50 and time_travel_count_new >= 50:
                    time_travel_flex_count = 50
                elif time_travel_count_old < 100 and time_travel_count_new >= 100:
                    time_travel_flex_count = 100
                elif time_travel_count_old < 150 and time_travel_count_new >= 150:
                    time_travel_flex_count = 150
                elif time_travel_count_old < 200 and time_travel_count_new >= 200:
                    time_travel_flex_count = 200
                elif time_travel_count_old < 300 and time_travel_count_new >= 300:
                    time_travel_flex_count = 300
                elif time_travel_count_old < 400 and time_travel_count_new >= 400:
                    time_travel_flex_count = 400
                elif time_travel_count_old < 420 and time_travel_count_new >= 420:
                    time_travel_flex_count = 420
                elif time_travel_count_old < 500 and time_travel_count_new >= 500:
                    time_travel_flex_count = 500
                elif time_travel_count_old < 600 and time_travel_count_new >= 600:
                    time_travel_flex_count = 600
                elif time_travel_count_old < 700 and time_travel_count_new >= 700:
                    time_travel_flex_count = 700
                elif time_travel_count_old < 800 and time_travel_count_new >= 800:
                    time_travel_flex_count = 800
                elif time_travel_count_old < 900 and time_travel_count_new >= 900:
                    time_travel_flex_count = 900
                elif time_travel_count_old < 999 and time_travel_count_new >= 999:
                    time_travel_flex_count = 999
                elif time_travel_count_old < 1_100 and time_travel_count_new >= 1_100:
                    time_travel_flex_count = 1_100
                elif time_travel_count_old < 1_200 and time_travel_count_new >= 1_200:
                    time_travel_flex_count = 1_200
                elif time_travel_count_old < 1_300 and time_travel_count_new >= 1_300:
                    time_travel_flex_count = 1_300
                elif time_travel_count_old < 1_400 and time_travel_count_new >= 1_400:
                    time_travel_flex_count = 1_400
                elif time_travel_count_old < 1_500 and time_travel_count_new >= 1_500:
                    time_travel_flex_count = 1_500
                elif time_travel_count_old < 1_600 and time_travel_count_new >= 1_600:
                    time_travel_flex_count = 1_600
                elif time_travel_count_old < 1_700 and time_travel_count_new >= 1_700:
                    time_travel_flex_count = 1_700
                elif time_travel_count_old < 1_800 and time_travel_count_new >= 1_800:
                    time_travel_flex_count = 1_800
                elif time_travel_count_old < 1_900 and time_travel_count_new >= 1_900:
                    time_travel_flex_count = 1_900
                elif time_travel_count_old < 2_000 and time_travel_count_new >= 2_000:
                    time_travel_flex_count = 2_000
                elif time_travel_count_old < 1_000_000 and time_travel_count_new >= 1_000_000:
                    time_travel_flex_count = 1_000_000
                else:
                    return
                event = f'time_travel_{time_travel_flex_count}'
                try:
                    description = TIME_TRAVEL_DESCRIPTIONS[event].replace('{user_name}', user.name)
                except KeyError:
                    return
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Christmas loot, quest and duel embeds
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
                'epic snowball', #All languages, epic snowball
            ]
            if (any(search_string in embed_field0_value.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #English
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\bepic\b \bsnowball\b)', #Spanish/Portuguese
                ]
                item_events = {
                    'godly present': 'xmas_godly',
                    'void present': 'xmas_void',
                    'epic snowball': 'xmas_snowball',
                }
                match = await functions.get_match_from_patterns(search_patterns, embed_field0_value)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                guild_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                if len(guild_users) > 1:
                    await functions.add_warning_reaction(message)
                    await message.channel.send(
                        f'Congratulations **{user_name}**, you found something worthy of an auto flex!\n'
                        f'Sadly I am unable to determine who you are as your username is not unique.\n'
                        f'To resolve this, either change your username (not nickname!) or use slash commands next time.'
                    )
                    return
                if not guild_users: return
                user = guild_users[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} '
                        f'{emojis.PRESENT_VOID} **VOID present**, duh.'
                    )
                elif event == 'xmas_snowball':
                    description = (
                        f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                        f'I sense a snowman in their not-so-distant future.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas presents, ultraining embed
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
            ]
            if (any(search_string in embed_field1_value.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b|\bvoid\b) \bpresent\b', #English godly and void present
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (godly\b|void\b) \bpresent', #Spanish/Portuguese godly and void present
                ]
                item_events = {
                    'godly': 'xmas_godly',
                    'void': 'xmas_void',
                }
                match = await functions.get_match_from_patterns(search_patterns, embed_field1_value)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_ULTRAINING,
                                                        user_name=user_name)
                        )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex christmas present quest/ultr message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} '
                        f'{emojis.PRESENT_VOID} **VOID present**, duh.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # EPIC snowball from snowball fight
            search_strings = [
                'epic snowball', #All languages
            ]
            if (any(search_string in embed_description.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r' \*\*(.+?)\*\* also got (.+?) (.+?) \*\*EPIC snowball\*\*', #English
                ]
                match = await functions.get_match_from_patterns(search_patterns, embed_description)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                if user is None:
                    user_command_message = (
                        await functions.get_message_from_channel_history(
                            message.channel, r'(?:\bsummon\b|\bfight\b|\bsleep\b)',
                            user_name=user_name, no_prefix=True
                        )
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex epic snowball fight message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                    f'I sense a snowman in their not-so-distant future.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'xmas_snowball', description)

            # Cards from card slots
            search_strings = [
                "— card slots", #All languages
            ]
            if (any(search_string in embed_autor.lower() for search_string in search_strings)
                and not 'cardroll' in embed_description.lower()):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_id_match = re.search(regex.USER_ID_FROM_ICON_URL, icon_url)
                    if user_id_match:
                        user_id = int(user_id_match.group(1))
                        user = message.guild.get_member(user_id)
                    if user is None:
                        user_name_match = re.search(regex.USERNAME_FROM_EMBED_AUTHOR, embed_autor)
                        if user_name_match:
                            user_name = user_name_match.group(1)
                            user_command_message = (
                                await messages.find_message(message.channel.id, regex.COMMAND_CARD_SLOTS, user_name=user_name)
                            )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex card slots message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                card_name_match = re.search(r'\*\*(.+?)\*\*', embed_title.lower())
                if not card_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Card not found in auto flex card slots message.', message)
                    return
                card_name = card_name_match.group(1)
                description = (
                    f'**{user.name}** just found a **{card_name.capitalize()}**!\n'
                    f'I didn\'t know slot machines work with cards, but sure, have it your way.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'card_slots', description)

        if not message.embeds:
            message_content = message.content

            # Craft artifacts
            search_strings_1 = [
                '** successfully crafted!', #English
            ]
            search_strings_2 = [
                'see `artifacts`', #English
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings_1)
                and any(search_string in message_content.lower() for search_string in search_strings_2)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_CRAFT_ARTIFACT)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex craft artifact message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                event = 'artifacts'
                artifact_name_match = re.search(r'\*\*(.+?)\*\* ', message_content.lower())
                artifact_name = artifact_name_match.group(1)
                artifact_emoji = strings.ARTIFACTS_EMOJIS.get(artifact_name, '')

                if artifact_name == 'vampire teeth':
                    description = (
                        f'**{user.name}** found, uh... well. Some {artifact_emoji} **{artifact_name}**.\n'
                        f'In 3 parts.\n'
                        f'And then reassembled them.\n'
                        f'... yes.'
                    )
                elif artifact_name == 'claus belt':
                    description = (
                        f'HO HO HOOOOOO... **{user.name}** found... Santa\'s {artifact_emoji} **{artifact_name}**?\n'
                        f'If you fold it in half, it might just about fit you.\n'
                        f'Go eat something.\n'
                        f'Also, thank you for helping our effort to lessen the stuck-in-chimney-spam.'
                    )
                    event = 'artifacts_claus_belt'
                elif artifact_name == 'bunny mask':
                    description = (
                        f'Now what is this then. **{user.name}** found a {artifact_emoji} **{artifact_name}**!\n'
                        f'This looks a little silly, dear, but sure, wear it.\n'
                        f'We won\'t judge.'
                    )
                    event = 'artifacts_bunny_mask'
                elif artifact_name == 'cowboy boots':
                    description = (
                        f'Ew **{user.name}**. Really? Now you\'re crafting old {artifact_emoji} **{artifact_name}**? What\'s next? Old Roman socks?\n'
                        f'Well, you do you.'
                    )
                    event = 'artifacts_cowboy_boots'
                elif artifact_name == 'shiny pickaxe':
                    description = (
                        f'**{user.name}** finally has enough of this game. They crafted a {artifact_emoji} **{artifact_name}** and are now off to play ~~Roblox~~ Minecraft.'
                    )
                    event = 'artifacts_shiny_pickaxe'
                else:
                    description = (
                        f'**{user.name}** found some dusty old parts and crafted a {artifact_emoji} **{artifact_name}** '
                        f'with them!\n'
                        f'That thing looks weird, bro.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Loot from work commands
            search_strings = [
                'this may be the luckiest moment of your life', #English, ultimate logs
                'is this a **dream**????', #English, ultra logs
                'oooooofff!!', #English, super fish
                'wwwooooooaaa!!!1', #English, hyper logs
                '**epic berry**', #English, epic berries
            ]
            search_strings_excluded = [
                'contribu', #All languages, void contributions
                'epic bundle', #All languages, halloween shop
                'epic coins', #All languages, epic shop
            ]
            if len(message_content.split('\n')) > 1:
                if (any(search_string in message_content.lower() for search_string in search_strings)
                    and all(search_string not in message_content.lower() for search_string in search_strings_excluded)
                    or ('nice!' in message_content.lower() and 'watermelon' in message_content.lower())):
                    guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                    if not guild_settings.auto_flex_enabled: return
                    user = await functions.get_interaction_user(message)
                    search_patterns = [
                        r'\?\? \*\*(.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English ULTRA log
                        r'!!1 (.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English HYPER log
                        r' \*\*(.+?)\*\* got (.+?) (.+?) __\*\*(ultimate log)\*\*__', #English ULTIMATE log
                        r'\*\*(.+?)\*\* also got (.+?) (.+?) \*\*(epic berry)\*\*', #English EPIC berry
                        r'\*\*(.+?)\*\* got (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #English SUPER fish, watermelon
                        r'\?\? \*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese ULTRA log
                        r'!!1 (.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese HYPER log
                        r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (?:__)?\*\*(.+?)(?:\n|__|$)', #Spanish/Portuguese ULTIMATE log, SUPER fish, watermelon
                    ]
                    item_events = {
                        'epic berry': 'work_epicberry',
                        'hyper log': 'work_hyperlog',
                        'super fish': 'work_superfish',
                        'ultimate log': 'work_ultimatelog',
                        'ultra log': 'work_ultralog',
                        'watermelon': 'work_watermelon',
                    }
                    match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if not match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find auto flex data in work message.', message)
                        return
                    user_name = match.group(1)
                    item_amount = int(match.group(2).replace(',', ''))
                    item_name = match.group(4).lower().replace('**','').strip()
                    if item_name not in item_events: return
                    event = item_events[item_name]
                    if user is None:
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_WORK,
                                                        user_name=user_name)
                        )
                        if user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('Couldn\'t find user for auto flex work message.', message)
                            return
                        user = user_command_message.author
                    try:
                        user_settings: users.User = await users.get_user(user.id)
                    except exceptions.FirstTimeUserError:
                        return
                    if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                    if event == 'work_ultimatelog':
                        description = (
                            f'**{user_name}** did some really weird timber magic stuff and found **{item_amount:,}** '
                            f'{emojis.LOG_ULTIMATE} **ULTIMATE logs**!\n'
                            f'Not sure this is allowed.'
                        )
                    elif event == 'work_ultralog':
                        description = (
                            f'**{user_name}** just cut down **{item_amount:,}** {emojis.LOG_ULTRA} **ULTRA logs** with '
                            f'three chainsaws.\n'
                            f'One of them in their mouth... uh... okay.'
                        )
                    elif event == 'work_watermelon':
                        description = (
                            f'**{user_name}** got tired of apples and bananas and stole **{item_amount:,}** '
                            f'{emojis.WATERMELON} **watermelons** instead.\n'
                            f'They should be ashamed (and make cocktails).'
                        )
                    elif event == 'work_superfish':
                        description = (
                            f'**{user_name}** went fishing and found **{item_amount:,}** weird purple {emojis.FISH_SUPER} '
                            f'**SUPER fish** in the river.\n'
                            f'Let\'s eat them, imagine wasting those on a VOID armor or something.'
                        )
                    elif event == 'work_hyperlog':
                        description = (
                            f'**{user_name}** took a walk in the park when suddenly a tree fell over and split into '
                            f'**{item_amount:,}** {emojis.LOG_HYPER} **HYPER logs**.'
                        )
                    elif event == 'work_epicberry':
                        description = (
                            f'**{user_name}** is making fruit salad!\n'
                            f'It will consist of bananas, apples and '
                            f'**{item_amount:,}** {emojis.EPIC_BERRY} **EPIC berries** they just randomly found '
                            f'while gathering the rest.\n'
                        )
                    await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas loot, non-embed
            search_strings = [
                'godly present', #All languages, godly present
                'void present', #All languages, void present
                'eternal present', #All languages, eternal present
                'epic snowball', #All languages, void present
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* got (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\beternal\b \bpresent\b|\bepic\b \bsnowball\b)', #English
                    r'\*\*(.+?)\*\*\ went.+?found (.+?) (.+?) \*\*(\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\beternal\b \bpresent\b)\*\*', #English godly and void present, chimney
                    r'\*\*(.+?)\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?) (\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\beternal\b \bpresent\b|\bepic\b \bsnowball\b)', #Spanish/Portuguese
                    r'\*\*(.+?)\*\* se metió.+encontró (.+?) (.+?) \*\*(\bgodly\b \bpresent\b|\bvoid\b \bpresent\b|\beternal\b \bpresent\b|\bepic\b \bsnowball\b)\*\*', #Spanish/Portuguese, chimney
                ]
                item_events = {
                    'godly present': 'xmas_godly',
                    'void present': 'xmas_void',
                    'eternal present': 'xmas_eternal',
                    'epic snowball': 'xmas_snowball',
                }
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match: return
                user_name = match.group(1)
                item_amount = match.group(2)
                item_name = match.group(4)
                event = item_events.get(item_name.lower().replace('**',''), None)
                if event is None: return
                if user is None:
                    guild_users = await functions.get_member_by_name(self.bot, message.guild, user_name)
                    if len(guild_users) > 1:
                        await functions.add_warning_reaction(message)
                        await message.reply(
                            f'Congratulations, you found something worthy of an auto flex!\n'
                            f'Sadly I am unable to determine who you are as your username is not unique.\n'
                            f'To resolve this, either change your username (not nickname!) or use slash commands next time.'
                        )
                        return
                    if not guild_users: return
                    user = guild_users[0]
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if event == 'xmas_godly':
                    description = (
                        f'**{user_name}** pretended to be nice all year, fooled Santa and got {item_amount} nice shiny '
                        f'{emojis.PRESENT_GODLY} **GODLY present** as a reward.'
                    )
                elif event == 'xmas_void':
                    description = (
                        f'**{user_name}** just stumbled upon the rarest of gifts!\n'
                        f'Wdym "love, family and friends"? I\'m talking about {item_amount} {emojis.PRESENT_VOID} '
                        f'**VOID present**, duh.'
                    )
                elif event == 'xmas_eternal':
                    description = (
                        f'**{user_name}** found {item_amount} {emojis.PRESENT_ETERNAL} **ETERNAL present**!\n'
                        f'Totally deserved, too, they were nice all year, never complaining about their lousy RNG.'
                    )
                    await user_settings.update(inventory_present_eternal=user_settings.inventory.present_eternal + int(item_amount))
                elif event == 'xmas_snowball':
                    description = (
                        f'**{user_name}** just found {item_amount} {emojis.SNOWBALL_EPIC} **EPIC snowball**!\n'
                        f'I sense a snowman in their not-so-distant future.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

            # Christmas, stuck in chimney
            search_strings = [
                'stuck in the chimney...', #English
                'atascó en la chimenea...', #Spanish
                'atascó en la chimenea...', #TODO: Portuguese
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\*\ went', #English
                ]
                match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not match: return
                user_name = match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_XMAS_CHIMNEY,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex chimney message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** managed to get themselves stuck in a chimney. Send help!\n'
                    f'After uploading a video of the whole thing on tiktok ofc.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'xmas_chimney', description)

            # Forge godly cookie
            search_strings = [
                'bunch of cookies against the godly sword and then leaves it', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* press', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find use name in auto flex godly cookie message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_FORGE_GODLY_COOKIE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex godly cookie message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'Oh boy, oh boy, someone is going to try to beat the EPIC NPC today!\n'
                    f'Unless **{user_name}** just crafted a {emojis.GODLY_COOKIE} **GODLY cookie** for fun. '
                    f'You never know.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'forge_cookie',
                                                  description)

            # Lootboxes from hunt and adventure
            search_strings = [
                'found a', #English
                'found the', #English
                'encontr', #Spanish, Portuguese
            ]
            search_strings_loot = [
                'omega lootbox',
                'godly lootbox',
                'void lootbox',
                'eternal lootbox',
                'wolf skin',
                'zombie eye',
                'unicorn horn',
                'mermaid hair',
                'chip',
                'dragon scale',
                'dark energy',
                'epic berry',
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and (
                    any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_HUNT)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_HUNT_TOP)
                    or any(f'> {monster.lower()}' in message_content.lower() for monster in strings.MONSTERS_ADVENTURE)
                    or any(monster.lower() in message_content.lower() for monster in strings.MONSTERS_ADVENTURE_TOP)
                )
                and any(search_string in message_content.lower() for search_string in search_strings_loot)
            ):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                hardmode = together = False
                new_format_match = re.search(r'^__\*\*', message_content)
                old_format = False if new_format_match else True
                search_strings_hardmode = [
                    '(but stronger', #English
                    '(pero más fuerte', #Spanish
                    '(só que mais forte', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_hardmode):
                    hardmode = True
                search_strings_together = [
                    'hunting together', #English
                    'cazando juntos', #Spanish
                    'caçando juntos', #Portuguese
                ]
                if any(search_string in message_content.lower() for search_string in search_strings_together):
                    together = True
                partner_name = None
                if together:
                    search_patterns = [
                        r"\*\*(.+?)\*\* and \*\*(.+?)\*\*", #English
                        r"\*\*(.+?)\*\* y \*\*(.+?)\*\*", #Spanish
                        r"\*\*(.+?)\*\* e \*\*(.+?)\*\*", #Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        partner_name = user_name_match.group(2)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('User names not found in auto flex hunt together message.', message)
                        return
                else:
                    search_patterns_user_name = [
                        r"\*\*(.+?)\*\* found a", #English
                        r"\*\*(.+?)\*\* encontr", #Spanish, Portuguese
                    ]
                    user_name_match = await functions.get_match_from_patterns(search_patterns_user_name, message_content)
                    if not user_name_match:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user name in auto flex hunt message.', message)
                        return
                    user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HUNT_ADVENTURE,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex hunt/adventure message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                # Lootboxes
                lootboxes_user = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                    'ETERNAL lootbox': emojis.LB_ETERNAL,
                }
                lootboxes_user_lost = {
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                    'ETERNAL lootbox': emojis.LB_ETERNAL,
                }
                if message.guild.id != 713541415099170836:
                    lootboxes_user_lost['OMEGA lootbox'] = emojis.LB_OMEGA
                lootboxes_partner = {
                    'OMEGA lootbox': emojis.LB_OMEGA,
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                    'ETERNAL lootbox': emojis.LB_ETERNAL,
                }
                lootboxes_partner_lost = {
                    'GODLY lootbox': emojis.LB_GODLY,
                    'VOID lootbox': emojis.LB_VOID,
                    'ETERNAL lootbox': emojis.LB_ETERNAL,
                }
                if message.guild.id != 713541415099170836:
                    lootboxes_partner_lost['OMEGA lootbox'] = emojis.LB_OMEGA
                lootbox_user_found = []
                lootbox_user_lost = []
                lootbox_partner_found = []
                lootbox_partner_lost = []
                epic_berry_user_found = []
                epic_berry_partner_found = []
                search_patterns_together_old_user = [
                    fr"{re.escape(user_name)}\*\* got (.+?) (.+?)", #English
                    fr"{re.escape(user_name)}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_together_old_user_lost = [
                    fr"{re.escape(user_name)}\*\* lost (.+?) (.+?)", #English
                ]
                search_patterns_solo = [
                    fr"\*\* got (.+?) (.+?)", #English
                    fr"\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                ]
                search_patterns_solo_lost = [
                    fr"\*\* lost (.+?) (.+?)", #English
                ]
                message_content_user = message_content_partner = ''
                search_patterns_user = []
                search_patterns_user_lost = []
                search_patterns_partner = []
                search_patterns_partner_lost = []
                if together and not old_format:
                    partner_loot_start = message_content.find(f'**{partner_name}**:')
                    message_content_user = message_content[:partner_loot_start]
                    message_content_partner = message_content[partner_loot_start:]

                if together:
                    search_patterns_together_new = [
                        fr"\+(.+?) (.+?)", #All languages, slash
                        fr"got (.+?) (.+?)", #English, prefix
                        fr"cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese, prefix
                    ]
                    search_patterns_together_new_lost = [
                        fr"\-(.+?) (.+?)", #All languages, slash
                        fr"lost (.+?) (.+?)", #English, prefix
                    ]
                    search_patterns_together_old_partner = [
                        fr"{re.escape(partner_name)}\*\* got (.+?) (.+?)", #English
                        fr"{re.escape(partner_name)}\*\* cons(?:e|i)gui(?:ó|u) (.+?) (.+?)", #Spanish, Portuguese
                    ]
                    search_patterns_together_old_partner_lost = [
                        fr"{re.escape(partner_name)}\*\* lost (.+?) (.+?)", #English
                    ]
                    if old_format:
                        search_patterns_user = search_patterns_together_old_user
                        search_patterns_user_lost = search_patterns_together_old_user_lost
                        search_patterns_partner = search_patterns_together_old_partner
                        search_patterns_partner_lost = search_patterns_together_old_partner_lost
                        message_content_user = message_content_partner = message_content
                    else:
                        search_patterns_user = search_patterns_partner = search_patterns_together_new
                        search_patterns_user_lost = search_patterns_partner_lost = search_patterns_together_new_lost
                        partner_loot_start = message_content.find(f'**{partner_name}**:')
                        message_content_user = message_content[:partner_loot_start]
                        message_content_partner = message_content[partner_loot_start:]
                else:
                    search_patterns_user = search_patterns_solo
                    search_patterns_user_lost = search_patterns_solo_lost
                    message_content_user = message_content

                for lootbox in lootboxes_user.keys():
                    for pattern in search_patterns_user:
                        pattern = rf'{pattern} {re.escape(lootbox)}'
                        lootbox_match = re.search(pattern, message_content_user, re.IGNORECASE)
                        if lootbox_match: break
                    if not lootbox_match: continue
                    lootbox_amount = lootbox_match.group(1)
                    lootbox_user_found.append(lootbox)
                    lootbox_user_found.append(lootbox_amount)
                    break
                
                for lootbox in lootboxes_user_lost.keys():
                    for pattern in search_patterns_user_lost:
                        pattern = rf'{pattern} {re.escape(lootbox)}'
                        lootbox_match = re.search(pattern, message_content_user, re.IGNORECASE)
                        if lootbox_match: break
                    if not lootbox_match: continue
                    lootbox_amount = lootbox_match.group(1)
                    lootbox_user_lost.append(lootbox)
                    lootbox_user_lost.append(lootbox_amount)
                    break

                for pattern in search_patterns_user:
                    pattern = rf'{pattern} epic berry'
                    berry_match = re.search(pattern, message_content_user, re.IGNORECASE)
                    if berry_match:
                        drop_amount = int(berry_match.group(1))
                        if (user_settings.current_area == 0
                            or 'pretending' in message_content_user.lower()
                            or 'pretendiendo' in message_content_user.lower()
                            or 'fingindo' in message_content_user.lower()):
                            drop_amount_check = drop_amount / 3
                        else:
                            drop_amount_check = drop_amount
                        if drop_amount_check >= 5:
                            epic_berry_user_found.append('EPIC berry')
                            epic_berry_user_found.append(drop_amount)
                            break

                if together:
                    for lootbox in lootboxes_partner.keys():
                        for pattern in search_patterns_partner:
                            pattern = rf'{pattern} {re.escape(lootbox)}'
                            lootbox_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                            if lootbox_match: break
                        if not lootbox_match: continue
                        lootbox_amount = lootbox_match.group(1)
                        lootbox_partner_found.append(lootbox)
                        lootbox_partner_found.append(lootbox_amount)
                        break
                    
                    for lootbox in lootboxes_partner_lost.keys():
                        for pattern in search_patterns_partner_lost:
                            pattern = rf'{pattern} {re.escape(lootbox)}'
                            lootbox_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                            if lootbox_match: break
                        if not lootbox_match: continue
                        lootbox_amount = lootbox_match.group(1)
                        lootbox_partner_lost.append(lootbox)
                        lootbox_partner_lost.append(lootbox_amount)
                        break

                    for pattern in search_patterns_partner:
                        pattern = rf'{pattern} epic berry'
                        berry_match = re.search(pattern, message_content_partner, re.IGNORECASE)
                        if berry_match:
                            drop_amount = int(berry_match.group(1))
                            if ('pretending' in message_content_partner.lower()
                                or 'pretendiendo' in message_content_partner.lower()
                                or 'fingindo' in message_content_partner.lower()):
                                drop_amount_check = drop_amount / 3
                            else:
                                drop_amount_check = drop_amount
                            if drop_amount_check >= 5:
                                epic_berry_partner_found.append('EPIC berry')
                                epic_berry_partner_found.append(drop_amount)
                                break

                lb_omega_non_hm_amount = 2 if message.guild.id == 713541415099170836 else 1
                lb_omega_hm_amount = 3
                lb_omega_partner_amount = 2 if message.guild.id == 713541415099170836 else 1
                if (lootbox_user_found or lootbox_partner_found or epic_berry_user_found
                    or epic_berry_partner_found or lootbox_user_lost or lootbox_partner_lost):

                    # Lootboxes
                    events_user = {
                        'OMEGA lootbox': 'lb_omega',
                        'GODLY lootbox': 'lb_godly',
                        'VOID lootbox': 'lb_void',
                        'ETERNAL lootbox': 'lb_eternal',
                    }
                    events_partner = {
                        'OMEGA lootbox': 'lb_omega_partner',
                        'GODLY lootbox': 'lb_godly_partner',
                        'VOID lootbox': 'lb_void_partner',
                        'ETERNAL lootbox': 'lb_eternal_partner',
                    }
                    description = event = ''
                    if lootbox_user_found:
                        name, amount = lootbox_user_found
                        event = events_user[name]
                        if event == 'lb_void':
                            description = (
                                f'Everbody rejoice because **{user_name}** did something almost impossible and found '
                                f'**{amount}** {lootboxes_user[name]} **{name}**!\n'
                                f'We are all so happy for you and not at all jealous.'
                            )
                        elif event == 'lb_eternal':
                            description = (
                                f'Shiny! **{user_name}** just found something... blue? Might this be '
                                f'**{amount}** {lootboxes_user[name]} **{name}**??\n'
                                f'This would also be a good excuse for a giveaway, you know.'
                            )
                        elif event == 'lb_omega':
                            if not hardmode and int(amount) >= lb_omega_non_hm_amount:
                                event = 'lb_omega_no_hardmode'
                                description = (
                                    f'**{user_name}** found {amount} {lootboxes_user[name]} **{name}** just like that.\n'
                                    f'And by "just like that" I mean **without hardmoding**!\n'
                                    f'See, hardmoders, that\'s how it\'s done!'
                                )
                            elif int(amount) >= lb_omega_hm_amount:
                                event = 'lb_omega_multiple'
                                description = (
                                    f'While an {lootboxes_user[name]} **{name}** isn\'t very exciting, '
                                    f'**{user_name}** just found __**{amount}**__ of them at once!\n'
                                    f'(Well, actually, the horse did all the work)'
                                )
                            else:
                                event = ''
                        else:
                            description = (
                                f'**{user_name}** just found **{amount}** {lootboxes_user[name]} **{name}**!\n'
                                f'~~They should be banned!~~ We are so happy for you!'
                            )
                    if lootbox_user_lost:
                        name, amount = lootbox_user_lost
                        event = 'lb_a18'
                        description = (
                            f'**{user_name}** just lost **{amount}** {lootboxes_user_lost[name]} **{name}**!\n'
                            f'Damn, they really suck at this game.'
                        )
                    if lootbox_partner_found:
                        name, amount = lootbox_partner_found
                        if lootbox_user_found and event != '':
                            description = (
                                f'{description}\n\n'
                                f'Ah yes, also... as if that wasn\'t OP enough, they also found their partner '
                                f'**{partner_name}** **{amount}** {lootboxes_partner[name]} **{name}** ON TOP OF THAT!\n'
                                f'I am really not sure why this much luck is even allowed.'
                            )
                        else:
                            event = events_partner[name]
                            if event == 'lb_godly_partner':
                                description = (
                                    f'If you ever wanted to see what true love looks like, here\'s an example:\n'
                                    f'**{user_name}** just got their partner **{partner_name}** **{amount}** '
                                    f'{lootboxes_partner[name]} **{name}**!\n'
                                    f'We\'re all jealous.'
                                )
                            elif event == 'lb_void_partner':
                                description = (
                                    f'I am speechless because what we are seeing here is one of the rarest things ever.\n'
                                    f'**{user_name}** just found their partner **{partner_name}**... **{amount}** '
                                    f'{lootboxes_partner[name]} **{name}**.\n'
                                    f'Yes, you read that right.'
                                )
                            elif event == 'lb_eternal_partner':
                                description = (
                                    f'Of course it is **{partner_name}**, who else would be brave and lucky enough to steal '
                                    f'**{amount}** {lootboxes_partner[name]} **{name}** from their partner?\n'
                                    f'**{user_name}** might need emotional support after this.'
                                )
                            elif int(amount) >= lb_omega_partner_amount:
                                description = (
                                    f'**{user_name}** ordered **{amount}** {lootboxes_partner[name]} **{name}** and it '
                                    f'just got delivered.\n'
                                    f'...to **{partner_name}**\'s address lol.'
                                )
                    if lootbox_partner_lost:
                        name, amount = lootbox_partner_lost
                        event = 'lb_a18_partner'
                        description = (
                            f'**{user_name}** turns out to be the worst partner you can image.\n'
                            f'They just made **{partner_name}** lose  **{amount}** {lootboxes_user_lost[name]} **{name}**!\n'
                            f'You should be ashamed, really.'
                        )
                    if description != '':
                        await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)

                    # EPIC berries
                    description = ''
                    if epic_berry_user_found:
                        name, amount = epic_berry_user_found
                        event = 'epic_berry'
                        description = (
                            f'**{user_name}** found **{amount}** {emojis.EPIC_BERRY} **EPIC berries**!\n'
                            f'I can see a drooling horse approaching in the distance. Better get out of the way.'
                        )

                    if epic_berry_partner_found:
                        name, amount = epic_berry_partner_found
                        if description != '':
                            event = 'epic_berry'
                            description = (
                                f'{description}\n\n'
                                f'Because **{user_name}** is such a nice person and likes to share, '
                                f'their partner **{partner_name}** also got **{amount}**!\n'
                                f'What a lovely marriage.'
                            )
                        else:
                            event = 'epic_berry_partner'
                            description = (
                                f'What do you get when you marry? Love? Happiness? Gifts?\n'
                                f'Your **{amount}** {emojis.EPIC_BERRY} **EPIC berries** stolen, that\'s what.\n'
                                f'If you don\'t believe me, look at what **{partner_name}** just did to **{user_name}**!'
                            )
                    if description != '':
                        await self.send_auto_flex_message(message, guild_settings, user_settings, user, event, description)


            # Lootbox event
            search_strings = [
                'your lootbox has evolved', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* uses', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex lootbox event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_OPEN,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex lootbox event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** used a magic spell on a lootbox for some reason which then evolved into an '
                    f'{emojis.LB_OMEGA} **OMEGA lootbox**! For some reason.\n'
                    f'I wonder what the Ministry of Magic would say to this.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_lb', description)

            # Enchant event
            search_strings = [
                'your sword got an ultra-edgy enchantment', #English sword
                'your armor got an ultra-edgy enchantment', #English armor
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* tries', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex enchant event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ENCHANT,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex enchant event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** failed to enchant stuff properly and enchanted the same thing twice.\n'
                    f'Somehow that actually worked tho and got them an **ULTRA-EDGY enchant**? {emojis.ANIME_SUS}'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_enchant',
                                                  description)

            # Farm event
            search_strings = [
                'the seed surrendered', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* hits', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex farm event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_FARM,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex farm event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                search_patterns = [
                    r'up (\d+?) times', #English
                ]
                levels_match = await functions.get_match_from_patterns(search_patterns, message_content)
                levels = int(levels_match.group(1))
                if levels > 0:
                    description = (
                        f'**{user.name}** fought a seed (why) by hitting the floor with their fists (what) '
                        f'and **leveled up {levels:,} times** (??).\n'
                        f'Yeah, that totally makes sense.'
                    )
                else:
                    description = (
                        f'**{user.name}** fought a seed by smashing the floor with their bare hands.\n'
                        f'Not only does this not make any sense whatsoever, they didn\'t even get a single level out of '
                        f'it.\n'
                        f'Embarassing, really.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_farm',
                                                  description)

            # Heal event
            search_strings = [
                'killed the mysterious man', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r'\*\*(.+?)\*\* killed', #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex heal event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HEAL,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex heal event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                description = (
                    f'**{user.name}** encountered a poor and lonely **mysterious man** and... killed him.\n'
                    f'Enjoy your **level up**, I guess. Hope you feel bad.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_heal',
                                                  description)

            # Training event
            search_strings = [
                'wings spawned', #English
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r"in \*\*(.+?)\*\*'s back", #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex training event message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_TRAINING,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex training event message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                search_patterns = [
                    r'became \*\*(\d+?) ', #English
                ]
                amount_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not amount_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find dark energy amount in auto flex training event message.', message)
                    return
                amount = amount_match.group(1)
                description = (
                    f'**{user.name}** was tired of an earthly existence and tried to fly away.\n'
                    f'_Somehow_ they not only spawned wings and didn\'t crash miserably, they also found '
                    f'**{amount}** {emojis.DARK_ENERGY} **dark energy** while doing that.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'event_training',
                                                  description)

            # Time capsule
            search_strings = [
                "a portal was opened", #English
                "se abrió un portal", #Spanish
                "um portal foi aberto", #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(r'\*\*(.+?)\*\* breaks', message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_TIME_CAPSULE,
                                                    user_name=user_name)
                        )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex time capsule message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.auto_flex_enabled
                    or user_settings.time_travel_count is None): return
                time_travel_count_new = user_settings.time_travel_count + 1
                trade_daily_total = floor(100 * (time_travel_count_new + 1) ** 1.35)
                await user_settings.update(time_travel_count=time_travel_count_new, trade_daily_total=trade_daily_total)
                event = f'time_travel_{time_travel_count_new}'
                try:
                    description = TIME_TRAVEL_DESCRIPTIONS[event].replace('{user_name}', user.name)
                except KeyError:
                    return
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Time travels from unsealing eternity
            search_strings = [
                "unsealed **the eternity**", #English
                "unsealed **the eternity**", #TODO: Spanish
                "unsealed **the eternity**", #TODO: Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                        user_command_message = (
                            await messages.find_message(message.channel.id, regex.COMMAND_UNSEAL_ETERNITY,
                                                    user_name=user_name)
                        )
                        if not user_name_match or user_command_message is None:
                            await functions.add_warning_reaction(message)
                            await errors.log_error('User not found in auto flex eternity unseal message.', message)
                            return
                        user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if (not user_settings.bot_enabled or not user_settings.auto_flex_enabled
                    or user_settings.time_travel_count is None): return

                time_travel_match = re.search(r'\s([\d,]+?)\s<', message_content)
                time_travel_count_old = user_settings.time_travel_count
                time_travel_count_new = time_travel_count_old + int(time_travel_match.group(1).replace(',',''))
                trade_daily_total = floor(100 * (time_travel_count_new + 1) ** 1.35)
                await user_settings.update(time_travel_count=time_travel_count_new, trade_daily_total=trade_daily_total)

                if time_travel_count_old < 1 and time_travel_count_new >= 1:
                    time_travel_flex_count = 1
                elif time_travel_count_old < 3 and time_travel_count_new >= 3:
                    time_travel_flex_count = 3
                elif time_travel_count_old < 5 and time_travel_count_new >= 5:
                    time_travel_flex_count = 5
                elif time_travel_count_old < 10 and time_travel_count_new >= 10:
                    time_travel_flex_count = 10
                elif time_travel_count_old < 25 and time_travel_count_new >= 25:
                    time_travel_flex_count = 25
                elif time_travel_count_old < 50 and time_travel_count_new >= 50:
                    time_travel_flex_count = 50
                elif time_travel_count_old < 100 and time_travel_count_new >= 100:
                    time_travel_flex_count = 100
                elif time_travel_count_old < 150 and time_travel_count_new >= 150:
                    time_travel_flex_count = 150
                elif time_travel_count_old < 200 and time_travel_count_new >= 200:
                    time_travel_flex_count = 200
                elif time_travel_count_old < 300 and time_travel_count_new >= 300:
                    time_travel_flex_count = 300
                elif time_travel_count_old < 400 and time_travel_count_new >= 400:
                    time_travel_flex_count = 400
                elif time_travel_count_old < 420 and time_travel_count_new >= 420:
                    time_travel_flex_count = 420
                elif time_travel_count_old < 500 and time_travel_count_new >= 500:
                    time_travel_flex_count = 500
                elif time_travel_count_old < 600 and time_travel_count_new >= 600:
                    time_travel_flex_count = 600
                elif time_travel_count_old < 700 and time_travel_count_new >= 700:
                    time_travel_flex_count = 700
                elif time_travel_count_old < 800 and time_travel_count_new >= 800:
                    time_travel_flex_count = 800
                elif time_travel_count_old < 900 and time_travel_count_new >= 900:
                    time_travel_flex_count = 900
                elif time_travel_count_old < 999 and time_travel_count_new >= 999:
                    time_travel_flex_count = 999
                elif time_travel_count_old < 1_100 and time_travel_count_new >= 1_100:
                    time_travel_flex_count = 1_100
                elif time_travel_count_old < 1_200 and time_travel_count_new >= 1_200:
                    time_travel_flex_count = 1_200
                elif time_travel_count_old < 1_300 and time_travel_count_new >= 1_300:
                    time_travel_flex_count = 1_300
                elif time_travel_count_old < 1_400 and time_travel_count_new >= 1_400:
                    time_travel_flex_count = 1_400
                elif time_travel_count_old < 1_500 and time_travel_count_new >= 1_500:
                    time_travel_flex_count = 1_500
                elif time_travel_count_old < 1_600 and time_travel_count_new >= 1_600:
                    time_travel_flex_count = 1_600
                elif time_travel_count_old < 1_700 and time_travel_count_new >= 1_700:
                    time_travel_flex_count = 1_700
                elif time_travel_count_old < 1_800 and time_travel_count_new >= 1_800:
                    time_travel_flex_count = 1_800
                elif time_travel_count_old < 1_900 and time_travel_count_new >= 1_900:
                    time_travel_flex_count = 1_900
                elif time_travel_count_old < 2_000 and time_travel_count_new >= 2_000:
                    time_travel_flex_count = 2_000
                elif time_travel_count_old < 1_000_000 and time_travel_count_new >= 1_000_000:
                    time_travel_flex_count = 1_000_000
                else:
                    return
                event = f'time_travel_{time_travel_flex_count}'
                try:
                    description = TIME_TRAVEL_DESCRIPTIONS[event].replace('{user_name}', user.name)
                except KeyError:
                    return
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

            # Rare halloween loot
            search_strings = [
                'sleepy potion', #English potion
                'suspicious broom', #English broom
            ]
            search_strings_scare = [
                '** scared **', #English potion
                'got so much scared', #English broom
                'got so hella scared', #English broom
            ]
            if (any(search_string in message_content.lower() for search_string in search_strings)
                and any(search_string in message_content.lower() for search_string in search_strings_scare)):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                search_patterns = [
                    r" \*\*(.+?)\*\* scared", #English
                    r"scared by \*\*(.+?)\*\*", #English
                ]
                user_name_match = await functions.get_match_from_patterns(search_patterns, message_content)
                if not user_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find user name in auto flex hal boo message.', message)
                    return
                user_name = user_name_match.group(1)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_HAL_BOO,
                                                    user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find user for auto flex hal boo message.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return

                if 'sleepy potion' in message_content.lower():
                    emoji = emojis.SLEEPY_POTION
                    item_name = 'sleepy potion'
                else:
                    emoji = emojis.SUSPICIOUS_BROOM
                    item_name = 'suspicious broom'
                description = (
                    f'**{user.name}** scared a friend to death and got a {emoji} **{item_name}** as a reward for that.\n'
                    f'So we\'re getting rewarded for being a bad friend now? Hope you feel bad, okay?'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'hal_boo',
                                                  description)

            # Brew electronical potion
            search_strings = [
                '**electronical potion**, you\'ve received the following boosts', #English
                '**electronical potion**, has recibido los siguientes boosts', #Spanish
                '**electronical potion**, recebeu os seguintes boosts', #Portuguese
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_command_message = (
                        await messages.find_message(message.channel.id, regex.COMMAND_ALCHEMY)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the dragon breath potion auto flex.', message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                description = (
                    f'**{user.name}** is thirsty, but unlike, you know, _normal_ people, it has to be the rather exclusive '
                    f'{emojis.POTION_ELECTRONICAL} **Electronical potion** for them.\n'
                    f'The snob.'
                )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'brew_electronical',
                                                  description)

            # Card drops
            search_strings = [
                'epic card',
                'omega card',
                'godly card',
                'void card',
                'eternal card',
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if not user_name_match:
                        user_name_match = re.search(r'__\*\*(.+?)\*\* ', message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for autoflex card drop message.', message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the autoflex card drop message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                card_recipient_name_match = re.search(
                    r'\*\*(.+?)\*\* (?:recebeu|conseguiu|consiguió|got) 1 (.+?) \*\*(.+?) card\*\*',
                    message_content
                )
                if not card_recipient_name_match:
                    await functions.add_warning_reaction(message)
                    await errors.log_error('Couldn\'t find card recipient for autoflex card drop message.', message)
                    return
                card_recipient_name = card_recipient_name_match.group(1)
                card_name = card_recipient_name_match.group(3)
                card_emoji = getattr(emojis, f'CARD_{card_name.upper()}', '')
                if await functions.encode_text(user.name) == await functions.encode_text(card_recipient_name):
                    event = 'card_drop'
                else:
                    event = 'card_drop_partner'
                if event == 'card_drop':
                    description = (
                        f'**{user.name}** hacked the game and got a {card_emoji} **{card_name} card**.\n'
                        f'I would argue that being this lucky justifies an instant ban, really.'
                    )
                elif event == 'card_drop_partner':
                    description = (
                        f'**{user.name}** just came up VERY close with a {card_emoji} **{card_name} card**.\n'
                        f'Too bad it got snatched away by their partner **{card_recipient_name}** right after.\n'
                        f'What a loser, lol.'
                    )
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, event,
                                                  description)

                
            # Golden cards
            search_strings = [
                'goldened these cards!',
            ]
            if any(search_string in message_content.lower() for search_string in search_strings):
                guild_settings: guilds.Guild = await guilds.get_guild(message.guild.id)
                if not guild_settings.auto_flex_enabled: return
                user = await functions.get_interaction_user(message)
                if user is None:
                    user_name_match = re.search(regex.NAME_FROM_MESSAGE_START, message_content)
                    if not user_name_match:
                        user_name_match = re.search(r'^\*\*(.+?)\*\* ', message_content)
                    if user_name_match:
                        user_name = user_name_match.group(1)
                    else:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a user for autoflex golden card message.', message)
                        return
                    user_command_message = (
                        await messages.find_message(message.channel.id, user_name=user_name)
                    )
                    if user_command_message is None:
                        await functions.add_warning_reaction(message)
                        await errors.log_error('Couldn\'t find a command for the autoflex golden card message.',
                                               message)
                        return
                    user = user_command_message.author
                try:
                    user_settings: users.User = await users.get_user(user.id)
                except exceptions.FirstTimeUserError:
                    return
                if not user_settings.bot_enabled or not user_settings.auto_flex_enabled: return
                
                description = (
                    f'**{user.name}** played some poker, won (clearly cheated) and goldened all their cards.\n'
                    f'These EPIC RPG players get more decadent every day.'
                )
                
                await self.send_auto_flex_message(message, guild_settings, user_settings, user, 'card_golden',
                                                  description)
                    


# Initialization
def setup(bot: bridge.AutoShardedBot):
    bot.add_cog(AutoFlexCog(bot))
