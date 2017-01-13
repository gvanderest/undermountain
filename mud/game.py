"""
GAME
The World in which we play.
"""
import asyncio
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

        self.set_modules(modules)
        self.set_logging(logging)

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

    def dispatch(self, event_type, data=None):
        if data is None:
            data = {}

        event = Event(event_type, data)

        for manager in self.managers:
            if event.type not in manager.HANDLE_EVENTS:
                continue

            event = manager.handle_event(event)
            if event.is_blocked():
                break

        return event

    def start(self):
        """Start the Game loop."""
        self.running = True
        self.dispatch("GAME_STARTED")

        while self.running:
            self.dispatch("GAME_TICK")
            yield from asyncio.sleep(1.0)

        self.dispatch("GAME_STOPPED")
