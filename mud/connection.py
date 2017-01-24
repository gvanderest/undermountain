import gevent
import logging

class Connection(object):
    NEWLINE = "\n"
    NEWLINE_REPLACE = "\n\r"
    DEBUG = False
    UNIQUE_ID = 0

    def __init__(self, server):
        self.clean_shutdown = False  # Are we in the middle of a clean shutdown

        self.id = self.get_unique_id()  # Connection-wide unique identifier
        self.server = server  # Which server is this Connection attached to?
        self.actor = None  # Who is the Player controlling?

        self.output_buffer = ""  # Output going to Player
        self.input_buffer = ""  # Commands from the Player

        self.client = None  # Interpreter for Connection

        self.ip = ""  # Connection IP
        self.hostname = ""  # Connection hostname
        self.port = -1  # Connection port

    @classmethod
    def get_unique_id(cls):
        """Return a unique ID to identify this Connection."""
        cls.UNIQUE_ID += 1
        return str(cls.UNIQUE_ID)

    def read(self):
        """
        Read from raw socket.
        @returns {unicode} The input from the socket or None if error
        """
        raise Exception("Not yet implemented")

    def receive(self, message):
        """Write a line to the input_buffer."""
        if self.DEBUG:
            logging.debug("DEBUG RECEIVE: " + repr(message))
        self.input_buffer += message

    def handle_flushing_output(self):
        """Push output_buffer to socket if present."""
        if not self.output_buffer:
            return
        self.flush(self.output_buffer)
        self.output_buffer = ""

    def get_next_input(self):
        """Return the line for the next command."""
        if self.NEWLINE not in self.input_buffer:
            return None

        # TODO Improve performance here with str-only operations
        parts = self.input_buffer.split(self.NEWLINE)
        message = parts.pop(0)
        self.input_buffer = self.NEWLINE.join(parts)
        return message

    def handle_next_input(self):
        """Handle the next message in the input_buffer."""
        message = self.get_next_input()
        if message is not None:
            return self.handle_input(message)

    def handle_input(self, command):
        """Handle an input being provided."""
        if self.DEBUG:
            logging.debug("DEBUG INPUT: " + command)
        self.client.handle_input(command)

    def write(self, message):
        """Write to the output_buffer."""
        if self.DEBUG:
            logging.debug("DEBUG WRITE: " + repr(message))
        self.output_buffer += message

    def writeln(self, message=""):
        """Write a line to the output_buffer."""
        self.write(message + self.NEWLINE)

    def flush(self, message):
        """Flush the message to the socket, clearing the buffer is handled
           elsewhere."""
        raise Exception("Not yet implemented")

    def start(self):
        self.running = True
        self.client.start()
        while self.running:
            message = self.read()

            if message is None:
                break

            self.receive(message)
            gevent.sleep(0.1)

    def stop(self, clean=False):
        self.running = False
        self.clean_shutdown = clean
        self.close()
        self.server.remove_connection(self)

    def clear_output_buffer(self):
        self.output_buffer = ""
