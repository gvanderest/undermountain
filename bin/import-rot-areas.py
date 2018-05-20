#!/usr/bin/env python
"""Import ROT Areas to Undermountain."""

from glob import glob
from settings import ROT_DATA_PATH, DATA_PATH
from utils.hash import get_random_hash
from utils.json import json


areas = {}
rooms = {}
objects = {}
subroutines = {}
actors = {}
exits = {}


ROOM_FLAG_MAP = {
    "dark": 2**0,
    "bank": 2**1,
    "no_mob": 2**2,
    "indoors": 2**3,
    "bounty_office": 2**4,
    "no_quit": 2**5,
    "no_potion": 2**6,
    "no_fly": 2**7,
    "no_improved_invis": 2**8,
    "private": 2**9,
    "safe": 2**10,
    "solitary": 2**11,
    "pet_shop": 2**12,
    "no_recall": 2**13,
    "admin_only": 2**14,
    "immortal_only": 2**15,
    "hero_only": 2**16,
    "newbie_only": 2**17,
    "law": 2**18,
    "no_where": 2**19,
    "clan_entrance": 2**20,
    "locked": 2**21,
    "arena_wait": 2**22,
    "arena": 2**23,
    "no_gate": 2**24,
    "no_magic": 2**25,
    "free_pk": 2**26,
    "mount_shop": 2**27,
    "no_transport": 2**28
}

ROOM_FLAG2_MAP = {
    "fuel_shop": 2**0,
    "engine_shop": 2**1,
    "weapon_shop": 2**2,
    "hull_shop": 2**3,
    "repair_shop": (2**4, 2**17),
    "armor_shop": 2**5,
    "hangar": 2**6,
    "special_hull_shop": 2**7,
    "airship_only": 2**8,
    "no_pk": 2**9,
    "no_public": 2**10,
    "airship_safe": 2**11,
    "special_weapon_shop": 2**12,
    "no_hunger": 2**13,
    "speical_engine_shop": 2**14,
    "locksmith": 2**15,
    "air_arena": 2**16,
    "nytek_hull_shop": 2**18,
    "nytek_weapon_shop": 2**19,
    "nytek_engine_shop": 2**20,
    "air_pk_not_safe": 2**21,
    "for_rent": 2**22,
    "rpt_room": 2**23,
    "no_rot_death": 2**24,
    "home": 2**25,
    "work_office": 2**26,
    "bathroom": 2**27,
    "loading_docks": 2**28,
    "for_sale": 2**29,
    "public_room": 2**30,
    "courier": 2**31
}

EXIT_FLAGS_MAP = {
    "door": 2**0,
    "closed": 2**1,
    "locked": 2**2,
    "pick_proof": 2**3,
    "no_pass_door": 2**4,
    "pick_easy": 2**5,
    "pick_hard": 2**6,
    "pick_infuriating": 2**7,
    "no_close": 2**8,
    "no_lock": 2**9,
    "secret": 2**10,
    "no_bump": 2**11,
    "original_door": 2**12,
    "area_border": 2**13
}

ROOM_SECTORS_MAP = {
    "building": 0,
    "city": (1, 21),
    "field": 2,
    "forest": 3,
    "hill": 4,
    "mountain": 5,
    "water": (6, 7),
    "??unused??": 8,
    "air": 9,
    "desert": 10,
    "road": 11,
    "inn": 12,
    "temple": 14,
    "guild": 15,
    "swamp": 16,
    "jungle": 17,
    "dungeon": 18,
    "garden": 19,
    "cavern": 20,
    "airship_port": 22,
    "airship_hangar": 23,
    "player_home": 24,
    "player_hangar": 25,
    "dock": 26,
    "bridge": 27,
    "battlefield": 29,
    "factory": 30,
    "junkyard": 31,
    "empty_lot": 32,
    "underwater": 33,
}

FLAGS_INFERRED_FROM_SECTORS_MAP = {
    "noswim": 7
}


