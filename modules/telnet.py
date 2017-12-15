from gevent import monkey
from mud.client import Client
from mud.inject import inject
from mud.connection import Connection
from mud.server import Server
from mud.module import Module
from utils.ansi import colorize, decolorize
from utils.fuzzy_resolver import FuzzyResolver

import gevent
import settings
import socket as raw_socket

monkey.patch_all()


class TelnetClient(Client):
    INITIAL_STATE = "login_username"

    def __init__(self, *args, **kwargs):
        super(TelnetClient, self).__init__(*args, **kwargs)
        self.write_ended_with_newline = False
        self.prompt_thread = False
        self.resolver = FuzzyResolver(self.game.commands)
        self.color = True
        self.writeln("Connected to {rU{8nd{wer{Wmou{wnt{8ai{rn{x.")
        self.writeln()
        self.write("What is your name, adventurer? ")

    @inject("Characters")
    @property
    def actor(self, Characters):
        return Characters.get(self.connection.actor_id)

    def stop(self):
        self.writeln("Disconnecting..")

    def handle_login_username_input(self, message):
        Characters = self.game.get_injector("Characters")
        name = message.strip().lower().title()

        found = Characters.get({"name": name})
        if not found:
            found = Characters.save(Characters.ENTITY_CLASS({
                "room_id": "abc123",
                "name": name,
            }))
        elif found.connection:
            found.echo("You have been kicked off due to another logging in.")
            found.connection.close()

        found.online = True
        found.connection_id = self.connection.id
        found.save()

        self.connection.actor_id = found.id

        self.state = "playing"
        self.handle_playing_input("look")

    def quit(self):
        self.connection.close()
        self.connection.server.remove_connection(self.connection)

    def write(self, message=""):
        if self.state == "playing" and not self.write_ended_with_newline:
            message = "\n" + message

        if self.color:
            message = colorize(message)
        else:
            message = decolorize(message)

        self.write_ended_with_newline = message[-1] == "\n"

        super(TelnetClient, self).write(message)
        if not self.prompt_thread:
            self.prompt_thread = gevent.spawn(self.write_prompt)

    def write_prompt(self):
        if self.state != "playing":
            return
        self.writeln()
        self.write("{x> ")

    @inject("Characters")
    def handle_playing_input(self, message, Characters):
        actor = Characters.get(self.connection.actor_id)
        delay = None

        while self.inputs and not self.inputs[0]:
            self.inputs.pop(0)

        parts = message.split(" ")
        name = parts[0].lower()
        args = parts[1:]

        kwargs = {"args": args, "name": name, "message": " ".join(args)}

        command = None
        for real_name, entry in self.resolver.query(name):
            min_level = entry.get("min_level", 0)
            max_level = entry.get("max_level", 9999)
            fake_level = 1
            if fake_level < min_level or fake_level > max_level:
                continue
            kwargs["name"] = real_name
            command = entry["handler"]
            break

        if command:
            # TODO Handle command exceptions.
            # try:
            delay = command(actor, **kwargs)
            # except Exception as e:
            #     self.writeln(repr(e))
            #     self.writeln("Huh?!")
        else:
            self.writeln("Huh?")

        return delay


class TelnetConnection(Connection):
    def __init__(self, server, socket, address):
        super(TelnetConnection, self).__init__(server)
        self.socket = socket
        self.client = TelnetClient(self)
        self.address = address
        self.buffer = ""

    def start(self):
        gevent.spawn(self.read)

    def close(self):
        try:
            self.socket.flush()
        except Exception:
            pass

        try:
            self.socket.shutdown(raw_socket.SHUT_WR)
        except Exception:
            pass

        try:
            self.socket.close()
        except Exception:
            pass

        self.socket = None

    def read(self):
        """Listen for commands/etc."""
        while self.socket:
            try:
                raw = self.socket.recv(4096)
            except Exception:
                raw = None
            if not raw:
                self.close()
                break

            try:
                self.buffer += raw.decode("utf-8").replace("\r\n", "\n")
            except Exception:
                pass

            if "\n" in self.buffer:
                split = self.buffer.split("\n")
                inputs = split[:-1]
                self.buffer = split[-1]

                self.client.handle_inputs(inputs)

    def write(self, message=""):
        if not self.socket:
            return
        message = message.replace("\n", "\r\n")
        self.socket.send(message.encode())


class TelnetServer(Server):
    def __init__(self, game):
        super(TelnetServer, self).__init__(game)
        self.ports = []

    def start(self):
        """Instantiate the ports to listen on."""
        for host, port in settings.TELNET_PORTS:
            socket = raw_socket.socket(
                raw_socket.AF_INET,
                raw_socket.SOCK_STREAM,
            )
            socket.setsockopt(
                raw_socket.SOL_SOCKET,
                raw_socket.SO_REUSEADDR,
                1,
            )
            socket.bind((host, port))
            self.ports.append(socket)
            gevent.spawn(self.accept, socket)

    def accept(self, port):
        """Listen and handle Connections on port."""
        port.listen()
        while True:
            socket, address = port.accept()
            conn = TelnetConnection(self, socket, address)
            self.add_connection(conn)
            gevent.spawn(conn.start)


class TelnetModule(Module):
    DESCRIPTION = "Support the Telnet protocol for connections"

    def __init__(self, game):
        super(TelnetModule, self).__init__(game)
        self.game.register_manager(TelnetServer)
