"""
WEBSOCKET MODULE
"""
import base64
import gevent
import socket
import gevent.monkey
import hashlib
from mud.module import Module
from mud.connection import Connection
from modules.telnet import TelnetClient, TelnetServer
from utils.ansi import Ansi

gevent.monkey.patch_socket()


class WebsocketClient(TelnetClient):
    def start(self):
        pass


class WebsocketConnection(Connection):
    """Wrapper for interfacing with raw Websocket connection."""
    TYPE = "Websocket"
    READ_SIZE = 1024

    def __init__(self, the_socket, addr, server):
        super(WebsocketConnection, self).__init__(server)

        self.socket = the_socket  # Raw socket
        self.client = None
        self.color = True

        self.ip = socket.gethostbyname(addr[0])  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

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

    def encode_frames(self, message):
        if self.encoding == "base64":
            encoded = base64.b64encode(message.encode()).decode("utf-8")

        packet = bytearray()

        # Indexes:      01234567
        packet.append(0b10000001)

        length = len(encoded)
        if length < 126:
            packet.append(length)
        else:
            packet.append(126)
            packet.append(length >> 8)
            packet.append(length % 2**8)

        packet += bytearray(ord(c) for c in encoded)

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

        first_byte = bin(frame.pop(0))[2:].zfill(8)
        final_chunk = bool(int(first_byte[0]))
        rsv1 = int(first_byte[1], 2)
        rsv2 = int(first_byte[2], 2)
        rsv3 = int(first_byte[3], 2)
        opcode = int(first_byte[4:], 2)

        second_byte = bin(frame.pop(0))[2:].zfill(8)
        masked = bool(int(second_byte[0]))
        length = int(second_byte[1:], 2)

        length_parts = []
        if length >= 126:
            for x in range(2 if length == 126 else 8):
                length_parts.append(bin(frame.pop(0)[2:].zfill(8)))
            length = int("".join(length_parts), 2)

        mask = bytearray()
        for x in range(4):
            mask.append(int(bin(frame.pop(0)), 2))

        masks = [mask[i % 4] for i in range(len(frame))]

        results = [(int(frame[x]) ^ int(masks[x])) for x in range(len(frame))]

        chars = [chr(x) for x in results]

        try:
            decoded = base64.b64decode("".join(chars)).decode("utf-8")
        except ValueError:
            decoded = None

        return decoded

    def send_upgrade_protocol_response(self, request):
        if "Upgrade" in request["headers"].get("Connection") and \
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
        except Exception as e:
            return None

        if not self.upgraded:
            self.http_buffer += message.decode("utf-8")
            if self.http_buffer.endswith("\r\n\r\n"):
                self.handle_http_request(self.http_buffer)
            return ""

        message = self.decode_frame(message)
        if not message:
            return ""

        return message

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        self.socket.close()

    def flush(self):
        if not self.output_buffer:
            return

        message = self.output_buffer
        self.output_buffer = ""

        if self.color:
            message = Ansi.colorize(message)
        else:
            message = Ansi.decolorize(message)

        try:
            if self.upgraded:
                frames = self.encode_frames(message)
                self.socket.sendall(frames)
            else:
                self.socket.sendall(message.encode())
        except OSError:
            self.running = False


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
