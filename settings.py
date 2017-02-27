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
    Websocket
)

DATA_PATH = os.path.dirname(__file__) + "/data"
ROT_DATA_PATH = DATA_PATH + "/__rot__"


PID_FILE = "pid"
SHUTDOWN_FILE = 'SHUTDOWN'
REBOOT_FILE = 'REBOOT'

TELNET_PORTS = (
    {"host": "0.0.0.0", "port": 4201},
    {"host": "0.0.0.0", "port": 4202},
)

WEBSOCKET_PORTS = (
    {"host": "0.0.0.0", "port": 14201},
    {"host": "0.0.0.0", "port": 14202},
)

DEBUG_CONNECTION_COUNTS = False
DEBUG_INPUT_TIMING = True

DIRECTIONS = {
    "north": {"name": "{Rnorth", "opposite_id": "south"},
    "east": {"name": "{Meast", "opposite_id": "west"},
    "south": {"name": "{rsouth", "opposite_id": "north"},
    "west": {"name": "{mwest", "opposite_id": "west"},
    "up": {"name": "{Yup", "opposite_id": "down"},
    "down": {"name": "{ydown", "opposite_id": "up"},
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

ORGANIZATION_TYPES = {
    "clan": {
        "leader_count": 1,
        "ranks": [
            {
                "id": "leader",
                "name": "Leader",
                "who_symbol": "L",
                "rank": 1,

                "max_count": 1,
                "powers": {
                    "invite": True,
                    "remove": True,
                    "promote": True,
                    "demote": True
                }
            },
            {
                "id": "officer",
                "name": "Officer",
                "who_symbol": "O",
                "rank": 2,
                "powers": {
                    "invite": True,
                    "remove": True,
                    "promote": True,
                    "demote": True
                }

            },
            {
                "id": "member",
                "name": "Member",
                "who_symbol": "M",
                "rank": 3,
                "powers": {
                    "invite": False,
                    "remove": False,
                    "promote": False,
                    "demote": False
                }
            },
            {
                "id": "recruit",
                "name": "Recruit",
                "who_symbol": "R",
                "rank": 4,
                "powers": {
                    "invite": False,
                    "remove": False,
                    "promote": False,
                    "demote": False
                }
            }
        ]
    }
}
ORGANIZATIONS = {
    "vector": {
        "type_id": "clan",
        "name": "{MV{mectorian {ME{mmpire",
        "who_name": "{MV{mectr",
        "rank_names": {
            "leader": "{ML{meader",
            "officer": "{ML{meader",
            "member": "{MM{member",
            "recruit": "{MR{mecruit",
        }
    },
    "blackchurch": {
        "type_id": "clan",
        "name": "{8Black Church",
        "who_name": "BlkCh",
        "allies": [
            "radiantheart"
        ],
        "rank_names": {
            "leader": "Leader",
            "officer": "Officer",
            "member": "Member",
            "recruit": "Recruit",
        }
    },
    "strife": {
        "type_id": "clan",
        "name": "{MCh{murc{8h of S{mtrife",
        "who_name": "{MC{8o{MS",
        "rank_names": {
            "leader": "{MH{mig{8hpri{mes{Mt",
            "officer": "{MB{mi{8sh{mo{Mp",
            "member": "{MM{me{8mb{me{Mr",
            "recruit": "{MA{mc{8oly{mt{Me",
        }
    },
    "radiantheart": {
        "type_id": "clan",
        "allies": [
            "blackchurch"
        ],
        "name": "{RO{rr{yd{re{Rr {cof the {RR{rad{yi{ran{Rt H{re{ya{rr{Rt",
        "who_name": "{RR{rd{RH{rr{Rt",
        "rank_names": {
            "leader": "Lord Knight",
            "officer": "Officer",
            "member": "Member",
            "recruit": "Recruit",
        }
    },
}

CHANNELS = {
    "ooc": {
        "name": "Out Of Character",
        "default_active": True,
        "force_visible": True,
        "force_immortal_visible": False,
        "default_color": "{w",
        "self_format": "{{WYou OOC {{8'{{w{message}{{8'{{x",
        "format": "{{W[*OOC*]{{c{actor.name} {{8'{{w{message}{{8'{{x",
    },
    "trash": {
        "name": "Trash",
        "default_active": False,
        "confirmation": True,
        "confirmation_message": "Are you sure you wish to activate the trash channel?\nType 'trash' again if so.",
        "force_visible": True,
        "format": "TRASH {actor.name} '{message}'",
    },
    "clan": {
        "name": "Clan Chat",
        "self_format": "You clan '{{M{message}{{x'",
        "format": "{actor.name} clans '{{M{message}{{x'",
        "default_active": True,
        "activate_check": lambda self: self.clan_id is not None,
        "receive_check": lambda self, other: self.clan_id == other.clan_id,
        "send_check": lambda self: self.clan_id is not None,
    }
}
