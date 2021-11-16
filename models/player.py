class Player(object):
    def __init__(self, member):
        try:
            # if type(member) == discord.Member:
            self.name = member.name
        except AttributeError:
            # else:
            self.name = member

        self.game_role = None
        self.team = None
        self.turn = None
