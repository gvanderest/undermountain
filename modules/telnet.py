"""
TELNET MODULE
"""
import logging
import gevent
import socket
import gevent.monkey
from mud.module import Module
from mud.manager import Manager
from modules.core import Actor

gevent.monkey.patch_socket()


class Client(object):
    def __init__(self, connection):
        self.connection = connection
        self.write = connection.write
        self.writeln = connection.writeln
        self.state = "login_username"

    def handle_input(self, message):
        method_name = "handle_{}".format(self.state)

        method = getattr(self, method_name)
        method(message)

class TelnetClient(Client):
    """Wrapper for how our Game works."""

    def hide_next_input(self):
        self.write("<TODO HIDE> ")

    def start(self):
        self.write_login_banner()
        self.write_login_username_prompt()

    def write_login_banner(self):
        self.writeln("Waterdeep: City of Splendors")
        self.writeln()
        self.writeln("So far, what's implemented is essentially a groupchat.")

    def write_login_username_prompt(self):
        self.write("What is your name, adventurer? ")

    def handle_login_username(self, message):
        if not message:
            self.writeln("Please pick a name, even if it's short.")
            self.write_login_username_prompt()
            return
        self.state = "chatting"
        self.connection.actor = Actor({
            "name": message.lower().title()
        })
        actor = self.connection.actor
        self.writeln("Thanks for providing your name, {}!".format(actor.name))
        self.login()
        self.write_chatting_prompt()

    def write_login_password_prompt(self):
        self.write("Password: ")
        self.hide_next_input()

    def write_chatting_prompt(self):
        self.write("> ")

    def handle_chatting(self, message):
        if message == "/quit":
            self.quit()
            return

        if not message:
            self.writeln("Empty message not sent.")
        else:
            self.gecho(message)
        self.write_chatting_prompt()

    def gecho(self, message, emote=False):
        this_conn = self.connection
        server = this_conn.server
        actor = this_conn.actor

        template = "{}<#{}>: {}"
        if emote:
            template = "{}<#{}> {}"

        output = template.format(
            actor.name,
            this_conn.id,
            message
        )

        for connection in server.connections:
            client = connection.client

            if client.state != "chatting":
                continue

            connection.writeln(output)

    def disconnect(self):
        self.gecho("disconnected from the chat", emote=True)

    def reconnect(self):
        self.gecho("reconnected to the chat", emote=True)

    def quit(self):
        self.gecho("quit the chat", emote=True)
        self.connection.stop(clean=True)

    def login(self):
        self.gecho("joined the chat", emote=True)


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
        try:
            message = self.socket.recv(self.READ_SIZE)
        except Exception:
            return None

        if not message:
            return None

        message = message.decode("utf-8").replace("\r\n", "\n")
        return message

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
        except Exception:
            pass
        try:
            self.socket.close()
        except Exception:
            pass

    def flush(self, message):
        try:
            self.socket.sendall(message)
        except Exception:
            pass


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
                connection.handle_next_input()
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
