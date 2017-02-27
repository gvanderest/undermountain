"""
EXAMPLE MODULE
"""
from utils.entity import Entity
from utils.ansi import Ansi
from utils.collection import GameCollection, Index, CollectionEntity
from mud.module import Module
from mud.manager import Manager
from utils.listify import listify
import logging
import random


def walk_command(self, arguments):
    """Walk in a direction."""
    from settings import DIRECTIONS

    if not arguments:
        self.echo("Walk where?")
        return

    direction_id = arguments[0]
    direction = DIRECTIONS.get(direction_id, None)

    if direction is None:
        self.echo("You can't walk in that direction.")
        return

    room = self.get_room()
    exit = room.get_exit(direction_id)

    if exit is None:
        self.echo("You can't walk in that direction.")
        return

    target_room = exit.get_room()
    if target_room is None:
        raise Exception("Room does not exist for exit {} in room {}".format(
            direction_id,
            room.id
        ))

    self.set_room(target_room)
    self.save()
    self.handle_command("look")


def sockets_command(self):
    """List the socket Connections."""
    game = self.get_game()
    connections = game.get_connections()
    self.echo("[Port  Num Connected_State Login@ Idle] Player Name Host")
    self.echo("-" * 79)
    count = 0

    for conn in connections:
        count += 1
        state = "handshaking"
        actor_name = "UNKNOWN"
        client = conn.get_client()

        if client:
            state = client.state
            if client.actor:
                actor_name = client.actor.name

        self.echo("[%3d %15s %7s %3d] %s %s (%s) %s" % (
            count,
            state,
            "00:00XX",
            0,
            actor_name,
            conn.hostname,
            conn.ip,
            conn.TYPE
        ))

    self.echo()
    self.echo("%d users" % count)

def exception_command(self):
    """Raise an Exception."""
    raise Exception("Testing exception")


def title_command(self, arguments):
    if not arguments:
        self.echo("Change your title to what?")
        return

    if arguments[0] == "clear":
        self.title = ""
        self.echo("Your title has been cleared.")
    else:
        self.title = " ".join(arguments)
        self.echo("Your title has been set to: %s{x" % self.title)

    self.save()


def who_command(self, arguments, Characters):
    # FIXME Use Players injector instead, in the future
    total_count = 0
    visible_count = 0
    top_count = 999

    self.echo((" " * 15) + "{GThe Visible Mortals and Immortals of Waterdeep")
    self.echo("{g" + ("-" * 79))

    actors = list(Characters.query())
    actors = sorted(actors, key=lambda a: a.is_immortal(), reverse=True)
    for actor in actors:
        total_count += 1
        if not self.can_see(actor):
            continue

        visible_count += 1

        line = ""

        level_restring = actor.get("who_level_restring", None)
        if level_restring:
            line += level_restring + "{x"
        else:
            line += "{RIMM{x" if actor.is_immortal() else "{x  1{x"

        line += " "

        who_restring = actor.get("who_restring", None)
        if who_restring:
            line += who_restring
        else:
            gender_restring = actor.get("who_gender_restring", None)
            line += gender_restring if gender_restring else "{BM{x"

            line += " "

            race_restring = actor.get("who_race_restring", None)
            line += race_restring if race_restring else "{CH{cuman"

            line += " "

            class_restring = actor.get("who_class_restring", None)
            line += class_restring if class_restring else "{RA{rdv"

            line += " "

            clan_restring = actor.get("who_clan_restring", None)
            if clan_restring:
                line += clan_restring
            else:
                clan = actor.get_organization("clan")
                if not clan:
                    line += " " * 5
                else:
                    line += Ansi.pad_right(clan.who_name, 5)

        line += " "

        flag_restring = actor.get("who_flags_restring", None)
        if flag_restring:
            line += "{x[%s{x]" % flag_restring
        else:
            line += ("{x[...{BN{x......]{x" if actor.is_immortal()
                     else "  {x[.{BN{x......]{x")
        line += " "
        line += actor.name

        if actor.title:
            if actor.title[0] not in ",.":
                line += " "
            line += ("{x%s{x" % actor.title) if actor.title else ""

        for bracket in actor.get("who_brackets", []):
            line += (" {x[%s{x]" % bracket)

        self.echo(line)

    self.echo()
    self.echo(("{GPlayers found{g: {x%s   " % visible_count) +
              ("{GTotal online{g: {W%s   " % total_count) +
              ("{GMost on today{g: {x%s" % top_count))


