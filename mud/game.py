"""
GAME
The World in which we play.
"""
import gevent
import inspect
import logging
import sys
import traceback
from utils.event import Event
from utils.ansi import Ansi


class Game(object):
    """An instance of the Game."""

    VERSION = None

    @classmethod
    def get_version(cls):
        """Return the version string."""
        if cls.VERSION is not None:
            return cls.VERSION

        with open("VERSION", "r") as fh:
            version = fh.read().strip()
            cls.VERSION = version

        return cls.VERSION

    def __init__(self, modules=None, injectors=None):
        self.state = {}

        if False:
            tol_desc = [
                "This is the interior of a large white marble temple.  A pipe "
                "organ",
                "plays in the background as people sing a hymn of peacefulness.  "
                "A",
                "priest up front tells the story of the forces of the realms, be "
                "it Life,",
                "the force that gives breath and a heartbeat, and Death, the "
                "force that",
                "steals these gifts away.  There is a guard standing watch, "
                "keeping the",
                "peace.  To the south is the Temple Square and to the west is "
                "the donation",
                "room.  To the east is the City Morgue and a newer section of "
                "Main Street",
                "heads off to the north.",
            ]
            self.state = {
                "actors": {
                    "abc123": {
                        "room_id": "tol123",
                        "keywords": "tchazzar",
                        "name": "{8Tchazzar, {rthe Dragon Queen",
                        "room_name": "{8Tchazzar, {rThe Dragon Queen{x rests on her throne here.",
                        "description": [
                            "This is the biggest dragon you have ever seen. It has five heads, one of",
                            "each chromatic dragon color.",
                        ],
                        "subroutines": {
                            "leaving": [
                                """
    if random(0, 1) == 1:
        self.say("Sorry {}, I feel like you should stick around.".format(target.name))
        event.block()
                                """,
                                "self.say('Seeya, {}!'.format(target.name))"
                            ],
                            "entered": [
                                "self.say('Hey there, {}!'.format(target.name))"
                            ]
                        }
                    }
                },
                "areas": {
                    "westbridge": {
                        "name": "Westbridge City",
                    },
                    "random_dungeon": {
                        "name": "Random Dungeon",
                    }
                },
                "objects": {},
                "rooms": {
                    "tol123": {
                        "id": "tol123",
                        "name": "The Temple of Life",
                        "vnum": "westbridge:temple_of_life",
                        "description": tol_desc,
                        "area_id": "westbridge",
                        "flags": [
                            "safe",
                            "law",
                            "noloot"
                        ],
                        "exits": {
                            "west": {"room_id": "donation_pit"},
                            "south": {"room_id": "temple_square"},
                        },
                    },
                    "donation_pit": {
                        "id": "donation_pit",
                        "name": "Donation Pit",
                        "vnum": "westbridge:donation_pit",
                        "area_id": "westbridge",
                        "exits": {
                            "east": {"room_id": "tol123"},
                        },
                    },
                    "temple_square": {
                        "id": "temple_square",
                        "name": "Temple Square",
                        "vnum": "westbridge:temple_square",
                        "area_id": "westbridge",
                        "exits": {
                            "north": {"room_id": "tol123"},
                            "east": {"room_id": "healing_wound_inn"},
                            "west": {"room_id": "church_steps"},
                            "south": {"room_id": "room_0"},
                        },
                    },
                    "healing_wound_inn": {
                        "id": "healing_wound_inn",
                        "name": "Healing Wound Inn",
                        "vnum": "westbridge:healing_wound_inn",
                        "area_id": "westbridge",
                        "exits": {
                            "west": {"room_id": "temple_square"},
                        },
                    },
                    "church_steps": {
                        "id": "church_steps",
                        "name": "The Steps of the Church",
                        "vnum": "westbridge:church_steps",
                        "area_id": "westbridge",
                        "exits": {
                            "east": {"room_id": "temple_square"},
                        },
                    },
                    "cop321": {
                        "id": "cop321",
                        "name": "Coliseum Of Pain",
                        "vnum": "westbridge:coliseum_entrance",
                        "description": [],
                        "area_id": "westbridge",
                        "exits": {
                            "up": {"room_id": "tol123"},
                        },
                    },
                },
            }

            # Makea lot of rooms
            rooms = 100
            for x in range(rooms):
                exits = {}
                if x > 0:
                    exits["north"] = {"room_id": "room_{}".format(x - 1)}
                else:
                    exits["north"] = {"room_id": "temple_square"}

                if x < rooms - 1:
                    exits["south"] = {"room_id": "room_{}".format(x + 1)}

                room_id = "room_{}".format(x)
                self.state["rooms"][room_id] = {
                    "id": room_id,
                    "area_id": "random_dungeon",
                    "vnum": room_id,
                    "name": "Room {}".format(x),
                    "description": [
                        "You're in room {}".format(x)
                    ],
                    "exits": exits
                }

            races = ["green_dragon", "red_dragon", "skeleton", "blue_dragon",
                     "white_dragon", "goblin", "dwarf", "drow", "elf", "human",
                     "pixie", "black_dragon"]
            import random
            actors = 100
            for x in range(actors):
                actor_id = "actor_{}".format(x)
                self.state["actors"][actor_id] = {
                    "id": actor_id,
                    "keywords": "actor {}".format(x),
                    "name": "Actor {}".format(x),
                    "room_name": "Actor {}".format(x),
                    "description": [],
                    "room_id": "room_{}".format(random.randint(0, rooms)),
                    "race_id": random.choice(races)
                }

            objects = 100
            for x in range(objects):
                object_id = "object_{}".format(x)
                self.state["objects"][object_id] = {
                    "id": object_id,
                    "name": "Object {}".format(x),
                    "room_id": "room_{}".format(random.randint(0, rooms)),
                    "description": []
                }

        self.running = False
        self.modules = []
        self.injectors = {}
        self.managers = []
        self.connections = []

        self.set_modules(modules)

    def get_actor_connection(self, actor):
        # FIXME Make this a dictionary
        for connection in self.connections:
            if connection.client.actor_id == actor.id:
                return connection

    def get_connections(self):
        """Return a list of Connections."""
        return self.connections

    def handle_exception(self, e):
        """Handle an Exception and report appropriately."""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted = "".join(traceback.format_exception(
            exc_type,
            exc_value,
            exc_traceback
        ))
        escaped = Ansi.escape(formatted)
        logging.error("EXCEPTION: " + escaped)
        self.wiznet("exception", escaped)

    def wiznet(self, type, message):
        """Display a wiznet message to Players."""
        for connection in self.connections:
            actor = connection.get_actor()
            if actor is None:
                continue
            actor.echo("{Y-->{x %s" % (message))

    def add_connection(self, connection):
        """Add a Connection to the Game."""
        self.connections.append(connection)
        logging.info("Added connection from {}({}):{}".format(
            connection.hostname,
            connection.ip,
            connection.port,
        ))

    def remove_connection(self, connection):
        """Remove a Connection from the Game."""
        self.connections.remove(connection)
        logging.info("Removed connection from {}({}):{}".format(
            connection.hostname,
            connection.ip,
            connection.port,
        ))

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def set_modules(self, modules):
        """Set the modules list to the provided list."""
        self.modules = []
        for module in modules:
            self.modules.append(module(self))

            for manager in module.MANAGERS:
                self.add_manager(manager)

            for name, cls in module.INJECTORS.items():
                self.add_injector(name, cls)

    def add_manager(self, manager):
        self.managers.append(manager(self))

    def add_injector(self, name, injector):
        self.injectors[name] = injector(self)

    def get_injector(self, name):
        """Return a single Injector."""
        return self.injectors[name]

    def get_injectors(self, *names):
        """Return a tuple of Injectors."""
        return tuple(map(self.get_injector, names))

    def shutdown(self):
        """Stop any processes/modules that are running."""
        self.running = False

    def inject_async(self, method, **kwargs):
        return gevent.spawn(self.inject, method, **kwargs)

    def inject(self, method, **overrides):
        """
        Call a function with injectors hydrated.  Additional injectors can be
        provided as a dictionary.

        Method args such as self, args, and kwargs, are completely ignored.

        @param {function} method to be called
        @param {dict} [overrides=None] to add/override existing game injectors
        @returns {*} result of the method call
        """
        # Make a copy of the injectors
        injectors = dict(self.injectors)

        if overrides is not None:
            injectors.update(overrides)

        arg_names = inspect.getargspec(method)[0]

        values = {}
        for name in arg_names:

            # Allow overriding of "_self"->"self" injector
            internal_name = name
            if name == "self":
                if "_self" not in injectors:
                    continue
                internal_name = "_self"

            try:
                values[name] = injectors[internal_name]
            except KeyError as e:
                raise KeyError("Injector '{}' in {} not found for {}".format(
                    name, arg_names, method))

        try:
            return method(**values)
        except Exception as e:
            self.handle_exception(e)
            return None

    def dispatch(self, event_type, data=None):
        if data is None:
            data = {}

        event = Event(event_type, data)
        event = self.handle_event(event)

        return event

    def handle_event(self, event):
        for manager in self.managers:
            # Skip past any unhandled events, if list provided
            if manager.HANDLE_EVENTS is not None:
                if event.type not in manager.HANDLE_EVENTS:
                    continue

            event = self.inject(manager.handle_event, event=event)
            if event is None:
                raise Exception("Manager {} did not return an Event from its"
                                "handle_event method".format(manager))
            if event.is_blocked():
                break

        return event

    def start(self):
        """Start the Game loop."""
        self.running = True
        self.dispatch("GAME_STARTED")

        for manager in self.managers:
            self.inject_async(manager.start)

        while self.running:
            # FIXME Move this into unique threads for Managers, for now, this
            # fits, but is not pretty.
            gevent.sleep(1.0)
            logging.info("Tick")
            for manager in self.managers:
                self.inject(manager.tick)

        for manager in self.managers:
            self.inject_async(manager.stop)

        self.dispatch("GAME_STOPPED")

    def stop(self):
        self.running = False
