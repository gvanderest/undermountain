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


class TelnetClient(object):
    """Wrapper for how our Game works."""
    def handle_input(self, message):
        pass


class Connection(object):
    NEWLINE = "\n"
    NEWLINE_REPLACE = "\n\r"
    DEBUG = False
    UNIQUE_ID = 0

    def __init__(self, server):
        self.id = self.get_unique_id()  # Connection-wide unique identifier
        self.server = server  # Which server is this Connection attached to?
        self.actor = None  # Who is the Player controlling?

        self.output_buffer = ""  # Output going to Player
        self.input_buffer = ""  # Commands from the Player

        self.client = TelnetClient(self)

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

    def get_next_command(self):
        """Return the line for the next command."""
        if self.NEWLINE not in self.input_buffer:
            return None

        # TODO Improve performance here with str-only operations
        parts = self.input_buffer.split(self.NEWLINE)
        command = parts.pop(0)
        self.input_buffer = self.NEWLINE.join(parts)
        return command

    def handle_next_command(self):
        """Handle the next message in the input_buffer."""
        command = self.get_next_command()
        if command is not None:
            return self.handle_command(command)

    def handle_command(self, command):
        """Handle a command being provided."""
        logging.info("TELNET: " + command)
        for connection in self.server.connections:
            if connection is not self:
                connection.writeln(command)

    def write(self, message):
        """Write to the output_buffer."""
        if self.DEBUG:
            logging.debug("DEBUG WRITE: " + repr(message))
        self.output_buffer += message

    def writeln(self, message):
        """Write a line to the output_buffer."""
        self.write(message + self.NEWLINE)

    def flush(self, message):
        """Flush the message to the socket, clearing the buffer is handled
           elsewhere."""
        raise Exception("Not yet implemented")

    def start(self):
        self.running = True
        while self.running:
            message = self.read()

            if message is None:
                self.destroy()
                break

            self.receive(message)
            gevent.sleep(0.1)

    def destroy(self):
        self.stop()
        self.server.remove_connection(self)

    def stop(self):
        self.running = False

    def clear_output_buffer(self):
        self.output_buffer = ""


class TelnetConnection(Connection):
    READ_SIZE = 1024
    DEBUG = True

    def __init__(self, socket, addr, *args, **kwargs):
        super(TelnetConnection, self).__init__(*args, **kwargs)

        self.socket = socket  # Raw socket

        self.ip = addr[0]  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def read(self):
        message = self.socket.recv(self.READ_SIZE)
        if not message:
            return None
        message = message.decode("utf-8").replace("\r\n", "\n")
        return message

    def flush(self, message):
        self.socket.sendall(message)


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

    def add_connection(self, connection):
        """Add the Connection to the list."""
        # TODO register Connection with Game
        self.connections.append(connection)

    def remove_connection(self, connection):
        """Remove the Connection from the list."""
        # TODO unregister Connection with Game
        self.connections.remove(connection)

    def handle_new_connection(self, sock, addr):
        logging.info("New telnet connection from {}:{}".format(*addr))
        connection = TelnetConnection(sock, addr, self)
        self.add_connection(connection)
        connection.start()

    def accept_port_connections(self, port):
        while self.running:
            sock, addr = port.accept()
            gevent.spawn(self.handle_new_connection, sock, addr)
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

        while self.running:
            for connection in self.connections:
                connection.handle_next_command()
                connection.handle_flushing_output()
            gevent.sleep(0.01)

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

    def tick(self):
        logging.info("Number of Telnet connections: {}".format(
            len(self.connections))
        )


class Telnet(Module):
    MODULE_NAME = "Telnet"
    VERSION = "0.1.0"

    MANAGERS = [
        TelnetManager,
    ]
