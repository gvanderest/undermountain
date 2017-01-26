"""
WEBSOCKETS MODULE
"""
import asyncio
import websockets
import logging
import gevent
import socket
import gevent.monkey
from mud.module import Module
from mud.server import Server
from modules.telnet import TelnetConnection, TelnetClient
from utils.ansi import Ansi

gevent.monkey.patch_socket()


class WebsocketsConnection(TelnetConnection):
    """Wrapper for interfacing with raw Websockets connection."""
    def __init__(self, websocket, path, server):
        super(TelnetConnection, self).__init__(server)

        self.socket = socket  # Raw socket
        self.client = TelnetClient(self)
        self.color = True

        self.ip = "abc"
        self.hostname = "abc"
        self.port = -1

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


class WebsocketsServer(Server):
    def init(self):
        self.ports = []

    def create_server(self, entry):
        """Create a port to listen on."""
        host = entry["host"]
        port = entry["port"]

        event_loop = asyncio.get_event_loop()
        server = websockets.serve(self.handle_connection, host, port)

        running = event_loop.run_until_complete(server)
        self.ports.append(running)

        logging.info("Started websockets server: {}:{}".format(host, port))

    def handle_connection(self, reader, writer):
        print("HELLOOOOO", reader, writer)
        logging.info("New websockets connection from {}:{}".format("abc", "123"))
        # connection = TelnetConnection(sock, addr, self)
        # self.add_connection(connection)
        # connection.start()

    def start(self):
        """Instantiate the servers/ports and sockets."""
        from settings import WEBSOCKETS_PORTS

        self.running = True

        for entry in WEBSOCKETS_PORTS:
            self.create_server(entry)

        # event_loop = asyncio.get_event_loop()
        # gevent.spawn(event_loop.run_forever)

        while self.running:
            for connection in self.connections:
                connection.handle_next_input()
                connection.handle_flushing_output()
            gevent.sleep(0.01)


class Websockets(Module):
    MODULE_NAME = "Websockets"
    VERSION = "0.1.0"

    MANAGERS = [
        WebsocketsServer,
    ]
