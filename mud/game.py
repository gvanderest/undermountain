"""
GAME
The World in which we play.
"""
import gevent
import inspect
import logging
import sys
import traceback
from settings import DATA_PATH
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
        self.state["actors"] = {}
        self.state["actors"]["abc123"] = {
            "room_id": "0b7360121a97cc0ca78f211be86592ff0043b7c3",
            "room_vnum": "westbridge:3001",
            "keywords": "tchazzar",
            "name": "{8Tchazzar, {rthe Dragon Queen",
            "room_name": "{8Tchazzar, {rThe Dragon Queen{x rests on her throne here.",
            "description": [
                "This is the biggest dragon you have ever seen. It has five heads, one of",
                "each chromatic dragon color.",
            ],
            "subroutines": {
                "dying": [
                    """
self.say("One cannot die in this room.")
event.block()
target.set_stat_base("current_hp", 100)
                    """
                ],
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

        self.running = False
        self.modules = []
        self.injectors = {}
        self.managers = []
        self.connections = []

        self.set_modules(modules)

    def get_data_path(self):
        """Return the folder path to the DATA directory."""
        return DATA_PATH

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
