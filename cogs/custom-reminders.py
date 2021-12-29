# custom-reminders.py

from discord.ext import commands

from database import reminders
from resources import emojis, exceptions, functions, strings


class CustomRemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    """Cog that contains custom reminder commands"""
    # --- Commands ---
    # rm
    @commands.group(aliases=('rm','remind',), invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def reminder(self, ctx: commands.Context, *args: str) -> None:
        """Sets custom reminders"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax_add = (
            f'The syntax is `{prefix}rm [time] [text]`\n'
            f'Support time codes: `w`, `d`, `h`, `m`, `s`\n\n'
            f'Example: `{prefix}rm 1h30m Coffee time!`'
        )
        syntax_delete = (
            f'The syntax is `{prefix}rm delete [ID]`\n'
            f'You can find the ID with `{prefix}list`\n\n'
            f'Example: `{prefix}rm delete 3`'
        )
        error_invalid_time = (
            f'Invalid time.\n\n'
            f'{syntax_add}'
        )
        error_max_time = 'The maximum time is 4w6d23h59m59s.'

        if not args:
            await ctx.reply(
                f'This command lets you manage custom reminders.\n\n'
                f'**Adding reminders**\n'
                f'{syntax_add}\n\n'
                f'**Deleting reminders**\n'
                f'{syntax_delete}',
                mention_author=False
            )
            return
        args = [arg.lower() for arg in args]
        arg_time = args[0]
        last_time_code = None
        last_char_was_number = False
        reminder_text = ''
        timestring = ''
        current_number = ''
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
            elif set(slice).issubset(allowedcharacters_timecode) and last_char_was_number:
                if slice == 'w':
                    if last_time_code is None:
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
                    if last_time_code in ('weeks',None):
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
                    if last_time_code in ('weeks','days',None):
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
                    if last_time_code in ('weeks','days','hours',None):
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
                    if last_time_code in ('weeks','days','hours','minutes',None):
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
            if last_char_was_number:
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
            reminder_text = strings.DEFAULT_MESSAGE_CUSTOM_REMINDER.replace('%', reminder_text)
            time_left = await functions.parse_timestring_to_timedelta(ctx, timestring)
            if time_left.total_seconds() > 3_023_999:
                await ctx.reply(error_max_time, mention_author=False)
                return
            reminder: reminders.Reminder = (
                await reminders.insert_user_reminder(ctx.author.id, 'custom', time_left,
                                                     ctx.channel.id, reminder_text)
            )
            if reminder.record_exists:
                await ctx.message.add_reaction(emojis.NAVI)
            else:
                await ctx.reply(strings.MSG_ERROR, mention_author=False)

    @reminder.command(name='delete', aliases=('del','remove'), invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_delete(self, ctx: commands.Context, *args: str) -> None:
        """Sets custom reminders"""
        prefix = ctx.prefix
        if prefix.lower() == 'rpg ': return
        syntax_delete = (
            f'The syntax is `{prefix}rm delete [ID]`\n'
            f'You can find the ID with `{prefix}list`\n\n'
            f'Example: `{prefix}rm delete 3`'
        )
        error_invalid_message_id = (
            f'Invalid message ID.\n\n'
            f'{syntax_delete}'
        )
        if not args or len(args) > 1:
            await ctx.reply(syntax_delete, mention_author=False)
            return
        try:
            reminder_id = int(args[0])
        except:
            await ctx.reply(error_invalid_message_id, mention_author=False)
            return
        if reminder_id < 1:
            await ctx.reply(error_invalid_message_id, mention_author=False)
            return
        try:
            reminder: reminders.Reminder = await reminders.get_user_reminder(ctx.author.id, 'custom', reminder_id)
        except exceptions.NoDataFoundError:
            await ctx.reply('There is no custom reminder with that ID.', mention_author=False)
            return
        await reminder.delete()
        if not reminder.record_exists:
            await ctx.message.add_reaction(emojis.NAVI)
        else:
            await ctx.reply('There was an error deleting the reminder, RIP.', mention_author=False)


# Initialization
def setup(bot):
    bot.add_cog(CustomRemindersCog(bot))