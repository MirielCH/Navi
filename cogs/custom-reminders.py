# custom-reminders.py

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import discord
import emojis
import global_data
import global_functions
import asyncio
import database

from discord.ext import commands
from discord.ext import tasks
from datetime import datetime, timedelta

# custom reminder commands (cog)
class customCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Commands ---
    # rm
    @commands.command(aliases=('reminder','remind',))
    @commands.bot_has_permissions(send_messages=True)
    async def rm(self, ctx, *args):

        prefix = ctx.prefix

        syntax_add = (
            f'The syntax is `{ctx.prefix}rm [time] [text]`\n'
            f'Support time codes: `w`, `d`, `h`, `m`, `s`\n\n'
            f'Example: `{ctx.prefix}rm 1h30m Coffee time!`'
        )

        syntax_delete = (
            f'The syntax is `{ctx.prefix}rm delete [ID]`\n'
            f'You can find the ID with `{prefix}list`\n\n'
            f'Example: `{ctx.prefix}rm delete 3`'
        )

        error_invalid_time = (
            f'Invalid time.\n\n'
            f'{syntax_add}'
        )

        error_invalid_message_id = (
            f'Invalid message ID.\n\n'
            f'{syntax_delete}'
        )

        error_max_time = 'The maximum time is 4w6d23h59m59s.'

        if args:
            arg = args[0]
            if arg in ('delete','del'):
                if len(args) == 2:
                    reminder_id = args[1]
                    if reminder_id.isnumeric():
                        try:
                            reminder_id = int(reminder_id)
                            if reminder_id <= 9:
                                activity = f'custom0{reminder_id}'
                            else:
                                activity = f'custom{reminder_id}'
                            delete_status = await database.delete_reminder(ctx, ctx.author.id, activity)
                            task_name = f'{ctx.author.id}-{activity}'
                            if delete_status == 'deleted':
                                if task_name in global_data.running_tasks:
                                    global_data.running_tasks[task_name].cancel()
                                    delete_task = global_data.running_tasks.pop(task_name, None)
                                await ctx.message.add_reaction(emojis.navi)
                            elif delete_status == 'notfound':
                                await ctx.reply('There is no custom reminder with that ID.', mention_author=False)
                                return
                            else:
                                await ctx.reply('There was an error deleting the reminder, RIP.', mention_author=False)
                                return
                            return
                        except:
                            await ctx.reply(error_invalid_message_id, mention_author=False)
                            return
                    else:
                        await ctx.reply(error_invalid_message_id, mention_author=False)
                        return
                else:
                    await ctx.reply(syntax_delete, mention_author=False)
                    return
            else:
                last_time_code = None
                last_char_was_number = False
                reminder_text = ''
                timestring_complete = False
                timestring = ''
                current_number = ''
                arg_time = args[0].lower()
                pos = 0
                while not pos == len(arg_time):
                    slice = arg_time[pos:pos+1]
                    pos = pos+1
                    allowedcharacters_numbers = set('1234567890')
                    allowedcharacters_timecode = set('wdhms')
                    if set(slice).issubset(allowedcharacters_numbers):
                        timestring = f'{timestring}{slice}'
                        current_number = f'{current_number}{slice}'
                        last_char_was_number = True
                    elif set(slice).issubset(allowedcharacters_timecode) and last_char_was_number == True:
                        if slice == 'w':
                            if last_time_code == None:
                                timestring = f'{timestring}w'
                                try:
                                    current_number_numeric = int(current_number)
                                except Exception as e:
                                    await ctx.send(f'Error: {e}')
                                    return
                                if current_number_numeric > 4:
                                    await ctx.reply(error_max_time, mention_author=False)
                                    return
                                last_time_code = 'weeks'
                                last_char_was_number = False
                                current_number = ''
                            else:
                                await ctx.reply(error_invalid_time, mention_author=False)
                                return
                        elif slice == 'd':
                            if last_time_code in ('weeks', None):
                                timestring = f'{timestring}d'
                                try:
                                    current_number_numeric = int(current_number)
                                except Exception as e:
                                    await ctx.send(f'Error: {e}')
                                    return
                                if current_number_numeric > 34:
                                    await ctx.reply(error_max_time, mention_author=False)
                                    return
                                last_time_code = 'days'
                                last_char_was_number = False
                                current_number = ''
                            else:
                                await ctx.reply(error_invalid_time, mention_author=False)
                                return
                        elif slice == 'h':
                            if last_time_code in ('days',None):
                                timestring = f'{timestring}h'
                                try:
                                    current_number_numeric = int(current_number)
                                except Exception as e:
                                    await ctx.reply(f'Error: {e}', mention_author=False)
                                    return
                                last_time_code = 'hours'
                                last_char_was_number = False
                                current_number = ''
                            else:
                                await ctx.reply(error_invalid_time, mention_author=False)
                                return
                        elif slice == 'm':
                                if last_time_code in ('days','hours',None):
                                    timestring = f'{timestring}m'
                                    try:
                                        current_number_numeric = int(current_number)
                                    except Exception as e:
                                        await ctx.reply(f'Error: {e}', mention_author=False)
                                        return
                                    last_time_code = 'minutes'
                                    last_char_was_number = False
                                    current_number = ''
                                else:
                                    await ctx.reply(error_invalid_time, mention_author=False)
                                    return
                        elif slice == 's':
                            if last_time_code in ('days','hours','minutes',None):
                                timestring = f'{timestring}s'
                                try:
                                    current_number_numeric = int(current_number)
                                except Exception as e:
                                    await ctx.reply(f'Error: {e}', mention_author=False)
                                    return
                                last_time_code = 'seconds'
                                last_char_was_number = False
                                current_number = ''
                            else:
                                await ctx.reply(error_invalid_time, mention_author=False)
                                return
                        else:
                            await ctx.reply(error_invalid_time, mention_author=False)
                            return
                    else:
                        await ctx.reply(error_invalid_time, mention_author=False)
                        return
                if last_char_was_number == True:
                    await ctx.reply(error_invalid_time, mention_author=False)
                    return
                if len(args) > 1:
                    args = list(args)
                    args.pop(0)
                    for arg in args:
                        reminder_text = f'{reminder_text} {arg}'
                else:
                    reminder_text = 'idk, something?'

                reminder_text = reminder_text.strip()

                time_left = await global_functions.parse_timestring(ctx, timestring)
                if time_left < 16:
                    await ctx.reply('The time needs to be at least 16 seconds, sorry.', mention_author=False)
                    return
                if time_left > 3023999:
                    await ctx.reply(error_max_time, mention_author=False)
                    return
                write_status = await global_functions.write_reminder(self.bot, ctx, 'custom', time_left, reminder_text)
                if write_status in ('inserted','scheduled','updated'):
                    await ctx.message.add_reaction(emojis.navi)
                else:
                    await ctx.reply('There was an error writing the reminder, RIP.', mention_author=False)
                    return
                return
        else:
            await ctx.reply(
                f'This command lets you manage custom reminders.\n\n'
                f'**Adding reminders**\n'
                f'{syntax_add}\n\n'
                f'**Deleting reminders**\n'
                f'{syntax_delete}',
                mention_author=False
            )

# Initialization
def setup(bot):
    bot.add_cog(customCog(bot))