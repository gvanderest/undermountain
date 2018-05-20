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

# Passwords and encryption
PASSWORD_ALGORITHM = "sha256"
PASSWORD_SALT = "undermountain"  # TODO Make this generated once on first run
PASSWORD_ROUNDS = 100000

TICK_SECONDS = 5.0  # Defaults to one tick per minute

# Special keywords.
SELF_NAMES = (
    "self",
)


# Modules to include
MODULES = (
    "modules.core.CoreModule",
    "modules.telnet.TelnetModule",
    "modules.combat.CombatModule",
    "modules.build.BuildModule",
    "modules.socials.SocialsModule",
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

VNUM_AREA_SEPARATOR = ":"

# Conversation channels.
CHANNELS = {
    "ooc": {
        "to_others": "{W[*OOC*]{c{name} {8'{w{message}{8'{x",
        "to_self": "{WYou OOC {8'{w{message}{8'{x",
    },
    "trash": {
        "toggle_warning": """
You are about to enable a channel that is bad.
Please verify that you really want to turn this bad channel by toggling \
again.""",
        "to_others": "{name} TRASHes '{message}'",
        "to_self": "You TRASH '{message}'",
    },
    "immtalk": {
        "to_others": "{x{name}: {W{message}{x",
    },
    "auction": {
        "to_self": "You {R<{G-{Y={MA/B{Y={G-{R> {CAuction {x'{G{message}{x'",
        "to_others":
            "{name} {R<{G-{Y={MA/B{Y={G-{R> {CAuctions {x'{G{message}{x'",
    },
    "bid": {
        "to_self": "You {R<{G-{Y={MA/B{Y={G-{R> {CBid {x'{G{message}{x'",
        "to_others":
            "{name} {R<{G-{Y={MA/B{Y={G-{R> {CBids {x'{G{message}{x'",
    },
    "cgossip": {
        "to_self": "You cgossip '{R{message}{x'",
        "to_others": "{name} cgossips '{R{message}{x'",
    },
    "qgossip": {
        "to_self": "You {C({Wqg{Bo{bs{Bs{Wip{C){x '{C{message}{x'",
        "to_others": "{name} {C({Wqg{Bo{bs{Bs{Wip{C){x '{C{message}{x'",
    },
    "heronet": {
        "to_self": "{g[You {GHero-Net{g]: '{message}{g'",
        "to_others": "{g[{name} {GHero-Nets{g]: '{message}{g'",
    },
    "quote": {
        "to_self": "You quote '{g{message}{x'",
        "to_others": "{name} quotes '{g{message}{x'",
    },
    "ask": {
        "to_self": "You [Q/A] Ask '{Y{message}{x'",
        "to_others": "{name} [Q/A] Asks '{Y{message}{x'",
    },
    "answer": {
        "to_self": "You [Q/A] Answer '{Y{message}{x'",
        "to_others": "{name} [Q/A] Answers '{Y{message}{x'",
    },
}


LEVEL_MAXIMUM = 15
