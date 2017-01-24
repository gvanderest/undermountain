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

    def __init__(self, modules=None, injectors=None, logging=False):
        ms_desc = [
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
            "areas": {
                "westbridge": {
                    "name": "Westbridge City",
                },
            },
            "rooms": {
                "market_square": {
                    "name": "Market Square",
                    "description": ms_desc,
                    "area_id": "westbridge",
                }
            },
            "characters": {
                "xyz321": {
                    "name": "Torog",
                    "room_id": "market_square",
                },
                "abc123": {
                    "name": "Kelemvor",
                    "room_id": "market_square",
                },
            }
        }
        self.running = False
        self.modules = []
        self.logging = False
        self.injectors = {}
        self.managers = []
        self.connections = []

        self.set_modules(modules)
        self.set_logging(logging)

    def handle_exception(self, e):
        """Handle an Exception and report appropriately."""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted = "".join(traceback.format_exception(
            exc_type,
            exc_value,
            exc_traceback
        ))
        logging.error("EXCEPTION: " + formatted)
        self.wiznet("exception", formatted)

    def wiznet(self, type, message):
        """Display a wiznet message to Players."""
        for connection in self.connections:
            actor = connection.actor
            if actor is None:
                continue
            actor.echo("{Y-->{x %s" % (message))

    def add_connection(self, connection):
        """Add a Connection to the Game."""
        self.connections.append(connection)

    def remove_connection(self, connection):
        """Remove a Connection from the Game."""
        self.connections.remove(connection)

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

    def set_logging(self, logging):
        """Set the logging flag to a value."""
        self.logging = logging

    def shutdown(self):
        """Stop any processes/modules that are running."""
        self.running = False

    def inject(self, method, overrides=None, async=False):
        """
        Call a function with injectors hydrated.  Additional injectors can be
        provided as a dictionary.

        Method args such as self, args, and kwargs, are completely ignored.

        @param {function} method to be called
        @param {dict} [overrides=None] to add/override existing game injectors
        @returns {*} result of the method call
        """
        injectors = dict(self.injectors)

        if overrides is not None:
            injectors.update(overrides)

        arg_names = inspect.getargspec(method)[0]
        if arg_names and arg_names[0] in ["self"]:
            arg_names.pop(0)

        values = []
        for name in arg_names:
            try:
                values.append(injectors[name])
            except KeyError as e:
                # TODO use a better exception type?
                raise Exception("Injector '{}' not found".format(name))

        if async:
            return gevent.spawn(lambda: method(*values))
        return method(*values)

    def dispatch(self, event_type, data=None):
        if data is None:
            data = {}

        event = Event(event_type, data)

        for manager in self.managers:
            # Skip past any unhandled events, if list provided
            if manager.HANDLE_EVENTS is not None:
                if event.type not in manager.HANDLE_EVENTS:
                    continue

            event = self.inject(manager.handle_event, {"event": event})
            if event.is_blocked():
                break

        return event

    def start(self):
        """Start the Game loop."""
        self.running = True
        self.dispatch("GAME_STARTED")

        for manager in self.managers:
            self.inject(manager.start, async=True)

        while self.running:
            # FIXME Move this into unique threads for Managers, for now, this
            # fits, but is not pretty.
            for manager in self.managers:
                self.inject(manager.tick)
            gevent.sleep(1.0)

        for manager in self.managers:
            self.inject(manager.stop, async=True)

        self.dispatch("GAME_STOPPED")

    def stop(self):
        self.running = False
