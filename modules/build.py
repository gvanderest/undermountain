from mud.inject import inject
from mud.module import Module
from random import randint, choice
from utils.hash import get_random_hash

def format_field_value(name, value):
    FIELD_LENGTH = 20
    return "{}[{}]".format(name.ljust(FIELD_LENGTH, "."), value)


@inject("Rooms")
def in_room_edit(self, Rooms, context=None, args=None, **kwargs):
    room = Rooms.get(context["room_id"]) if context else self.room

    def display_redit_summary():
        self.echo(format_field_value("ID", room.id))
        self.echo(format_field_value("Name", room.name))
        self.echo(format_field_value("Vnum", room.vnum))

        self.echo("Description:")
        for line in room.description:
            self.echo(line)

    args = list(args) if args else []

    if not args:
        display_redit_summary()
        return

    command = args.pop(0).lower()

    if "name" == command:
        name = " ".join(args)
        room.name = name
        self.echo("Room name set to: {}".format(name))
        room.save()

    elif "vnum" == command:
        vnum = args.pop(0).lower()
        existing = Rooms.get({"area_vnum": room.area_vnum, "vnum": vnum})
        if existing:
            self.echo(
                "That vnum is already being used by a room in this area.")
            return

        room.vnum = vnum
        room.save()
        # TODO Iterate through rooms to re-iink things?

    # Require they type at least "desc"
    elif command.startswith("desc") and "description".startswith(command):
        def description_edit_callback(context):
            room.description = context["lines"]
            room.save()
            display_redit_summary()

        self.client.start_edit_mode(description_edit_callback, context={
            "lines": room.description or [],
        })

    elif "done" == command:
        self.echo("Exited room edit mode.")
        self.client.end_proxy_command(in_room_edit)

    else:
        return False  # Command not found


def room_edit_command(self, *args, **kwargs):
    self.client.start_proxy_command(in_room_edit)
    in_room_edit(self)


@inject("Mobs", "Races")
def in_mob_edit(self, args,  Mobs, Races, context=None, **kwargs):
    args = list(map(lambda a: a.lower(), args))
    if not args:
        self.echo("Do what with mobs?")
        self.echo("name <names>")
        self.echo("vnum <string>")
        self.echo("desc <editor>")
        self.echo("level <number>")
        self.echo("create <vnum>")
        self.echo("create")
        self.echo("race <race>")
        self.echo("medit show")
        return

    command = args.pop(0)
    self.echo(f"args:{args}")

    mob = Mobs.get(context["mob_id"]) if context else self.mob

    def display_medit_summary(display_mob):
        if display_mob:
            self.echo(format_field_value("Name", display_mob.name))
            self.echo(format_field_value("Vnum", display_mob.vnum))
            self.echo(format_field_value("Level", display_mob.stats.level.base))
            self.echo(format_field_value("Race", display_mob.race_ids[0]))
            self.echo(format_field_value("HP", display_mob.stats.hp.base))
            self.echo(format_field_value("Mana", display_mob.stats.mana.base))

            self.echo("Description:")
            for line in display_mob.description:
                self.echo(line)
        else:
            if display_mob is None:
                self.echo("Starting a generic mob.")
                display_mob = Mobs.save({
                    "area_id": self.room.area.id,
                    "area_vnum": self.room.area.vnum,
                    "vnum": get_random_hash()[:6],
                    "name": "Unnamed Mob",
                    "level": 1,
                    "description": [],
                    "title": "",
                    "bracket": "",
                    "experience": 0,
                    "experience_per_level": 3000,
                    "room_id": "",
                    "room_vnum": self.room,
                    "race_ids": ["human"],
                    "class_ids": ["adventurer"],
                    "stats": self.stats,
                    "settings": {},
                    "gender_id": "male",
                })
        return display_mob

    mob = display_medit_summary(mob)
    if "name" == command:

        name = " ".join(args)
        self.echo(f"Name {name}")
        mob.name = name
        self.echo("Mob name set to: {}".format(name))
        mob.save()
        display_medit_summary(mob)

    elif "race" == command:
        race = args.pop(0)
        race = Races.fuzzy_get(race)
        self.echo(f"Race {race.id}")
        if not race:
            self.echo("That race does not exist, please try again.")
            return

        mob.race_ids = [race.id]
        mob.save()
        display_medit_summary(mob)

    elif "create" == command:
        room = self.room
        area = room.area

        # Look up the existing Mob
        if args:
            mob_vnum = args.pop(0)
            new_mob = Mobs.get({"vnum": mob_vnum})

            if not new_mob:
                self.echo("The Mob VNUM you've requested does not exist.")
                return

        # Create the new Mob
        else:
            mob = Mobs.save({
                "area_id": self.room.area.id,
                "area_vnum": self.room.area.vnum,
                "vnum": self.vnum,
                "name": "Unnamed Mob",
                "level": 1,
                "description": [],
                "title": "",
                "bracket": "",
                "experience": 0,
                "experience_per_level": 3000,
                "room_id": "",
                "room_vnum": self.room,
                "race_ids": ["human"],
                "class_ids": ["adventurer"],
                "stats": dict(self.stats),
                "settings": {},
                "gender_id": "male",
            })

        # Save the Mob
        new_mob.save()
        mob.save

        # Save the area.
        area.save()

        self.echo("Mob {} has been created.".format(new_mob.vnum))
        self.echo()

    elif "vnum" == command:
        vnum = args.pop(0)
        self.echo(f"Vnum {vnum}")
        existing = Mobs.get({"area_vnum": self.area_vnum, "vnum": vnum})
        if existing:
            self.echo(
                "That vnum is already being used by a mob in this area.")
            return

        mob.vnum = vnum
        mob.save()
        display_medit_summary(mob)
        # TODO Iterate through rooms to re-iink things?

    elif "level" == command:
        level = args.pop(0)
        if level.isdigit():
            level = int(level)
            mana_gain = 0
            hp_gain = 0
            self.echo(f"Level {level}")
            for x in range(level):
                mana_gain += randint(10, 85)
                hp_gain += randint(20, 45)
            mob.stats.level.base = level
            mob.stats.hp.base = 100 + hp_gain
            mob.stats.mana.base = 100 + mana_gain
            self.echo(f"HP {mob.stats.hp.base}")
            self.echo(f"Mana {mob.stats.mana.base}")
            mob.save()
            display_medit_summary(mob)
            return

    # Require they type at least "desc"
    elif command.startswith("desc") and "description".startswith(command):
        def description_edit_callback(context):
            mob.description = context["lines"]
            mob.save()
            display_medit_summary(mob)

        self.client.start_edit_mode(description_edit_callback, context={
            "lines": mob.description or [],
        })
        mob.save()

    elif "done" == command or "quit" == command:
        self.echo("Exited room edit mode.")
        self.client.end_proxy_command(in_mob_edit)

    elif "show" == command:
        display_medit_summary(mob)

    else:
        return False  # Command not found


