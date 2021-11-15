class Game(object):
    def __init__(self, game_name, container):
        title = game_name.title()
        if title not in [g.title for g in container]:
            self.title = title
        else:
            raise ValueError
        try:
            self.game_id = max([game.game_id for game in container]) + 1
        except ValueError:
            self.game_id = 1
        self.game_roles = None
        self.teams = None
        self.times_played = None
        self.min_players = int()
        self.max_players = int()

        container.append(self)
