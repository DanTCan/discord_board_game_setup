from core.core import discord, commands


class ContentValidator:
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx

    def yn(self, msg: discord.Message):
        return msg.author == self.ctx.author and msg.channel == self.ctx.channel and msg.content.lower() in ['y', 'n']

    def reasonable_int(self, msg: discord.Message):
        bad_value = False
        try:
            if not 0 <= int(msg.content) <= 15:
                bad_value = True
        except TypeError or ValueError:
            bad_value = True
        return msg.author == self.ctx.author and msg.channel == self.ctx.channel and not bad_value
    
    def new_or_show_lib(self, msg: discord.Message):
        bad_value = True
        print('TEST3', self.ctx, type(self.ctx))
        try:
            if msg.content.strip().lower() == 'new' or 'lib':
                bad_value = False
        except TypeError or ValueError:
            pass
        return msg.author == self.ctx.author and msg.channel == self.ctx.channel and not bad_value
    
    def game_selection(self, msg: discord.Message):
        bad_value = False
        try:
            if int(msg.content) not in [game.game_id for game in data.games_cache]:
                bad_value = True
        except TypeError or ValueError:
            bad_value = True
        return msg.author == self.ctx.author and msg.channel == self.ctx.channel and not bad_value