def generate_hash():
    return get_random_hash()


def parse_mobile(filename, lines):
    mobile = {
        "id": generate_hash(),
        "description": [],
        "effects": [],
        "raw_extra": [],
    }
    state = "vnum"
    for index, line in enumerate(lines):
        line_ends_string = line.endswith("~")
        cleaned = line.rstrip("~")
        parts = cleaned.split(" ")
        if state == "vnum" and line != "#MOBILES":
            if not line:
                continue
            assert line.startswith("#"), "Line doesn't start with hash: {}" \
                                         .format(line)
            mobile["vnum"] = int(line[1:])
            state = "keywords"

        elif state == "keywords":
            mobile["keywords"] = parts
            state = "name"

        elif state == "name":
            mobile["name"] = cleaned
            state = "room_name"

        elif state == "room_name":
            mobile["room_name"] = cleaned
            state = "something1"

        elif state == "something1":
            if line_ends_string:
                mobile["something1"] = cleaned
            state = "description"

        elif state == "description":
            if line.endswith("~"):
                if cleaned:
                    mobile["description"].append(cleaned)
                state = "race"
            else:
                mobile["description"].append(line)

        elif state == "race":
            mobile["race_id"] = cleaned
            state = "flags1"

        elif state == "flags1":
            mobile["raw_flags1"] = line
            state = "level_and_damage"

        elif state == "level_and_damage":
            mobile["raw_level_and_damage"] = line
            state = "armors"

        elif state == "armors":
            mobile["raw_armors"] = line
            state = "flags2"

        elif state == "flags2":
            mobile["raw_flags2"] = line
            state = "position_and_gender"

        elif state == "position_and_gender":
            mobile["raw_position_and_gender"] = line
            state = "flags3"

        elif state == "flags3":
            mobile["raw_flags3"] = line
            state = "extra"

        elif state == "extra":
            mobile["raw_extra"] = []

        else:
            print("UNHANDLED", line)

    return mobile


def parse_area(filename, lines):
    area = {
        "id": generate_hash(),
        "vnum": filename
    }
    for line in lines:
        if not line:
            continue
        parts = line.split(" ")
        if parts[0] == "Name":
            area["name"] = " ".join(parts[1:]).rstrip("~")
        elif parts[0] == "Builders":
            area["builders"] = parts[1:]
            area["builders"][-1] = area["builders"][-1].rstrip("~")
            if area["builders"][0] == "None":
                area["builders"] = []
        elif parts[0] == "VNUMs":
            area["vnums"] = (int(parts[1]), int(parts[2]))
        elif parts[0] == "Credits":
            area["credits"] = " ".join(parts[1:]).rstrip("~")
        elif parts[0] == "Security":
            area["security"] = int(parts[1])
        elif parts[0] == "Recall":
            area["recall_vnum"] = int(parts[1])
        elif parts[0] == "Faction":
            area["faction_id"] = "" if parts[1] == "~" else \
                parts[1].rstrip("~")
        elif parts[0] == "AQpoints":
            area["area_quest_points"] = int(parts[1])
        elif parts[0] == "Realm":
            area["realm_id"] = int(parts[1])
        elif parts[0] == "Zone":
            area["zone_id"] = int(parts[1])
        else:
            print("UNHANDLED", line)

    areas[area["vnum"]] = area
    return area


def parse_object(filename, lines):
    return None


