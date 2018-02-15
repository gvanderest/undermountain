from mud.inject import inject
from mud.module import Module


def format_field_value(name, value):
    FIELD_LENGTH = 20
    return "{}[{}]".format(name.ljust(FIELD_LENGTH, "."), value)


def in_room_edit_prompt(self):
    return ">"


@inject("Rooms")
def in_room_edit(self, Rooms, context=None, args=None, **kwargs):
    room = Rooms.get(context["room_id"]) if context else self.room

    args = list(args) if args else []

    if not args:
        self.echo(format_field_value("Name", room.name))

        self.echo("Description:")
        for line in room.description:
            self.echo(line)

        return

    command = args.pop(0).lower()

    if "name".startswith(command):
        name = " ".join(args)
        room.name = name
        self.echo("Room name set to: {}".format(name))
        room.save()

    elif "description".startswith(command):
        def description_edit_callback(context):
            room.description = context["lines"]
            room.save()

        self.client.start_edit_mode(description_edit_callback, context={
            "lines": room.description or [],
        })

    elif "done".startswith(command):
        self.echo("Exited room edit mode.")
        self.client.end_proxy_command(in_room_edit)

    else:
        return False  # Command not found


def room_edit_command(self, *args, **kwargs):
    self.client.start_proxy_command(in_room_edit)
    in_room_edit(self)


class BuildModule(Module):
    DESCRIPTION = "Allow players to build areas of the game"

    def __init__(self, game):
        super(BuildModule, self).__init__(game)
        self.game.register_command("redit", room_edit_command)
