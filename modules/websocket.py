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
import zlib
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


class WebsocketConnection(Connection):
    """Wrapper for interfacing with raw Websocket connection."""
    READ_SIZE = 1024

    def __init__(self, socket, path, server):
        super(WebsocketConnection, self).__init__(server)

        self.socket = socket  # Raw socket
        self.client = None
        self.color = True

        self.ip = "abc"
        self.hostname = "abc"
        self.port = -1

        self.http_buffer = ""
        self.upgraded = False
        self.encoding = "base64"

    @classmethod
    def generate_response_key(self, key):
        MAGIC_WEBSOCKET_HASH = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        key_bytes = (key + MAGIC_WEBSOCKET_HASH).encode()
        hashed = hashlib.sha1(key_bytes).digest()
        encoded = base64.b64encode(hashed).decode("utf-8")

        return encoded

    def encode_frame(self, message):
        if self.encoding == "base64":
            message = base64.b64encode(message.encode()).decode("utf-8")

        packet = []

        header = 0b10000001
        packet.append(header)

        length = len(message)
        header = 0b00000000
        if length < 127:
            header |= length
            packet.append(header)
        else:
            header |= 126
            packet.append(header)
            packet.append(0b00000000)
            packet.append(length)

        packet += [ord(c) for c in message]

        packet = bytes(bytearray(packet))

        return packet

    def decode_frame(self, frame):
        """Return a frame converted to a utf-8 message."""
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
        frame = bytearray(frame)

        first_byte = bin(frame.pop(0))[2:]
        final_chunk = bool(int(first_byte[0]))
        rsv1 = int(first_byte[1], 2)
        rsv2 = int(first_byte[2], 2)
        rsv3 = int(first_byte[3], 2)
        opcode = int(first_byte[4:], 2)

        print("FIRST BYTE", final_chunk, rsv1, rsv2, rsv3, opcode)

        second_byte = bin(frame.pop(0))[2:]
        masked = bool(int(second_byte[0]))
        length = int(second_byte[1:], 2)

        print("SECOND_BYTE", masked, length)

        if masked:
            print("MASKED")
            mask = int(bin(frame.pop(0))[2:] + bin(frame.pop(0))[2:] + \
                bin(frame.pop(0))[2:] + bin(frame.pop(0))[2:], 2)
            print("MASK", mask)

        return "Kelemvor"

    def send_upgrade_protocol_response(self, request):
        print("REQUEST")
        print(request)
        if request["headers"].get("Connection") == "Upgrade" and \
                request["headers"].get("Upgrade") == "websocket":

            key = request["headers"].get("Sec-WebSocket-Key", "")
            response_key = self.generate_response_key(key)
            response = "\r\n".join([
                "HTTP/1.1 101 Switching Protocols",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Protocol: {}".format(self.encoding),
                "Sec-WebSocket-Accept: {}".format(response_key),
            ]) + "\r\n\r\n"

            self.socket.sendall(response.encode())

            self.upgraded = True

            self.client = TelnetClient(self)
            self.client.start()

    def handle_http_request(self, message):
        request = {
            "headers": {}
        }

        lines = message.split("\r\n")

        for line in lines:
            if ":" in line:
                parts = line.split(":")
                key = parts[0].strip()
                value = parts[1].strip()

                request["headers"][key] = value

        self.send_upgrade_protocol_response(request)

    def read(self):
        try:
            message = self.socket.recv(self.READ_SIZE)
        except Exception:
            message = None

        if not message:
            return None

        if not self.upgraded:
            self.http_buffer += message.decode("utf-8")
            if self.http_buffer.endswith("\r\n\r\n"):
                self.handle_http_request(self.http_buffer)
            return ""

        message = self.decode_frame(message)
        return message

    def close(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def flush(self, message):
        if self.color:
            message = Ansi.colorize(message)
        else:
            message = Ansi.decolorize(message)

        print(">" * 79)
        print(message)
        print(">" * 79)

        if self.upgraded:
            self.socket.sendall(self.encode_frame(message))
        else:
            self.socket.sendall(message.encode())


assert WebsocketConnection.generate_response_key("sEGJXdZWFYbO1zhnJFIJYg==") == \
    "k8XClzmPQSrsx2iosVcli0dbw2g="
assert WebsocketConnection.generate_response_key("aP4YaacppD1DAxk7yVph6w==") == \
    "kvA1w1TSUEC0dZbKgCKKjzZO3LU="


class WebsocketServer(TelnetServer):
    CONNECTION_CLASS = WebsocketConnection

    def __init__(self, *args, **kwargs):
        super(WebsocketServer, self).__init__(*args, **kwargs)

        self.keys = []

    def get_port_entries(self):
        from settings import WEBSOCKET_PORTS
        return WEBSOCKET_PORTS


class Websocket(Module):
    MODULE_NAME = "Websocket"
    VERSION = "0.1.0"

    MANAGERS = [
        WebsocketServer,
    ]
