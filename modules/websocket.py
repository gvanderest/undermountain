"""
WEBSOCKET MODULE
"""
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import logging
import gevent
import socket
import gevent.monkey
from mud.module import Module
from mud.server import Server
from modules.telnet import TelnetConnection, TelnetClient
from utils.ansi import Ansi


class WebsocketConnection(TelnetConnection):
    """Wrapper for interfacing with raw Websocket connection."""
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


class WebsocketServer(Server):
    def init(self):
        self.ports = []

    def create_server(self, entry):
        """Create a port to listen on."""
        host = entry["host"]
        port = entry["port"]

        server = pywsgi.WSGIServer(
            (host, port),
            self.handle_connection
            # handler_class=WebSocketHandler
        )
        self.ports.append(server)
        gevent.spawn(server.serve_forever)

        logging.info("Started websockets server: {}:{}".format(host, port))

    def handle_connection(self, environ, start_response):
        logging.info("New websocket connection from {}:{}".format("abc", "123"))
        print("DEBUG", environ, start_response)
        ws = environ["wsgi.websocket"]
        while True:
            data = ws.receive()
            ws.send("THIS IS A TEST: " + data)
            gevent.sleep(1.0)

        # connection = TelnetConnection(sock, addr, self)
        # self.add_connection(connection)
        # connection.start()

    def start(self):
        """Instantiate the servers/ports and sockets."""
        from settings import WEBSOCKET_PORTS

        self.running = True

        for entry in WEBSOCKET_PORTS:
            self.create_server(entry)

        while self.running:
            for connection in self.connections:
                connection.handle_next_input()
                connection.handle_flushing_output()
            gevent.sleep(0.01)


class Websocket(Module):
    MODULE_NAME = "Websocket"
    VERSION = "0.1.0"

    MANAGERS = [
        WebsocketServer,
    ]
