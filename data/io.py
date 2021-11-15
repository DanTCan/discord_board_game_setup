import pickle
import os

games_cache = []
gl = os.path.join('data', 'games_library.pkl')


def pickle_loader(filename):
    with open(filename, 'rb') as fn:
        while 1:
            try:
                yield pickle.load(fn)
            except EOFError:
                break


try:
    generator = pickle_loader(gl)
    for pkl in generator:
        for game in pkl:
            games_cache.append(game)
    games_cache.sort(key=lambda x: x.game_id)
except FileNotFoundError:
    print('NOTHING SAVED YET!')


def save():
    with open(gl, 'wb') as f:
        pickle.dump(games_cache, f)
