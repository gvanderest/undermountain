"""
SETTINGS
Provide options and flags for users to customize.
"""
import os.path
from modules.core import Core
from modules.telnet import Telnet
from modules.websocket import Websocket


MODULES = (
    Core,
    Telnet,
    # Websocket
)

DATA_PATH = os.path.dirname(__file__) + "/data"
ROT_DATA_PATH = DATA_PATH + "/__rot__"


PID_FILE = "pid"
SHUTDOWN_FILE = 'SHUTDOWN'
REBOOT_FILE = 'REBOOT'


TELNET_PORTS = (
    {"host": "0.0.0.0", "port": 4200},
    {"host": "0.0.0.0", "port": 4201},
)

WEBSOCKET_PORTS = (
    {"host": "0.0.0.0", "port": 14200},
)

DEBUG_CONNECTION_COUNTS = False
DEBUG_INPUT_TIMING = True

DIRECTIONS = {
    "north": {"opposite_id": "south"},
    "east": {"opposite_id": "west"},
    "south": {"opposite_id": "north"},
    "west": {"opposite_id": "west"},
    "up": {"opposite_id": "down"},
    "down": {"opposite_id": "up"},
}

SWEAR_WORDS = (
    "cunt",
    "cunts",
    "fag",
    "faggot",
    "fags",
    "fuck",
    "fucker",
    "fucking",
    "fucked",
    "fucks",
    "nigger",
    "niggers",
)
SWEAR_WORDS_REPLACE_SYMBOL = "*"
SWEAR_WORDS_IGNORE_CHARS = "'\",\n\r-_?!"
