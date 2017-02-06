"""
WEBSOCKET MODULE
"""
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import base64
import logging
import gevent
import socket
import gevent.monkey
import hashlib
from mud.module import Module
from mud.server import Server
from mud.client import Client
from mud.connection import Connection
from modules.telnet import TelnetConnection, TelnetClient, TelnetServer
from utils.ansi import Ansi
from utils.hash import get_random_hash

gevent.monkey.patch_socket()


class WebsocketClient(TelnetClient):
    def start(self):
        pass

    def handle_input(self, message):
        conn = self.connection

        if ":" in message:
            parts = message.split(": ")
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) >= 2 else ""
            print(len(parts), parts)
            if key == "Sec-WebSocket-Key":
                conn.source_key = value
                conn.hash = get_random_hash()
                key_bytes = (conn.source_key + conn.hash).encode()
                print("RAW KEY", repr(key_bytes))
                conn.key = base64.b64encode(hashlib.sha1(key_bytes).hexdigest().encode())
                print("BOOOP", conn.key)

            elif key == "Sec-WebSocket-Protocol":
                self.encoding = value
                print("SETTING WEBSOCKET ENCODING", value)

        if not message:
            print(79 * "=")
            print("END OF REQUEST")
            response = """\
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: {}
Sec-WebSocket-Protocol: chat
""".format(conn.key)
            print(">" * 79)
            print(response)
            print(">" * 79)
            self.connection.socket.sendall(response.encode())
            # self.send_frames()

    def send_frames(self):
        """
          0                   1                   2                   3
          0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
         +-+-+-+-+-------+-+-------------+-------------------------------+
         |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
         |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
         |N|V|V|V|       |S|             |   (if payload len==126/127)   |
         | |1|2|3|       |K|             |                               |
         +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
         |     Extended payload length continued, if payload len == 127  |
         + - - - - - - - - - - - - - - - +-------------------------------+
         |                               |Masking-key, if MASK set to 1  |
         +-------------------------------+-------------------------------+
         | Masking-key (continued)       |          Payload Data         |
         +-------------------------------- - - - - - - - - - - - - - - - +
         :                     Payload Data continued ...                :
         + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
         |                     Payload Data continued ...                |
         +---------------------------------------------------------------+"""
        packet = [
            1,  # Is final chunk
            0, 0, 0,  # Reserved flags
            0, 0, 0, 1,  # Opcode
            0,  # Mask
            0, 0, 0, 0, 1, 0, 0  # Payload length in bytes
        ]

        message = "Test"
        packet += [ord(c) for c in message]

        print(bytearray(packet))

        self.connection.socket.send(bytearray(packet))
        # self.writeln(packet)


class WebsocketConnection(Connection):
    """Wrapper for interfacing with raw Websocket connection."""
    READ_SIZE = 1024

    def __init__(self, socket, path, server):
        super(WebsocketConnection, self).__init__(server)

        self.socket = socket  # Raw socket
        self.client = WebsocketClient(self)
        self.color = True

        self.ip = "abc"
        self.hostname = "abc"
        self.port = -1

        self.source_key = None
        self.key = None
        self.encoding = "base64"
        self.hash = None

    def read(self):
        message = self.socket.recv(self.READ_SIZE)

        if message is None or not message:
            return None

        message = message \
            .decode("utf-8", errors="ignore") \
            .replace("\r\n", "\n")

        print("RAW WEBSOCKET", message)
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


class WebsocketServer(TelnetServer):
    CONNECTION_CLASS = WebsocketConnection

    def get_port_entries(self):
        from settings import WEBSOCKET_PORTS
        return WEBSOCKET_PORTS


class Websocket(Module):
    MODULE_NAME = "Websocket"
    VERSION = "0.1.0"

    MANAGERS = [
        WebsocketServer,
    ]