def mob_edit_command(self, *args, **kwargs):
    self.client.start_proxy_command(in_mob_edit)
    in_mob_edit(self, args)


def save_command(self, *args, **kwargs):
    self.save()
    self.echo(f"{self.__class__.__name__} Saved.")


@inject("Areas", "Rooms")
def area_command(self, args, Areas, Rooms, **kwargs):
    args = list(map(lambda a: a.lower(), args))
    if not args:
        self.echo("Do what with areas?")
        self.echo("area list")
        self.echo("area search <keyword>")
        self.echo("area create <vnum>")
        self.echo("area edit [vnum]")
        self.echo("area delete <vnum> confirm")
        return

    command = args.pop(0)

    if "list" == command:
        for area in Areas.query():
            self.echo("{} - {} - {}".format(
                area.id, area.vnum, area.name))
        return

    if "search" == command:
        if not args:
            self.echo("Keywords required.")
            self.echo("area search <keyword>")

        keyword = args.pop(0)

        results = []
        for area in Areas.query():
            if keyword in area.name.lower() or keyword in area.vnum.lower():
                results.append(area)

        if results:
            self.echo("Search results:")
            for area in results:
                self.echo("{} - {}".format(
                    area.vnum,
                    area.name,
                ))
        else:
            self.echo("No areas found for keyword: {}".format(keyword))

        return

    elif "create" == command:
        if not args:
            self.echo("Vnum required.")
            self.echo("area create <vnum>")
            return

        vnum = args.pop(0)
        area = Areas.get({"vnum": vnum})

        if area:
            self.echo("An area with vnum '{}' already exists.".format(vnum))
            return

        area = Areas.save({"vnum": vnum})
        self.echo("Area '{}' created.".format(area.vnum))

        room = Rooms.save({"area_id": area.id, "area_vnum": vnum})
        self.echo("Room vnum '{}:{}' with id {} created.".format(
            vnum, room.vnum, room.id))
        # TODO Load area editor

        return

    elif "delete" == command:
        if not args:
            self.echo("Vnum must be provided.")
            self.echo("area delete <vnum> confirm")
            return

        vnum = args.pop(0)

        if not args or args.pop(0) != "confirm":
            self.echo("You must confirm the deletion.")
            self.echo("area delete <vnum> confirm")
            return

        area = Areas.get({"vnum": vnum})
        if not area:
            self.echo("Area with vnum '{}' not found.".format(vnum))
            return

        area.delete()
        self.echo("Area '{}' deleted.".format(vnum))

        return

    elif "edit" == command:
        self.echo("Edit an area")


class BuildModule(Module):
    DESCRIPTION = "Allow players to build areas of the game"

    def __init__(self, game):
        super(BuildModule, self).__init__(game)
        self.game.register_command("area", area_command)
        self.game.register_command("redit", room_edit_command)
        self.game.register_command("save", save_command)
        self.game.register_command("medit", mob_edit_command)