def swear_command(self, arguments):
    self.echo("Testing swear filter: fuck Fuck FUCK fUcK fuCK? !!Fuck!!")


LOOK_ACTOR_FLAGS = (
    ("y", "V", "invisible"),
    ("8", "H", "hiding"),
    ("c", "C", "charmed"),
    ("b", "T", "pass_door"),
    ("w", "P", "faerie_fire"),
    ("C", "I", "iceshield"),
    ("r", "I", "fireshield"),
    ("B", "L", "shockshield"),
    ("R", "E", "evil"),
    ("Y", "G", "good"),
    ("W", "S", "sanctuary"),
    ("G", "Q", "immortal_quest"),
)


def look_command(self, arguments, Characters):
    from settings import DIRECTIONS

    def format_actor_flags(actor):
        flag_found = False
        flags = ""
        for color, symbol, flag_id in LOOK_ACTOR_FLAGS:
            if not actor.has_flag(flag_id):
                symbol = "."
            else:
                flag_found = True
            flags += "{%s%s" % (color, symbol)

        if flag_found:
            return "{x[%s{x] " % flags
        return ""

    def format_actor(actor):
        return "%s%s is here" % (
            format_actor_flags(actor),
            actor.format_name_to(self)
        )

    if arguments:
        self.echo("Looking at players and things not yet supported.")
        return

    room = self.get_room()
    self.echo("{B%s{x" % room.name)

    for index, line in enumerate(room.description):
        if index == 0:
            self.echo("{x  " + line)
        else:
            self.echo(line)

    self.echo()

    basic_exits = []
    door_exits = []
    secret_exits = []

    for direction_id, direction in DIRECTIONS.items():
        exit = room.get_exit(direction_id)
        if not exit:
            continue

        if exit.is_door() and exit.is_closed():
            door_exits.append(direction["name"])

        else:
            basic_exits.append(direction["name"])

    line = ""
    line += "{x[{GExits{g:{x %s{x]" % (
        " ".join(basic_exits) if basic_exits else "none"
    )
    line += "   "
    line += "{x[{GDoors{g:{x %s{x]" % (
        " ".join(door_exits) if door_exits else "none"
    )
    self.echo(line)

    players = list(Characters.query())

    for player in players:
        if player == self:
            continue
        self.echo(format_actor(player))


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


def quit_command(self, arguments, Characters):
    self.echo("You are quitting.")
    client = self.get_client()
    client.quit()


def me_command(self, arguments):
    message = " ".join(arguments)
    self.gecho(message, emote=True)


class RoomEntity(CollectionEntity):
    def set_room(self, room):
        """Set the Room for the RoomEntity."""
        self.room_id = room.id

    def get_room(self):
        Rooms = self.get_injector("Rooms")
        return Rooms.find(self.room_id)

    def has_flag(self, flag_id):
        """Return whether this Entity has a flag applied or not."""
        return random.randint(0, 10) == 1


class Area(CollectionEntity):
    pass


class Areas(GameCollection):
    WRAPPER_CLASS = Area

    NAME = "areas"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
    ]


class RoomExit(Entity):
    def __init__(self, data, room, parent_room):
        super(RoomExit, self).__init__(data)
        self._room = room
        self._parent_room = parent_room

    def get_room(self):
        """Return the Room."""
        return self._room

    def get_flags(self):
        """Return list of flags."""
        return self.get("flags", [])

    def has_flag(self, flag_id):
        """Return whether the flag is present."""
        return flag_id in self.get_flags()

    def is_door(self):
        """Return whether exit is a door or not."""
        return self.has_flag("door")

    def is_closed(self):
        """Return whether exit is closed or not."""
        return self.has_flag("closed")

    def is_open(self):
        """Return whether exit is open or not."""
        return not self.is_closed()


