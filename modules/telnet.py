"""
TELNET MODULE
"""
import logging
import gevent
import socket
import gevent.monkey
from mud.module import Module
from mud.manager import Manager

gevent.monkey.patch_socket()


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

    def start(self):
        self.running = True
        while self.running:
            message = self.read()
            print(message)
            self.receive(message)
            gevent.sleep(0.1)

    def stop(self):
        self.running = False

class TelnetConnection(Connection):
    READ_SIZE = 1024

    def __init__(self, socket, addr):
        super(TelnetConnection, self).__init__()

        self.socket = socket  # Raw socket

        self.ip = addr[0]  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def read(self):
        message = self.socket.recv(self.READ_SIZE)
        return message.decode("utf-8")

    def flush(self):
        self.socket.sendall(self.output_buffer)
        self.output_buffer = ""


class TelnetManager(Manager):
    HANDLE_EVENTS = [
        "GAME_TICK"
    ]

    def init(self):
        self.ports = []
        self.connections = []

    def create_server(self, entry):
        """Create a port to listen on."""
        host = entry["host"]
        port = entry["port"]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)

        self.ports.append(sock)

        logging.info("Started telnet server: {}:{}".format(host, port))

    def handle_new_connection(self, connection, address):
        logging.info("New telnet connection from {}:{}".format(*address))
        upgraded = TelnetConnection(connection, address)
        self.connections.append(upgraded)
        # TODO register Connection with Game
        upgraded.start()

    def accept_port_connections(self, port):
        while self.running:
            connection, address = port.accept()
            gevent.spawn(self.handle_new_connection, connection, address)
            gevent.sleep(0.1)

    def start(self):
        """Instantiate the servers/ports and sockets."""
        super(TelnetManager, self).start()

        from settings import TELNET_PORTS

        self.running = True

        for entry in TELNET_PORTS:
            self.create_server(entry)

        for port in self.ports:
            gevent.spawn(self.accept_port_connections, port)

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
