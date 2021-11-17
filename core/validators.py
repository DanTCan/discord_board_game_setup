from core.core import discord, global_ctx


def check_yn(msg: discord.Message):
    return msg.author == global_ctx.author and msg.channel == global_ctx.channel and msg.content.lower() in ['y', 'n']


def check_reasonable_int(msg: discord.Message):
    bad_value = False
    try:
        if not 0 <= int(msg.content) <= 15:
            bad_value = True
    except TypeError or ValueError:
        bad_value = True
    return msg.author == global_ctx.author and msg.channel == global_ctx.channel and not bad_value


def check_new_or_show_lib(msg: discord.Message):
    bad_value = True
    print('TEST3', global_ctx, type(global_ctx))
    try:
        if msg.content.strip().lower() == 'new' or 'lib':
            bad_value = False
    except TypeError or ValueError:
        pass
    return msg.author == global_ctx.author and msg.channel == global_ctx.channel and not bad_value


def check_game_selection(msg: discord.Message):
    bad_value = False
    try:
        if int(msg.content) not in [game.game_id for game in data.games_cache]:
            bad_value = True
    except TypeError or ValueError:
        bad_value = True
    return msg.author == global_ctx.author and msg.channel == global_ctx.channel and not bad_value