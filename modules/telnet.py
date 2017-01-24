"""
TELNET MODULE
"""
import logging
import gevent
import socket
import gevent.monkey
from mud.client import Client
from mud.connection import Connection
from mud.module import Module
from mud.manager import Manager
from modules.core import Actor

gevent.monkey.patch_socket()


def no_handler(self, arguments):
    asfasdf()
    self.writeln("Huh?")


def quit_command(self, arguments):
    self.quit()


def me_command(self, arguments):
    message = " ".join(arguments)
    self.gecho(message, emote=True)


class TelnetClient(Client):
    """Wrapper for how our Game works."""

    COMMAND_HANDLERS = {
        "quit": quit_command,
        "me": me_command,
    }

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
        self.state = "playing"

        actor = Actor({
            "name": message.lower().title()
        })

        self.connection.actor = actor
        actor.set_connection(self.connection)

        self.writeln("Thanks for providing your name, {}!".format(actor.name))
        self.login()
        self.write_playing_prompt()

    def write_login_password_prompt(self):
        self.write("Password: ")
        self.hide_next_input()

    def write_playing_prompt(self):
        self.write("> ")

    def no_handler(self, arguments):
        self.writeln("Invalid command.")

    def get_game(self):
        return self.connection.server.game

    def handle_playing(self, message):
        if not message:
            self.write_playing_prompt()
            return

        if message.startswith("/"):
            parts = message.split(" ")
            first_part = parts.pop(0)

            command = first_part[1:]
            arguments = parts

            handler = self.COMMAND_HANDLERS.get(command, no_handler)

            if handler is None:
                self.writeln("Huh?")
            else:
                try:
                    handler(self, arguments)
                except Exception as e:
                    game = self.get_game()
                    game.handle_exception(e)
                    self.writeln("Huh?!  (Code bug detected and reported.)")

            self.write_playing_prompt()
        else:
            self.gecho(message)

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

            if client.state != "playing":
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


class TelnetConnection(Connection):
    READ_SIZE = 1024
    DEBUG = True

    def __init__(self, socket, addr, *args, **kwargs):
        super(TelnetConnection, self).__init__(*args, **kwargs)

        self.socket = socket  # Raw socket
        self.client = TelnetClient(self)

        self.ip = addr[0]  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def read(self):
        message = self.socket.recv(self.READ_SIZE)

        if message is None or not message:
            return None

        message = message.decode("utf-8").replace("\r\n", "\n")
        return message

    def close(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def flush(self, message):
        self.socket.sendall(message.encode())

class TelnetServer(Manager):
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
        self.game.add_connection(connection)

    def remove_connection(self, connection):
        """Remove the Connection from the list."""
        # TODO unregister Connection with Game
        self.connections.remove(connection)
        self.game.remove_connection(connection)

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
        super(TelnetServer, self).start()

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
        TelnetServer,
    ]
