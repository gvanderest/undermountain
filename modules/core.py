"""
EXAMPLE MODULE
"""
from utils.collection import GameCollection, Index, CollectionEntity
from mud.module import Module
from mud.manager import Manager
from utils.listify import listify
import logging


def swear_command(self, arguments):
    self.echo("Testing swear filter: fuck")


def look_command(self, arguments, Characters):
    if arguments:
        self.echo("Looking at players and things not yet supported.")
        return

    players = list(Characters.query())
    if not players:
        self.echo("You do not see anyone here.")
        return

    for player in players:
        self.echo("%s{x is here." % player.format_name_to(self))


def say_command(self, arguments):
    if not arguments:
        self.echo("Say what?")
        return

    message = " ".join(arguments)

    self.echo("{MYou say {x'{m%s{x'" % message)
    self.act_around(
        "{M%s says {x'{m%s{x'" % (self.name, message),
        exclude=self
    )


def no_handler(self, arguments):
    self.echo("Huh?")


def quit_command(self, arguments):
    self.echo("You are quitting.")
    self.quit()


def me_command(self, arguments):
    message = " ".join(arguments)
    self.gecho(message, emote=True)


class RoomEntity(CollectionEntity):
    def get_room(self):
        Rooms = self.get_injector("Rooms")
        return Rooms.find(self.room_id)


class Area(CollectionEntity):
    pass


class Areas(GameCollection):
    WRAPPER_CLASS = Area

    NAME = "areas"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
    ]


class RoomExit(CollectionEntity):
    pass


class RoomExits(GameCollection):
    WRAPPER_CLASS = RoomExit

    NAME = "room_exits"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("direction_id"),
        Index("room_id"),
    ]


class Room(CollectionEntity):
    def get_area(self):
        Areas = self.get_injector("Areas")
        return Areas.find(self.area_id)


class Rooms(GameCollection):
    WRAPPER_CLASS = Room

    NAME = "rooms"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("area_id"),
    ]


class Actor(RoomEntity):
    # TODO move commands and handlers/logic out into their own places
    ONE_CHAR_ALIASES = {
        "'": "say",
        "/": "recall",
        "=": "cgossip",
        "?": "help",
    }
    COMMAND_HANDLERS = {
        "look": look_command,
        "say": say_command,
        "say": say_command,
        "quit": quit_command,
        "me": me_command,
        "swear": swear_command,
    }

    def format_name_to(self, target):
        """Format the name of an Actor to another target, taking visibility
           into account."""
        return self.name

    def set_connection(self, connection):
        self._connection = connection

    def get_connection(self):
        return self._connection

    def get_client(self):
        connection = self.get_connection()
        if not connection:
            return None

        return connection.get_client()

    def echo(self, message):
        client = self.get_client()
        if client is None:
            return
        client.writeln(message)

    def act_around(self, message, *args, **kwargs):
        self.gecho(message, *args, **kwargs)

    def gecho(self, message, exclude=None):
        exclude = listify(exclude)

        connection = self._connection
        if connection is None:
            return

        connections = connection.server.game.connections
        for conn in connections:
            actor = conn.actor
            if actor is None:
                continue

            if actor in exclude:
                continue

            actor.echo(message)

    def get_aliases(self):
        return {}

    def get_game(self):
        return self._connection.server.game

    def quit(self):
        self._connection.stop()

    def handle_command(self, message, ignore_aliases=False):
        message = message.rstrip()

        if not message:
            return

        if not ignore_aliases:
            # Handle a one-character alias prefix
            possible_aliases = "".join(self.ONE_CHAR_ALIASES.keys())
            if message[0] in possible_aliases:
                existing = message
                message = self.ONE_CHAR_ALIASES[existing[0]]
                if existing[1:]:
                    message += " " + existing[1:]

            # Handle player aliases
            aliases = self.get_aliases()
            parts = message.split(" ")
            if parts[0] in aliases:
                parts = aliases[parts[0]].split(" ") + parts[1:]

        command = parts.pop(0).lower()
        arguments = tuple(parts)

        # Try to find a suitable command handler
        handler = no_handler
        for key, method in self.COMMAND_HANDLERS.items():
            if key.startswith(command):
                handler = method
                break

        # Execute the appropriate code
        if handler is None:
            self.echo("Huh?")
        else:
            game = self.get_game()
            try:
                game.inject(handler, _self=self, arguments=arguments)
            except Exception as e:
                game.handle_exception(e)
                self.echo("Huh?!  (Code bug detected and reported.)")


class Actors(GameCollection):
    WRAPPER_CLASS = Actor

    NAME = "actor"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("room_id"),
    ]


class Character(Actor):
    pass


class Characters(Actors):
    WRAPPER_CLASS = Character

    NAME = "characters"


class ExampleManager(Manager):
    HANDLE_EVENTS = [
        "GAME_TICK",
    ]

    def tick(self, Characters, Rooms, Areas):
        return
        chars = Characters.query({
            "room_id": "market_square",
        })

        logging.debug("Characters in room market_square:")
        if chars:
            for char in chars:
                count = char.get("count", 0)
                count += 1
                char.count = count
                char.save()
                room = char.get_room()
                area = room.get_area()
                logging.debug("* {} - {} - {} - {}".format(
                    char.name,
                    room.name,
                    area.name,
                    char.count
                ))
        else:
            print("No characters")


class Entities(GameCollection):
    pass


class Core(Module):
    MODULE_NAME = "Core"
    VERSION = "0.1.0"

    INJECTORS = {
        "Areas": Areas,
        "Rooms": Rooms,
        "RoomExits": RoomExits,
        "Actors": Actors,
        "Characters": Characters,
    }

    MANAGERS = [
        ExampleManager,
    ]
