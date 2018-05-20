from mud.inject import inject
from mud.module import Module


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