def parse_room(filename, lines):
    """Convert areafile lines into dict representing Room."""
    state = "vnum"
    room = {
        "id": generate_hash(),
        "area_vnum": filename,
        "description": [],
        "extra_descriptions": {},
        "exits": {}
    }

    DIRECTION_MAPPINGS = ["north", "east", "south", "west", "up", "down"]

    for index, line in enumerate(lines):
        try:
            if state == "vnum":
                if line.startswith("#"):
                    room["vnum"] = line[1:]
                    state = "name"
                else:
                    raise Exception("Invalid room format")

            elif state == "name":
                room["name"] = line.rstrip("~")
                state = "unknown"

            elif state == "unknown":
                state = "description"

            elif state == "description":
                if line.endswith("~"):
                    state = "flags1"
                else:
                    room["description"].append(line)

            elif state == "flags1":
                state = "flags2"
                flag_parts = line.split(" ")
                raw_flags = int(flag_parts[1])
                raw_flags2 = int(flag_parts[2])
                raw_sector = int(flag_parts[3])
                room["raw_flags1"] = raw_flags
                flags = set()

                for flag_name, bitvalues in ROOM_FLAG_MAP.items():
                    if not isinstance(bitvalues, tuple):
                        bitvalues = (bitvalues,)
                    for bitvalue in bitvalues:
                        if raw_flags & bitvalue:
                            flags.add(flag_name)

                for flag_name, bitvalues in ROOM_FLAG2_MAP.items():
                    if not isinstance(bitvalues, tuple):
                        bitvalues = (bitvalues,)
                    for bitvalue in bitvalues:
                        if raw_flags2 & bitvalue:
                            flags.add(flag_name)

                room["flags"] = list(flags)

            elif state == "flags2":
                room["raw_region_flag"] = line
                state = "meta"

            elif state == "meta":
                # Special?
                if line.startswith("S"):
                    print("TODO: Parse 'S' lines")

                # Direction
                elif line.startswith("D"):
                    state = "exit_name"
                    direction_index = int(line[1])
                    direction_id = DIRECTION_MAPPINGS[direction_index]
                    room_exit = {
                        "name": "",
                        "direction_id": direction_id,
                        "description": []
                    }

                # Extra Description
                elif line.startswith("E"):
                    state = "extra_desc_name"
                    extra_desc = {
                        "keywords": "",
                        "description": []
                    }

                # Mana and HP Healing
                elif line.startswith("M"):
                    print("TODO: Properly parse mana/hp heal")
                    room["raw_mana_heal"] = line

                # Mobprogs/Subroutines
                elif line.startswith("X"):
                    print("TODO: Attach mobprogs properly")

                # O? Unknown
                elif line.startswith("O"):
                    print("TODO: Figure out what a room's O meta does", line)

                # Q? Unknown
                elif line.startswith("Q"):
                    print("TODO: Figure out what a room's Q meta does", line)

                # B? Unknown
                elif line.startswith("B"):
                    print("TODO: Figure out what a room's B meta does", line)

                # Z? Unknown
                elif line.startswith("Z"):
                    print("TODO: Figure out what a room's Z meta does", line)

                # Y? Unknown
                elif line.startswith("Y"):
                    print("TODO: Figure out what a room's Y meta does", line)

                # R? Unknown
                elif line.startswith("R"):
                    print("TODO: Figure out what a room's R meta does", line)

                # T? Unknown
                elif line.startswith("T"):
                    print("TODO: Figure out what a room's T meta does", line)

                # V? Unknown
                elif line.startswith("V"):
                    print("TODO: Figure out what a room's V meta does", line)

                # P? Unknown
                elif line.startswith("P"):
                    print("TODO: Figure out what a room's P meta does", line)

                # Clan ownership
                elif line.startswith("C"):
                    room["clan_id"] = line[2:-1]

                # Whitespace is allowed
                elif not line:
                    pass

                # Error
                else:
                    raise Exception("Invalid meta section")

            elif state == "extra_desc_name":
                if line.endswith("~"):
                    state = "extra_desc_desc"
                else:
                    extra_desc["keywords"] += line

            elif state == "extra_desc_desc":
                if line.endswith("~"):
                    keywords = extra_desc["keywords"]
                    room["extra_descriptions"][keywords] = extra_desc
                    state = "meta"
                else:
                    extra_desc["description"].append(line)

            elif state == "exit_name":
                if line.endswith("~"):
                    state = "exit_description"
                else:
                    room_exit["name"] += " " + line

            elif state == "exit_description":
                if line.endswith("~"):
                    state = "exit_flags"
                else:
                    room_exit["description"].append(line)

            elif state == "exit_flags":
                print("TODO: Parse exit flags", line)
                parts = line.split(" ")
                room_exit["raw_flags1"] = parts[0]
                room_exit["raw_flags2"] = parts[1]
                room_exit["room_vnum"] = parts[2]
                room["exits"][room_exit["direction_id"]] = room_exit
                state = "meta"

            else:
                raise Exception("Unhandled room line")

        except Exception as e:
            print("Exception state:{} file:{} index:{} line:{}".format(
                state, filename, index, line))
            raise

    rooms[room["vnum"]] = room
    return room


