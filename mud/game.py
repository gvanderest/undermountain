import gevent
import importlib
import logging
import settings


class Game(object):
    VERSION = None

    def __init__(self, settings):
        self.settings = settings
        self.connections = []
        self.injectors = {}
        self.managers = []
        self.modules = []
        self.handlers = {}
        self.running = False

        for module in self.settings.MODULES:
            self.add_module(module)

    @classmethod
    def get_version(cls):
        if cls.VERSION is None:
            try:
                cls.VERSION = list(open("VERSION", "r"))[0].strip()
            except:
                cls.VERSION = "UNKNOWN"

        return cls.VERSION

    def add_injector(self, injector):
        name = injector.__name__

        if name in self.injectors:
            raise Exception("Injector with name '{}' already added.".format(
                name))

        self.injectors[name] = injector(self)
        logging.info("Added injector {}".format(name))

    def get_injector(self, name):
        return self.injectors.get(name)

    def add_module(self, maybe_module):
        if isinstance(maybe_module, str):
            parts = maybe_module.split(".")
            mod = importlib.import_module(".".join(parts[:-1]))
            class_name = parts[-1]
            module = getattr(mod, class_name)
        else:
            module = maybe_module

        instance = module(self)
        self.modules.append(instance)

        logging.info("Loaded module {}".format(module.__name__))

    def add_manager(self, manager_class):
        self.managers.append(manager_class(self))

    def get_connections(self):
        return self.connections

    def add_connection(self, connection):
        print("SELF CONNECTIONS", self.connections, connection)
        self.connections.append(connection)

    def remove_connection(self, connection):
        print("REMOVING", self.connections, connection)
        self.connections.remove(connection)

    def start(self):
        logging.info("Starting Game..")
        self.running = True
        for manager in self.managers:
            logging.info("Starting Manager {}".format(
                manager.__class__.__name__))
            manager.start()
        logging.info("Game started")

        while self.running:
            gevent.sleep(settings.GAME_LOOP_TIME)
            for manager in self.managers:
                manager.tick()
            logging.info("Tick")

    def stop(self):
        logging.info("Stopping Game..")
        for manager in self.managers:
            logging.info("Stopping Manager {}".format(
                manager.__class__.__name__))
            manager.stop()
        logging.info("Game stopped")

        self.running = False
