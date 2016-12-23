#!/usr/bin/env python
"""Import ROT Areas to Undermountain."""
import sys
sys.path.append("..")

from glob import glob
from settings import ROT_DATA_FOLDER

all_areas = {}


def generate_hash():
    return "abc213"

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
    return area

def parse_object(filename, lines):
    return None

def parse_room(filename, lines):
    return None

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


class Boop(Exception):
    pass


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
    '#oman',
    '#archipelago',
    '#flamsterd',
    '#isles',
    '#gardengirl',
    '#passageopener',
    '#passageopener,',
    '#moonshaequest',
]

for filename in glob(ROT_DATA_PATH + "/area/*.are"):
    section = None
    content = []
    print("Processing {}..".format(filename))

    try:
        for line in open(filename, "r"):
            line = line.rstrip("\r\n")
            parts = line.lower().split(' ')
            if line.startswith("#") and parts[0] not in \
                    ignore_lines_starting_with:
                if line == "#0":
                    continue

                if section is not None and content:
                    function = functions[section]
                    result = function(filename, content)
                    # if result is None:
                        # print("Incomplete: {} {} {}".format(
                            # filename, section, content[0]
                        # ))
                    # print(section, function(filename, content))

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

            content.append(line)
    except Boop:
        continue
