import json
import sys
import random
from collections import Counter

"""
This script can be used to import an file of an overmap map into Undermountain.
No warranty is provided, YMMV. It was created by penguin of Waterdeep.
The general shape of the socials.are file for purposes of this importer is:

############Undermountain overmap Map Format############
name Bitterwoods
minlevel 0
maxlevel 101
visibility 10
description The Main overmap map for Bitterwoods
##########################################################
<ascii map here>
"""


def get_random_hash():
    """Get a randomized hash."""
    return "%040x" % random.getrandbits(40 * 4)


def create_color_maping(area_map):
    # Get a set of all characters used
    alphabet = []
    for line in area_map:
        alphabet += list(set(line))

    alphabet = set(alphabet)
    color_mapping = {}
    for index, letter in enumerate(alphabet):
        # for each letter assign it a random color code in color_mapping
        color_mapping.update({letter: f"{{{index % 10}"})
    return color_mapping


class overmap:
    def __init__(self,
                 name,
                 min_level,
                 max_level,
                 visibility,
                 description,
                 area_map):
        self.vnum = name
        self.name = name
        self.description = description
        self.min_level = min_level
        self.max_level = max_level
        self.visibility = visibility
        self.area_map = area_map
        self.height = len(area_map)
        self.width = len(area_map[0])
        self.color_mapping = create_color_maping(area_map)
        self.actors = []
        self.flags = []
        self.id = get_random_hash()
        self.scripts = []
        self.rooms = []
        self.objects = []


filename = sys.argv[-1]
area_map = []
if filename:
    with open(filename, 'r') as f:
        overmap = f.readlines()
        count = 0

    while count < len(overmap):
        if overmap[count].startswith("name"):
            name = overmap[count].rstrip().split(" ", 1)[1]
            count += 1
            continue
        if overmap[count].startswith("minlevel"):
            min_level = overmap[count].rstrip().split(" ")[1]
            count += 1
            continue
        if overmap[count].startswith("desc"):
            # grab everything after the first word of the lne
            description = overmap[count].rstrip().split(' ', 1)[1]
            count += 1
            continue
        if overmap[count].startswith("maxlevel"):
            max_level = overmap[count].rstrip().split(" ")[1]
            count += 1
            continue
        if overmap[count].startswith("visibility"):
            visibility = overmap[count].rstrip().split(" ")[1]
            count += 1
            continue
        if overmap[count].startswith("#") or overmap[count].rstrip() == "":
            count += 1
            continue

        area_map.append(overmap[count].rstrip())
        count += 1

    area = overmap(name, min_level, max_level, visibility, description, area_map)

    fname = area.name + ".json"
    sf = open(fname, "w")
    sf.write(json.dumps(area.__dict__, sort_keys=False, indent=4, separators=(',', ':')))
    sf.close()
    print("{} file written.".format(fname))

else:
    print("Import failed: file not supplied.")