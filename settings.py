"""
SETTINGS
Provide options and flags for users to customize.
"""
import os.path

MODULES = (
    'modules.core.Core',
    'modules.telnet.Telnet',
    'modules.websocket.Websocket'
)

DATA_PATH = os.path.dirname(__file__) + "/data"
ROT_DATA_PATH = DATA_PATH + "/__rot__"


PASSWORD_SALT_PREFIX = "SALTY"
PASSWORD_SALT_SUFFIX = "PIRATE"

PID_FILE = "pid"
SHUTDOWN_FILE = 'SHUTDOWN'
REBOOT_FILE = 'REBOOT'

IDLE_TIME_TO_DISCONNECT = 60 * 10
DEFAULT_TELNET_PROMPT = "{8[{R%h{8/{r%H{8h {B%m{8/{b%M{8m {M%v{8v " \
    "{W%N{8({Y%X{8) {W%r{8({w%q{8/{w%t{8) {W%a{8]"

DEFAULT_ROOM_VNUM = "westbridge:temple_of_life"

TELNET_PORTS = (
    {"host": "0.0.0.0", "port": 4201},
    {"host": "0.0.0.0", "port": 4202},
)

WEBSOCKET_PORTS = (
    {"host": "0.0.0.0", "port": 14201},
    {"host": "0.0.0.0", "port": 14202},
)

DEBUG_CONNECTION_COUNTS = False
DEBUG_INPUT_TIMING = False

DIRECTIONS = {
    "north": {"name": "{Rnorth{x", "opposite_id": "south"},
    "east": {"name": "{Meast{x", "opposite_id": "west"},
    "south": {"name": "{rsouth{x", "opposite_id": "north"},
    "west": {"name": "{mwest{x", "opposite_id": "west"},
    "up": {"name": "{Yup{x", "opposite_id": "down"},
    "down": {"name": "{ydown{x", "opposite_id": "up"},
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
    "bitch": {
        "name": "Bitch",
        "default_active": False,
        "confirmation": True,
        "confirmation_message": "Are you sure you wish to activate the trash channel?\nType 'trash' again if so.",
        "force_visible": True,
        "format": "{actor.name} {{RB{{ri{{Bt{{bc{{Bh{{re{{Rs {{8'{{Y{message}{{8'",
        "self_format": "{{WYou {{YBITCH {{8'{{Y{message}{{8'",
    },
    "clan": {
        "name": "Clan Chat",
        "self_format": "You clan '{{M{message}{{x'",
        "format": "{actor.name} clans '{{M{message}{{x'",
        "default_active": True,
        "activate_check": lambda self: self.clan_id is not None,
        "receive_check": lambda self, other: self.clan_id == other.clan_id,
        "send_check": lambda self: self.clan_id is not None,
    },
    "say": {
        "name": "Say",
        "format": "{{M{actor.name}{{M says {{x'{{m{message}{{x'",
        "self_format": "{{MYou say {{x'{{m{message}{{x'",
        "receive_check": lambda a, t: a.room_id == t.room_id
    },
    "immtalk": {
        "name": "Immortal Talk",
        "format": "{{x{actor.name}: {{W{message}{{x"
    },
    "auction": {
        "name": "Auction",
        "self_format": "{{xYou {{R<{{G-{{Y={{MA/B{{Y={{G-{{R> {{CAuction {{x'{{G{message}{{x'",
        "format": "{{x{actor.name} {{R<{{G-{{Y={{MA/B{{Y={{G-{{R> {{CAuctions {{x'{{G{message}{{x'",
    },
    "bid": {
        "name": "Bid",
        "self_format": "{{xYou {{R<{{G-{{Y={{MA/B{{Y={{G-{{R> {{CBid {{x'{{G{message}{{x'",
        "format": "{{x{actor.name} {{R<{{G-{{Y={{MA/B{{Y={{G-{{R> {{CBids {{x'{{G{message}{{x'",
    },
    "cgossip": {
        "name": "Clan Gossip",
        "self_format": "You cgossip '{{R{message}{{x'",
        "format": "{actor.name} cgossips '{{R{message}{{x'",
    },
    "agossip": {
        "name": "Area Gossip",
        "self_format": "{{xYou {{8({{Rag{{ro{{Bs{{rs{{Rip{{8) '{{B{message}{{x'",
        "format": "{{x{actor.name} {{8({{Rag{{ro{{Bs{{rs{{Rip{{8) '{{B{message}{{x'",
    },
    "gtell": {
        "name": "Group Tell",
        "self_format": "You tell the group '{{c{message}{{x'",
        "format": "{actor.name} tells the group '{{c{message}{{x'",
    },
    "quote": {
        "name": "Quote",
        "self_format": "You quote '{{g{message}{{x'",
        "format": "{actor.name} quotes '{{g{message}{{x'",
    },
    "heronet": {
        "name": "Heronet",
        "format": "{{g[{{R{actor.name} {{GHero-Nets{{g]:'{message}{{g'{{x",
        "self_format": "{{g[You {{GHero-Net{{g]:'{message}{{g'{{x",
    },
    "qgossip": {
        "name": "Quest Gossip",
        "format": "{{x{actor.name} {{C({{Wqg{{Bo{{bs{{Bs{{Wip{{C) {{x'{{C{message}{{x'",
        "self_format": "{{xYou {{C({{Wqg{{Bo{{bs{{Bs{{Wip{{C) {{x'{{C{message}{{x'",
    },
    "music": {
        "name": "Music",
        "format": "{actor.name} MUSIC: '{{C{message}{{x'",
        "self_format": "You MUSIC: '{{C{message}{{x'",
    },
    "ask": {
        "name": "Ask",
        "format": "{actor.name} [Q/A] Asks '{{Y{message}{{x'",
        "self_format": "You [Q/A] Ask '{{Y{message}{{x'",
    },
    "answer": {
        "name": "Answer",
        "format": "{actor.name} [Q/A] Answers '{{Y{message}{{x'",
        "self_format": "You [Q/A] Answer '{{Y{message}{{x'",
    },
    "grats": {
        "name": "Congratulations",
        "format": "{actor.name} {{Gg{{Yr{{Ra{{Bt{{Ms '{{y{message}{{x'",
        "self_format": "You grats '{{y{message}{{x'",
    },
    "shout": {
        "name": "Shout",
        "format": "{actor.name} shouts '{{r{message}{{x'",
        "self_format": "You shout '{{r{message}{{x'",
    },
}

