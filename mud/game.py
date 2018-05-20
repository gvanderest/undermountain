from datetime import datetime
from logging.handlers import RotatingFileHandler
from mud.inject import inject

import gevent
import importlib
import logging
import settings
import traceback


logger = logging.getLogger()
FORMAT = "%(asctime)-15s [%(levelname)s] " + \
    "%(filename)s.%(funcName)s:%(lineno)s %(message)s"
formatter = logging.Formatter(FORMAT)

logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

log_file = RotatingFileHandler("log/undermountain.log")
log_file.setFormatter(formatter)
logger.addHandler(log_file)


class InvalidInjector(Exception):
    pass


class Game(object):
    def __init__(self):
        self.data = {}
        self.injectors = {}
        self.modules = []
        self.managers = []
        self.connections = {}
        self.commands = {}
        self.start_date = datetime.now()

        self.import_modules_from_settings()

    @property
    def game(self):
        return self

    def handle_exception(self, exception):
        output = traceback.format_exc()
        logging.error(output)

        escaped = output.replace("{", "{{")
        self.wiznet("exception", "Exception: {}".format(escaped))

    def wiznet(self, type, message, exclude=None):
        self.echo("{{Y--> {{x{}{{x".format(message), exclude=exclude)

    def trigger(self, *args, **kwargs):
        logging.debug("Global triggered {} {}".format(args, kwargs))

    def echo(self, message, exclude=None):
        """Send a message to all players."""
        if not exclude:
            exclude = []

        for conn in self.connections.values():
            actor = conn.client.actor
            if not actor:
                continue

            if actor in exclude:
                continue

            actor.echo(message)

    def import_modules_from_settings(self):
        for class_path in settings.MODULES:
            self.register_module(class_path)

    def import_class_path(self, path):
        parts = path.split(".")

        module_path = ".".join(parts[:-1])
        class_name = parts[-1]

        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def register_command(self, name, command):
        self.commands[name] = {"handler": command}
        return command

    def register_module(self, module_path):
        module_class = self.import_class_path(module_path)
        instance = module_class(self)
        self.modules.append(instance)
        return instance

    def register_manager(self, manager):
        instance = manager(self)
        self.managers.append(instance)
        logging.info("Registered manager {}".format(
            instance.__class__.__name__))
        return instance

    def register_injector(self, injector):
        instance = injector(self)
        self.injectors[injector.__name__] = instance
        logging.info("Registered injector {}".format(
            instance.__class__.__name__))
        return instance

    def get_injector(self, name):
        if name not in self.injectors:
            raise InvalidInjector(
                "{} is not a valid injector name".format(name))
        return self.injectors[name]

    def get_injectors(self, *names):
        return map(self.get_injector, names)

    @inject("Areas")
    def broadcast(self, type, data=None, unblockable=False, Areas=None):
        event = None
        for area in Areas.query():
            event = area.broadcast(type, data=data, unblockable=unblockable)
        return event

    @inject("Rooms")
    def start(self, Rooms):
        self.running = True

        for manager in self.managers:
            manager.start()

        self.broadcast("after:spawn")

        while self.running:
            gevent.sleep(1.0)

    def stop(self):
        self.running = False