def parse_special(filename, lines):
    return None


def parse_reset(filename, lines):
    return None


def parse_shop(filename, lines):
    return None


def parse_mobprog(filename, lines):
    return None


functions = {
    "area": parse_area,
    "mobile": parse_mobile,
    "object": parse_object,
    "room": parse_room,
    "special": parse_special,
    "reset": parse_reset,
    "shop": parse_shop,
    "mobprog": parse_mobprog,
}


# Some symbols that improperly trigger bad parsing
ignore_lines_starting_with = [
    '#rhg',
    '#rh',
    '#newthalos',
    '#goddesstatuemoonshae',
    '#questurias',
    '#dernallforestblocker',
    '#invulnerabledruid',
    '#combaturias',
    '#sos',
    '#som',
    '#sea',
    '#norland',
    '#candlekeep',
    '#alaron',
    '#snowdown',
    '#gwynneth',
    '#moray',
    '#norheim',
    '#define',
    '#6~',
    '#oman',
    '#archipelago',
    '#flamsterd',
    '#isles',
    '#gardengirl',
    '#passageopener',
    '#passageopener,',
    '#moonshaequest',
]

for path in glob(ROT_DATA_PATH + "/area/*.are"):
    section = None
    content = []
    print("Processing {}..".format(path))
    filename = path.split("/")[-1].split(".")[0]

    for line in open(path, "r"):
        line = line.rstrip("\r\n")
        parts = line.lower().split(' ')
        if line.startswith("#") and parts[0] not in \
                ignore_lines_starting_with:

            # Some room descriptions contain hash symbols
            if line.startswith("##") or line.startswith("#@"):
                continue

            if line == "#0":
                continue

            if section is not None and content:
                try:
                    function = functions[section]
                    result = function(filename, content)
                except Exception as e:
                    print("EXCEPTION {} SECTION {}".format(
                        filename, section))
                    for index, line in enumerate(content):
                        print("{}: {}".format(index, line))

                    print("=" * 79)
                    raise

            content = []

            if line == "#AREADATA":
                section = "area"
            elif line == "#MOBILES":
                section = "mobile"
            elif line == "#OBJECTS":
                section = "object"
            elif line == "#ROOMS":
                section = "room"
            elif line == "#SPECIALS":
                section = "special"
            elif line == "#RESETS":
                section = "reset"
            elif line == "#SHOPS":
                section = "shop"
            elif line == "#MOBPROGS":
                section = "mobprog"

        if line not in ["#AREADATA", "#ROOMS"]:
            content.append(line)

for room in rooms.values():
    room["area_id"] = areas[room["area_vnum"]]["id"]

    for room_exit in room["exits"].values():
        room_vnum = room_exit["room_vnum"]
        room_for_exit = rooms.get(room_vnum, None)

        if room_for_exit:
            room_exit["room_id"] = room_for_exit["id"]
        else:
            print("ROOM NOT FOUND FOR EXIT", room_vnum)

for area in areas.values():
    area["rooms"] = [
        room
        for room in rooms.values()
        if room["area_vnum"] == area["vnum"]
    ]

    output_path = "{}/{}/{}.json".format(DATA_PATH, "areas", area["vnum"])
    with open(output_path, "w") as fh:
        fh.write(json.dumps(area))