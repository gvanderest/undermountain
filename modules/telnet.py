"""
TELNET MODULE
"""
from mud.module import Module
from mud.manager import Manager
# from mud.connection import Connection
# import logging


class Connection(object):
    NEWLINE = "\n"
    NEWLINE_REPLACE = "\n\r"

    def __init__(self):
        self.actor = None  # Who is the Player controlling?

        self.output_buffer = ""  # Output going to Player
        self.input_buffer = ""  # Commands from the Player

        self.ip = ""  # Connection IP
        self.hostname = ""  # Connection hostname
        self.port = -1  # Connection port

    def read(self):
        """
        Read from raw socket.
        @returns {unicode} The input from the socket or None if error
        """
        raise Exception("Not yet implemented")

    def receive(self, message):
        """Write a line to the input_buffer."""
        self.input_buffer += message

    def handle_next(self, message):
        """Handle the next message in the input_buffer."""
        raise Exception("Not yet implemented")

    def write(self, message):
        """Write to the output_buffer."""
        self.output_buffer += message

    def writeln(self, message):
        """Write a line to the output_buffer."""
        self.write(message + self.NEWLINE)

    def flush(self):
        """Flush the output_buffer to the socket."""
        raise Exception("Not yet implemented")


class TelnetConnection(Connection):
    READ_SIZE = 1024

    def __init__(self, socket, addr):
        self.socket = socket  # Raw socket

        self.ip = addr[0]  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def read(self):
        message = self.socket.recv(self.READ_SIZE)
        return message

    def flush(self):
        self.socket.sendall(self.output_buffer)
        self.output_buffer = ""


class TelnetManager(Manager):
    def init(self):
        self.connections = []

    def start(self):
        pass

    def dehydrate(self):
        """Convert this into the dumbest data possible."""
        return {
            "connections": [conn.dehydrate() for conn in self.connections]
        }

    def hydrate(self, payload):
        """Convert dumb information into better."""
        self.connections = [
            TelnetConnection.hydrate(conn) for conn
            in payload["connections"]
        ]


class Telnet(Module):
    MODULE_NAME = "Telnet"
    VERSION = "0.1.0"

    MANAGERS = [
        TelnetManager,
    ]
