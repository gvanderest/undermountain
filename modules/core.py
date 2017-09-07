from mud.module import Module
# from mud.entity import Entity, Collection


class Character(object):
    pass


class Injector(object):
    def __init__(self, game):
        self.game = game
        self.init()

    def get_game(self):
        return self.game


class Characters(Injector):
    CLASSES = [Character]

    def init(self):
        self.characters = {}

    def query(self, *args, **kwargs):
        return self.characters.values()

    def save(self, char):
        self.characters[char.name] = char


class Core(Module):
    def init(self):
        self.game.add_injector(Characters)
