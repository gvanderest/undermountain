import gevent
import glob
import logging
import random
import settings


class Client(object):
    INITIAL_STATE = "null"

    def __init__(self, connection):
        self.connection = connection
        self.inputs = []
        self.parse_thread = None
        self.state = self.INITIAL_STATE

        self.prompt_disabled = False

        self.proxy_commands = []
        self.proxy_contexts = []
        self.proxy_callbacks = []
        self.proxy_prompts = []

        self.last_input = ""
        self.spam_count = 0

    @property
    def game(self):
        return self.connection.game

    def write_from_random_template(self, folder):
        """Read a random file from a data folder and output it."""
        path = "{}/{}".format(settings.DATA_FOLDER, folder)
        paths = glob.glob("{}/*".format(path))
        template_path = random.choice(paths)
        with open(template_path, "r") as fh:
            output = fh.read()
            self.write(output)

    def handle_inputs(self, inputs):
        if "clear" in inputs:
            self.inputs = []
            return

        self.inputs += inputs

        if not self.parse_thread:
            self.parse_thread = gevent.spawn(self.start_parse_thread)
        for input in inputs:
            logging.info("INPUT {}".format(input))

    def start_parse_thread(self):
        while self.inputs:
            message = self.inputs.pop(0)

            if message == "!":
                message = self.last_input
            else:
                self.last_input = message

            delay = self.handle_input(message)
            gevent.sleep(delay if delay else 0.3)
        self.parse_thread = None

    def handle_input(self, message):
        func_name = "handle_{}_input".format(self.state)
        func = getattr(self, func_name)
        return func(message)

    def write(self, message=""):
        self.connection.write(message)

    def writeln(self, message=""):
        self.write(message + "\n")
