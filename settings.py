"""
SETTINGS
Provide options and flags for users to customize.
"""
import os.path
from modules.core import Core
from modules.telnet import Telnet
from modules.websockets import Websockets


MODULES = (
    Core,
    Telnet,
    Websockets
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

WEBSOCKETS_PORTS = (
    {"host": "0.0.0.0", "port": 14200},
)


DIRECTIONS = {
    "north": {"opposite_id": "south"},
    "east": {"opposite_id": "west"},
    "south": {"opposite_id": "north"},
    "west": {"opposite_id": "west"},
    "up": {"opposite_id": "down"},
    "down": {"opposite_id": "up"},
}
