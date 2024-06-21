# misc.py
"""Contains miscellaneous commands"""

from decimal import Decimal, ROUND_HALF_UP

import discord
from discord.ext import bridge

# --- Commands ---
async def command_calculator(bot: bridge.AutoShardedBot, ctx: bridge.BridgeContext, calculation: str) -> None:
    """Calculator command"""
    def formatNumber(num):
        if num % 1 == 0:
            return int(num)
        else:
            num = num.quantize(Decimal('1.1234567890'), rounding=ROUND_HALF_UP)
            return num
    calculation = calculation.replace(' ','')
    allowedchars = set('1234567890.-+/*%()')
    if not set(calculation).issubset(allowedchars) or '**' in calculation:
        answer = (
            f'Invalid characters. Please only use numbers and supported operators.\n'
            f'Supported operators are `+`, `-`, `/`, `*` and `%`.'
        )
        if isinstance(ctx, discord.ApplicationContext):
            await ctx.respond(answer, ephemeral=True)
        else:
            await ctx.reply(answer)
        return
    error_parsing = (
        f'Error while parsing your input. Please check your input.\n'
        f'Supported operators are `+`, `-`, `/`, `*` and `%`.'
    )
    # Parse open the calculation, convert all numbers to float and store it as a list
    # This is necessary because Python has the annoying habit of allowing infinite integers which can completely lockup a system. Floats have overflow protection.
    pos = 1
    calculation_parsed = []
    number = ''
    last_char_was_operator = False # Not really accurate name, I only use it to check for *, % and /. Multiple + and - are allowed.
    last_char_was_number = False
    calculation_sliced = calculation
    try:
        while pos != len(calculation) + 1:
            slice = calculation_sliced[0:1]
            allowedcharacters = set('1234567890.-+/*%()')
            if set(slice).issubset(allowedcharacters):
                if slice.isnumeric():
                    if last_char_was_number:
                        number = f'{number}{slice}'
                    else:
                        number = slice
                        last_char_was_number = True
                    last_char_was_operator = False
                else:
                    if slice == '.':
                        if number == '':
                            number = f'0{slice}'
                            last_char_was_number = True
                        else:
                            number = f'{number}{slice}'
                    else:
                        if number != '':
                            calculation_parsed.append(Decimal(float(number)))
                            number = ''

                        if slice in ('*','%','/'):
                            if last_char_was_operator:
                                if isinstance(ctx, discord.ApplicationContext):
                                    await ctx.respond(error_parsing, ephemeral=True)
                                else:
                                    await ctx.reply(error_parsing)
                                return
                            else:
                                calculation_parsed.append(slice)
                                last_char_was_operator = True
                        else:
                            calculation_parsed.append(slice)
                            last_char_was_operator = False
                        last_char_was_number = False
            else:
                if isinstance(ctx, discord.ApplicationContext):
                    await ctx.respond(error_parsing, ephemeral=True)
                else:
                    await ctx.reply(error_parsing)
                return

            calculation_sliced = calculation_sliced[1:]
            pos += 1
        else:
            if number != '':
                calculation_parsed.append(Decimal(float(number)))
    except:
        if isinstance(ctx, discord.ApplicationContext):
            await ctx.respond(error_parsing, ephemeral=True)
        else:
            await ctx.reply(error_parsing)
        return

    # Reassemble and execute calculation
    calculation_reassembled = ''
    for slice in calculation_parsed:
        calculation_reassembled = f'{calculation_reassembled}{slice}'
    try:
        #result = eval(calculation_reassembled) # This line seems useless
        result = Decimal(eval(calculation_reassembled))
        result = formatNumber(result)
        if isinstance(result, int):
            result = f'{result:,}'
        else:
            result = f'{result:,}'.rstrip('0').rstrip('.')
        if len(result) > 2000:
            answer = 'Well. Whatever you calculated, the result is too long to display. GG.'
            if isinstance(ctx, discord.ApplicationContext):
                await ctx.respond(answer, ephemeral=True)
            else:
                await ctx.reply(answer)
            return
    except:
        answer = (
            f'Well, _that_ didn\'t calculate to anything useful.\n'
            f'What were you trying to do there? :thinking:'
        )
        if isinstance(ctx, discord.ApplicationContext):
            await ctx.respond(answer, ephemeral=True)
        else:
            await ctx.reply(answer)
        return
    if isinstance(ctx, discord.ApplicationContext):
        await ctx.respond(result)
    else:
        await ctx.reply(result)
    return