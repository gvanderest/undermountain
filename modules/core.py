from mud.module import Module
# from mud.entity import Entity, Collection


class Character(object):
    @classmethod
    def get_clean_name(self, name):
        return name.strip().lower().title()[0:12]


class Injector(object):
    def __init__(self, game):
        self.game = game
        self.init()

    def get_game(self):
        return self.game


class SkipRecord(Exception):
    pass


class Characters(Injector):
    CLASSES = [Character]

    def init(self):
        self.characters = {}

    def query(self, spec=None):
        if spec is None:
            spec = {}

        for char in self.characters.values():
            try:
                for key, expected in spec.items():
                    if getattr(char, key, None) != expected:
                        raise SkipRecord()
                yield char
            except SkipRecord:
                continue

    def save(self, char):
        self.characters[char.name] = char

    def find(self, spec):
        for entity in self.characters.values():
            try:
                for key, value in spec.items():
                    entity_value = getattr(entity, key, None)
                    if entity_value != value:
                        raise SkipRecord()
            except SkipRecord:
                continue

            return entity


class Core(Module):
    def init(self):
        self.game.add_injector(Characters)
