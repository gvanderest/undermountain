from logging.handlers import RotatingFileHandler

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
logger.setLevel(logging.DEBUG)

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

        self.import_modules_from_settings()

    def handle_exception(self, exception):
        output = traceback.format_exc().replace("{", "{{")
        logging.error(output)
        self.echo("{{Y--> {{xException: {}".format(output))

    def echo(self, message):
        """Send a message to all players."""
        for conn in self.connections.values():
            conn.client.actor.echo(message)

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

    def register_module(self, module_path):
        module_class = self.import_class_path(module_path)
        instance = module_class(self)
        self.modules.append(instance)

    def register_manager(self, manager):
        instance = manager(self)
        self.managers.append(instance)
        logging.info("Registered manager {}".format(
            instance.__class__.__name__))

    def register_injector(self, injector):
        instance = injector(self)
        self.injectors[injector.__name__] = instance
        logging.info("Registered injector {}".format(
            instance.__class__.__name__))

    def get_injector(self, name):
        if name not in self.injectors:
            raise InvalidInjector(
                "{} is not a valid injector name".format(name))
        return self.injectors[name]

    def get_injectors(self, *names):
        return map(self.get_injector, names)

    def start(self):
        self.running = True

        for manager in self.managers:
            manager.start()

        while self.running:
            gevent.sleep(1.0)
            logging.debug("Tick.")

    def stop(self):
        self.running = False