"""
SOCIALS

me_to_room - You performing it to the room or nobody
actor_to_room - Actor performing to the room or nobody

me_to_target - You performing the emote to an Actor
actor_to_me - Actor performing the emote to you
actor_to_target - Watching an Actor perform the emote to its Target

me_to_self - You performing the emote to yourself
actor_to_self - Actor performing the emote to itself
"""
SOCIALS = {
    "dance": {
        "me_to_room": "Feels silly, doesn't it?",
        "actor_to_room": "{actor.name} dances wildly before you!",

        "me_to_target": "You lead {target.him} to the dancefloor.",
        "actor_to_me": "{actor.name} you across the dancefloor.",
        "actor_to_target": "{actor.name} sends {target.name} across the dancefloor.",

        "actor_to_self": "{actor.name} skips a light Fandango.",
        "me_to_self": "You skip and dance around by yourself.",
    }
}

GENDERS = {
    "male": {
        "name": "Male",
        "who_name": "{BM",
    },
    "female": {
        "name": "Feale",
        "who_name": "{MF",
    },
    "neutral": {
        "name": "Neutral",
        "who_name": "{8N",
    },
}
RACES = {
    "human": {
        "name": "Human",
        "who_name": "{CH{cuman",
    },
    "goblin": {
        "name": "Goblin",
        "who_name": "{CG{cobln",
    },
    "halfling": {
        "name": "Halfling",
        "who_name": "{CH{cflng",
    },
    "elf": {
        "name": "Elf",
        "who_name": "{CE{clf  ",
    },
    "halfelf": {
        "name": "Half-Elf",
        "who_name": "{CH{c.Elf",
    },
    "halforc": {
        "name": "Half-Orc",
        "who_name": "{CH{c.Orc",
    },
    "avian": {
        "name": "Avian",
        "who_name": "{CA{cvian",
    },
    "centaur": {
        "name": "Centaur",
        "who_name": "{CC{centr",
    },
    "draconian": {
        "name": "Draconian",
        "who_name": "{CD{cracn",
    },
    "drow": {
        "name": "Drow",
        "who_name": "{CD{crow ",
    },
    "dwarf": {
        "name": "Dwarf",
        "who_name": "{CD{cwarf",
    },
    "esper": {
        "name": "Esper",
        "who_name": "{CE{csper",
    },
    "giant": {
        "name": "Giant",
        "who_name": "{CG{ciant",
    },
    "gnoll": {
        "name": "Gnoll",
        "who_name": "{CG{cnoll",
    },
    "gnome": {
        "name": "Gnome",
        "who_name": "{CG{cnome",
    },
    "heucuva": {
        "name": "Heucuva",
        "who_name": "{CH{ceucv",
    },
    "kenku": {
        "name": "Kenku",
        "who_name": "{CK{cenku",
    },
    "minotaur": {
        "name": "Minotaur",
        "who_name": "{CM{cintr",
    },
    "pixie": {
        "name": "Pixie",
        "who_name": "{CP{cixie",
    },
    "podrikev": {
        "name": "Podrikev",
        "who_name": "{CP{codkv",
    },
    "satyr": {
        "name": "Satyr",
        "who_name": "{CS{catyr",
    },
    "thrikreen": {
        "name": "Thri'Kreen",
        "who_name": "{CT{chken",
    },
    "titan": {
        "name": "Titan",
        "who_name": "{CT{citan",
    },
}

