import time
import re


class Client(object):
    NEWLINE = "\n"

    def __init__(self, connection):
        self.connection = connection
        self.state = "login_username"
        self.init()

    def init(self):
        pass

    def get_game(self):
        server = self.connection.server
        return server.game

    def handle_input(self, message):
        from settings import DEBUG_INPUT_TIMING

        game = self.get_game()
        method_name = "handle_{}_input".format(self.state)

        if DEBUG_INPUT_TIMING:
            time_started = time.time()

        message = self.filter_input(message)

        method = getattr(self, method_name)
        game.inject(method, message=message)

        if DEBUG_INPUT_TIMING:
            duration = time.time() - time_started
            self.writeln("Input execution time: %0.5f seconds" % duration)

    def quit(self):
        """Quit the game."""
        connection = self.get_connection()
        connection.close()

    def echo(self, *args, **kwargs):
        self.writeln(*args, **kwargs)

    def writeln(self, message=""):
        self.write(message + self.NEWLINE)

    def write(self, message=""):
        if not self.connection:
            return

        message = self.filter_output(message)
        self.connection.write(message)

    def filter_swears(self, message):
        # TODO filter out colors? {Rs{Gw{Ge{Ba{Rr -> {R*****
        # TODO split swear words into a service/injector of some kind
        from settings import SWEAR_WORDS
        from settings import SWEAR_WORDS_REPLACE_SYMBOL
        from settings import SWEAR_WORDS_IGNORE_CHARS
        from utils.ansi import Ansi

        # Strip out symbols that complicate things
        stripped = Ansi.decolorize(message)
        for char in SWEAR_WORDS_IGNORE_CHARS:
            stripped = stripped.replace(char, " ")

        # Make unique list
        words = set(stripped.lower().split(" "))

        # TODO Performance test this
        # Replace out swears, as they're found
        for word in words:
            word_is_swear = word in SWEAR_WORDS
            if word_is_swear:
                length = len(word)
                replacement = (SWEAR_WORDS_REPLACE_SYMBOL * length)[:length]

                pattern = re.compile(re.escape(word), re.IGNORECASE)

                message = pattern.sub(replacement, message)

        return message

    def filter_input(self, message):
        """Filter out swear words and other things from Player input."""
        return self.filter_swears(message)

    def filter_output(self, message):
        """Filter out swear words and other things for Player output."""
        return self.filter_swears(message)
