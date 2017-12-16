import os

#
# SYSTEM BASICS
#

# How fast is "one second" in the world?  Smaller number for faster
# Default: 1.0
GAME_LOOP_TIME = 1.0

# Where are datafiles for the game stored?
# Default: <base_folder>/data
BASE_FOLDER = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = "{}/data".format(BASE_FOLDER)
BACKUPS_FOLDER = "{}/backups".format(BASE_FOLDER)

# Modules to include
MODULES = (
    "modules.core.CoreModule",
    "modules.telnet.TelnetModule",
)

DIRECTIONS = {
    "north": {
        "id": "north",
        "colored_name": "{Rnorth{x",
        "opposite_id": "south",
    },
    "east": {
        "id": "east",
        "colored_name": "{Meast{x",
        "opposite_id": "west",
    },
    "south": {
        "id": "south",
        "colored_name": "{rsouth{x",
        "opposite_id": "north",
    },
    "west": {
        "id": "west",
        "colored_name": "{mwest{x",
        "opposite_id": "east",
    },
    "up": {
        "id": "up",
        "colored_name": "{Yup{x",
        "opposite_id": "down",
    },
    "down": {
        "id": "down",
        "colored_name": "{ydown{x",
        "opposite_id": "up",
    },
}


#
# NETWORKING AND CONNECTIONS
#

# Which ports do we want to allow/open up?
TELNET_PORTS = (
    ("0.0.0.0", 4200),
    ("0.0.0.0", 4201),
)

WEBSOCKET_PORTS = (
    ("0.0.0.0", 14200),
    ("0.0.0.0", 14201),
)

INITIAL_ROOM_VNUM = "market_square"
