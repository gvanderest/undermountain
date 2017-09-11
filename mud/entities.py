from mud.inject import inject
from utils.hash import get_random_hash


class Entity(object):
    def __init__(self, data=None, game=None):
        self.set_data(data)
        self.set_game(game)
        print("BOOP", self._data, self._game)

    def set_game(self, game):
        super(Entity, self).__setattr__("_game", game)

    def get_game(self):
        return self._game

    def get_data(self):
        return self._data

    def set_data(self, data=None):
        if data is None:
            data = {}
        self._data = data

    def __getattr__(self, key):
        return self._data.get(key, None)


def look_command(self):
    room = self.get_room()
    self.echo("{} [Room {}] [Id {}]".format(room.name, room.vnum, room.id))
    for index, line in enumerate(room.description):
        if index == 0:
            self.echo("  " + line)
        else:
            self.echo(line)

    self.echo()
    self.echo("[Exits: {}]   [Doors: {}]    [Secret: {}]".format(
        "none", "none", "none"))

    for obj in self.filter_visible(room.get_objects()):
        self.echo("     " + obj.get_room_display_name())

    for actor in self.filter_visible(room.get_actors()):
        if actor is self:
            continue
        self.echo(actor.get_room_display_name())

    self.echo()


def quit_command(self):
    self.online = False
    self.echo("You are quitting.")
    client = self.get_client()
    client.quit()


@inject("Characters")
def who_command(self, Characters):
    self.echo("""\
           The Visible Mortals and Immortals of Waterdeep
-----------------------------------------------------------------------------\
""")
    for char in Characters.query({"online": True}):
        parts = []
        parts.append("  1")
        parts.append("M")
        parts.append("Human")
        parts.append("Adv")
        parts.append("     ")
        parts.append("[........]")
        parts.append(char.name)
        if char.title:
            parts.append(char.title)
        if char.bracket:
            parts.append("[{}]".format(char.bracket))

        self.echo(" ".join(parts))

    self.echo()
    self.echo(
        "Players found: {}   "
        "Total online: {}   "
        "Most on today: {}"
        .format(
            0, 0, 0))


class CommandResolver(object):
    def __init__(self):
        self.commands = {}

    def add(self, keyword, handler):
        for partial in self.get_keyword_partials(keyword):
            if partial not in self.commands:
                self.commands[partial] = []

            self.commands[partial].append(handler)

    def remove(self, keyword, handler):
        for partial in self.get_keyword_partials(keyword):
            if partial not in self.commands:
                continue

            self.commands[partial].remove(handler)

            if not self.commands[partial]:
                del self.commands[partial]

    def get_keyword_partials(self, keyword):
        keyword = keyword.lower()

        for x in range(1, len(keyword) + 1):
            partial = keyword[:x]
            yield partial

    def query(self, keyword):
        return self.commands.get(keyword.lower(), [])


RESOLVER = CommandResolver()
RESOLVER.add("look", look_command)
RESOLVER.add("quit", quit_command)
RESOLVER.add("who", who_command)


class Room(Entity):
    def get_objects(self):
        yield Object({
            "id": get_random_hash(),
            "name": "a fountain",
            "long_name": "A large marble fountain stands here flowing with water.",
        })

    def get_game(self):
        return self._game

    @inject("Characters")
    def get_actors(self, Characters):
        for entities in (Characters,):
            for actor in entities.query({"room_id": self.id}):
                yield actor

    def has_exit(self, direction):
        return direction in self.get("exits", {})


class Actor(Entity):
    def gecho(self, line):
        game = self.get_game()
        for connection in game.get_connections():
            if connection is self.connection:
                continue
            connection.writeln("{}> {}".format(self.name, line))

    def force(self, line):
        self.handle_input(line)

    def handle_input(self, line):
        parts = line.split(" ")

        if not parts:
            self.echo("Huh?")
            return

        commands = RESOLVER.query(parts[0])
        if commands:
            commands[0](self=self)
        else:
            self.gecho(line)

    def echo(self, line=""):
        client = self.get_client()
        client.writeln(line)

    def can_see(self, entity):
        return True

    def filter_visible(self, collection):
        for entity in collection:
            if not self.can_see(entity):
                continue
            yield entity

    def get_room(self):
        game = self.get_game()
        return Room({
            "id": get_random_hash(),
            "area_vnum": "westbridge",
            "vnum": "market_square",
            "flags": [
                "law",
                "noloot",
                "city",
            ],
            "exits": {
                "north": None,
                "east": None,
                "south": None,
                "west": None,
                "up": None,
                "down": None,
            },
            "description": [
                "This place stands one of the greatest points in the realms, Market",
                "Square.  Market Square is the center point for the city of Westbridge,",
                "and also known to be the center point of the Western Great Realms.",
                "This area features a huge cobblestone square, crowned with a fountain",
                "and statue in the middle.  Park benches line the outer edges,",
                "allowing people to rest.  The center fountain stands tall, a statue in",
                "the middle of Nisstyre Bloodstoner with water flowing around the base.",
                "Several streets lead off different directions.  Going east and west",
                "from the square is Westbridge Way, a main route between the",
                "major cities.  To the west can be found the Bounty Hunters Office,",
                "Bakery and other shops.  To the east can be found The Quick-Mart and",
                "General Store.  Going north and south is Main Street of Westbridge.",
                "The Healing Wound Inn, and Questmasters Office is north, the Park and",
                "Bank South.  A large sign hangs in the corner of the square, pointing",
                "out the different shops.",
            ]
        }, game=game)


class Character(Actor):
    def get_game(self):
        return self._client.get_game()

    def get_client(self):
        return self._client

    def set_client(self, client):
        super(Entity, self).__setattr__("_client", client)

    def get_room_display_name(self):
        return "{} {} is here.".format(self.name, self.title)

    @classmethod
    def get_clean_name(self, name):
        return name.strip().lower().title()[0:12]


class Object(Entity):
    def get_room_display_name(self):
        return self.long_name


class Vehicle(Object):
    pass


class Item(Object):
    pass


class Equipment(Item):
    pass


class Consumable(Item):
    pass


class Potion(Consumable):
    pass


class Scroll(Consumable):
    pass


class Armor(Equipment):
    pass


class Weapon(Equipment):
    pass