# class RoomExits(GameCollection):
#     WRAPPER_CLASS = RoomExit
#
#     NAME = "room_exits"
#     INDEXES = [
#         Index("id", required=True, unique=True),
#         Index("direction_id"),
#         Index("room_id"),
#     ]


class Room(CollectionEntity):
    def get_area(self):
        Areas = self.get_injector("Areas")
        return Areas.find(self.area_id)

    def get_exits(self):
        """Return dict of exits."""
        return self.get("exits", {})

    def get_exit(self, direction_id):
        """Return a RoomExit."""
        Rooms = self.get_injector("Rooms")

        exits = self.get_exits()
        raw_exit = exits.get(direction_id, None)
        if not raw_exit:
            return None

        exit_room = Rooms.get(raw_exit["room_id"])
        return RoomExit(raw_exit, exit_room, self)


class Rooms(GameCollection):
    WRAPPER_CLASS = Room

    NAME = "rooms"
    INDEXES = [
        Index("id", required=True, unique=True),
        Index("name", required=True, unique=True),
        Index("area_id"),
    ]


class Organization(Entity):
    pass


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
        "quit": quit_command,
        "me": me_command,
        "swear": swear_command,
        "title": title_command,
        "exception": exception_command,
        "sockets": sockets_command,
        "who": who_command,
        "walk": walk_command,
    }

    def get_organization(self, type_id):
        """Return the Organization of a type."""
        from settings import ORGANIZATIONS

        organization_id = self.get_organization_id(type_id)

        if not organization_id:
            return None

        org = ORGANIZATIONS.get(organization_id, None)
        if not org:
            return None

        return Organization(org)

    def get_organization_id(self, type_id):
        """Return the Organization ID that matches the requested type."""
        return self.get_organization_ids().get(type_id, None)

    def get_organization_ids(self):
        """Return the key/value pairs of Organizations."""
        return self.get("organizations", {})

    def can_see(self, target):
        """Return whether this Actor can see target Entity."""
        return True

    def is_visible_to(self, target):
        """Return whether this Actor is visible to the target Entity."""
        return target.can_see(self)

    def format_name_to(self, target):
        """Format the name of an Actor to another target, taking visibility
           into account."""
        if target.can_see(self):
            return self.name
        return "Someone"

    def set_client(self, client):
        self._client = client

    def get_client(self):
        return self._client

    def echo(self, message=""):
        client = self.get_client()
        if client is None:
            return
        client.writeln(message)

    def act_around(self, message, *args, **kwargs):
        self.gecho(message, *args, **kwargs)

    def gecho(self, message, exclude=None):
        exclude = listify(exclude)

        game = self.get_game()
        connections = game.get_connections()
        for conn in connections:
            client = conn.get_client()
            actor = client.get_actor()

            if actor is None:
                continue

            if actor in exclude:
                continue

            actor.echo(message)

    def get_aliases(self):
        return {}

    def get_game(self):
        client = self.get_client()
        if not client:
            return None
        return client.get_game()

    def quit(self):
        client = self.get_client()
        client.quit()

    def handle_command(self, message, ignore_aliases=False):
        from settings import DIRECTIONS

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

        handler = None

        for direction_id in DIRECTIONS.keys():
            if direction_id.startswith(command):
                handler = walk_command
                arguments = (direction_id,)
                break

        # Try to find a suitable command handler
        if handler is None:
            for key, method in self.COMMAND_HANDLERS.items():
                if key.startswith(command):
                    handler = method
                    break

        # Execute the appropriate code
        if handler is None:
            self.echo("Huh?")
            return

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
    def is_immortal(self):
        return self.name == "Kelemvor"


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
        # "RoomExits": RoomExits,
        "Actors": Actors,
        "Characters": Characters,
    }

    MANAGERS = [
        ExampleManager,
    ]