CLASSES = {
    "mage": {
        "name": "Mage",
        "who_name": "{RM{rag",
        "tier": 1,
    },
    "thief": {
        "name": "Thief",
        "who_name": "{RT{rhi",
        "tier": 1,
    },
    "warrior": {
        "name": "Warrior",
        "who_name": "{RW{rar",
        "tier": 1,
    },
    "druid": {
        "name": "Druid",
        "who_name": "{RD{rru",
        "tier": 1,
    },
    "ranger": {
        "name": "Ranger",
        "who_name": "{RR{ran",
        "tier": 1,
    },
    "cleric": {
        "name": "Cleric",
        "who_name": "{RC{rle",
        "tier": 1,
    },
    "vampire": {
        "name": "Vampire",
        "who_name": "{RV{ram",
        "tier": 1,
    },

    "wizard": {
        "name": "Wizard",
        "who_name": "{BW{biz",
        "tier": 2,
        "parent_id": "mage",
    },
    "mercenary": {
        "name": "Mercenary",
        "who_name": "{BM{ber",
        "tier": 2,
        "parent_id": "thief"
    },
    "gladiator": {
        "name": "Gladiator",
        "who_name": "{BG{bla",
        "tier": 2,
        "parent_id": "fighter",
    },
    "sage": {
        "name": "Sage",
        "who_name": "{BS{bag",
        "tier": 2,
        "parent_id": "druid",
    },
    "strider": {
        "name": "Strider",
        "who_name": "{BS{btr",
        "tier": 2,
        "parent_id": "ranger",
    },
    "priest": {
        "name": "Priest",
        "who_name": "{BP{bri",
        "tier": 2,
        "parent_id": "cleric",
    },
    "lich": {
        "name": "Lich",
        "who_name": "{BL{bic",
        "tier": 2,
        "parent_id": "vampire",
    },
}

SELF_KEYWORDS = ["self"]
BANNED_NAME_PREFIXES = [] + SELF_KEYWORDS
BANNED_NAMES = [
    "root",
    "shell",
    "admin",
    "guest",
    "supervisor",
    "god",
    "bash",
]
