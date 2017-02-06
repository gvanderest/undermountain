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
from mud.server import Server
from utils.ansi import Ansi

gevent.monkey.patch_socket()


class TelnetClient(Client):
    """Wrapper for how our Game works."""
    def init(self):
        self.last_command = None
        self.actor = None

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

        game = self.get_game()
        Characters = game.get_injector("Characters")

        cleaned_name = message.lower().title()

        data = {"name": cleaned_name}

        actor = Characters.find(data)
        if actor:
            self.writeln("Sorry, that player is already playing.")
            self.write("What is your name? ")
            return

        actor = Characters.save(data)

        self.state = "playing"
        self.actor = actor
        actor.set_client(self)

        self.writeln("Thanks for providing your name, {}!".format(actor.name))
        self.writeln()
        self.login()
        self.write_playing_prompt()

    def write_login_password_prompt(self):
        self.write("Password: ")
        self.hide_next_input()

    def write_playing_prompt(self):
        conn = self.connection
        if conn.output_buffer and \
                conn.output_buffer[-2:] != (2 * self.NEWLINE):
            self.writeln()
        self.write("> ")

    def no_handler(self, arguments):
        self.writeln("Invalid command.")

    def get_connection(self):
        return self.connection

    def get_game(self):
        connection = self.get_connection()
        if not connection:
            return None
        return connection.get_game()

    def set_actor(self, actor):
        self.actor = actor

    def get_actor(self):
        return self.actor

    def handle_playing(self, message):
        if message == "!":
            if self.last_command is None:
                self.writeln("Huh?")
                self.write_playing_prompt()
            else:
                self.handle_playing(self.last_command)
            return

        self.last_command = message
        actor = self.get_actor()
        game = self.get_game()
        game.inject(
            actor.handle_command,
            message=message,
            ignore_aliases=False
        )

        self.write_playing_prompt()

    def gecho(self, message, emote=False):
        this_conn = self.connection
        game = self.get_game()
        actor = self.get_actor()

        template = "{}<#{}>: {}"
        if emote:
            template = "{}<#{}> {}"

        output = template.format(
            actor.name,
            this_conn.id,
            message
        )

        connections = game.get_connections()

        for connection in connections:
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
        Characters = self.get_game().get_injector("Characters")

        # Remove the Actor from the Game
        actor = self.get_actor()
        Characters.remove(actor)
        self.set_actor(None)

        self.connection.stop(clean=True)

    def login(self):
        # self.act_to_room("{actor.name} slowly fades into existence.")
        self.handle_input("look")


class TelnetConnection(Connection):
    READ_SIZE = 1024

    def __init__(self, socket, addr, *args, **kwargs):
        super(TelnetConnection, self).__init__(*args, **kwargs)

        self.socket = socket  # Raw socket
        self.client = TelnetClient(self)
        self.color = True

        self.ip = addr[0]  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def enable_color(self):
        self.color = True

    def disable_color(self):
        self.color = False

    def read(self):
        message = self.socket.recv(self.READ_SIZE)

        if message is None or not message:
            return None

        message = message \
            .decode("utf-8", errors="ignore") \
            .replace("\r\n", "\n")
        return message

    def close(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def flush(self, message):
        if self.color:
            message = Ansi.colorize(message)
        else:
            message = Ansi.decolorize(message)

        try:
            self.socket.sendall(message.encode())
        except OSError:
            pass


class TelnetServer(Server):

    CONNECTION_CLASS = TelnetConnection

    def init(self):
        self.ports = []

    def create_server(self, entry):
        """Create a port to listen on."""
        host = entry["host"]
        port = entry["port"]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)

        self.ports.append(sock)
        gevent.spawn(self.accept_port_connections, sock)

        logging.info("Started telnet server: {}:{}".format(host, port))

    def handle_connection(self, sock, addr):
        logging.info("New telnet connection from {}:{}".format(*addr))
        connection = self.CONNECTION_CLASS(sock, addr, self)
        self.add_connection(connection)
        connection.start()

    def get_port_entries(self):
        from settings import TELNET_PORTS
        return TELNET_PORTS

    def accept_port_connections(self, port):
        while self.running:
            sock, addr = port.accept()
            gevent.spawn(self.handle_connection, sock, addr)
            gevent.sleep(0.1)

    def start(self):
        """Instantiate the servers/ports and sockets."""
        super(TelnetServer, self).start()

        port_infos = self.get_port_entries()

        self.running = True

        for entry in port_infos:
            self.create_server(entry)

        while self.running:
            for connection in self.connections:
                connection.handle_next_input()
                connection.handle_flushing_output()
            gevent.sleep(0.01)


class Telnet(Module):
    MODULE_NAME = "Telnet"
    VERSION = "0.1.0"

    MANAGERS = [
        TelnetServer,
    ]
