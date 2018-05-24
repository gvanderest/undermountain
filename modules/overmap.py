from modules.core import Areas
from mud.module import Module
from mud.inject import inject
from mud.collection import Collection, Entity, FileStorage
from utils.tablefy import tablefy


class Overmap(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage


@inject("Overmap", "Areas")
def overmaps_command(self, Areas, *args, **kwargs):
    # TO_DO Table-fy this.
    count = 0
    self.echo("Available Overmaps.")
    self.echo("{R+-------------------------------------------")
    self.echo("{w|Level   | Vis |  Name           |  Description")
    self.echo("{R+-------------------------------------------{w")
    for area in Areas.query():
        if not area.area_map:
            continue
        else:
            self.echo(f"{{R|{{w{area.min_level} - {area.max_level} |  {area.visibility} | {area.name:>15} |{area.description}")
            count += 1
    self.echo("{R+-------------------------------------------{x")
    self.echo(f"({count}) Overmap(s) found")


class OvermapModule(Module):
    DESCRIPTION = "Allow players to edit overmap."

    def __init__(self, game):
        super(OvermapModule, self).__init__(game)
        self.game.register_command("overmap_recall", overmap_recall)
        self.game.register_command("overmaps", overmaps_command)
        self.game.register_injector(Overmap)


def overmap_recall(self, area, *args, **kwargs):
    if not area.overmap_recall:
        set_actor_location(self, area, 0, 0)
    else:
        set_actor_location(self, area, area.overmap_recall[0], area.overmap_recall[1])


def set_actor_location(actor, area, new_x, new_y):
    actor.overmap_x = new_x
    actor.overmap_y = new_y
    actor.overmap = area.name

    area.actors[actor.name] = (new_x, new_y)


def is_actor_at(x, y, area):
    for loc in area.actors.items():
        if loc[0] == x and loc[1] == y:
            return True


def is_object_at(x, y, area):
    for loc in area.objects.items():
        if loc[0] == x and loc[1] == y:
            return True


def is_room_at(x, y, area):
    for loc in area.rooms.items():
        if loc[0] == x and loc[1] == y:
            return True


def draw_room(x, y, area):
    if is_actor_at(x, y, area):
        print("{R*")
    if is_object_at(x, y, area):
        print("{G!")
    if is_room_at(x, y, area):
        return "{BV"

    return area.color_maping[area.area_map[y][x]] + area.area_map[y][x]


def draw_map(self, area):

    # Find slice indexes for horizontal
    start_x = max(0, self.overmap_x - area.visibility)
    end_x = min(area.wdith - 1, self.overmap_x + area.visibility) + 1

    # Find slice indexes for vertical
    start_y = max(0, self.overmap_y - area.visibility)
    end_y = min(area.height - 1, self.overmap_y + area.visibility) + 1

    # Slice region
    map_slice = [
        row[start_x:end_x] for row in area.area_map[start_y:end_y]
    ]

    xcount = 0
    ycount = 0
    # Draw
    print(f"Area: {area.name}")
    for line in map_slice:
        for room in line:
            draw_room(xcount + start_x, ycount + start_y, area)

    print(f"Location:  {self.overmap_x}.{self.overmap_y}")
    print(f"Nearby: {self.name}")


def overmap_walk(self, direction, area):
    if direction == "north":
        if self.overmap_y > 0:
            set_actor_location(self, area, self.overmap_x, self.overmap_y - 1)
        else:
            print(f"You are at the northern boarder of {area.name}")
    if direction == "south":
        if self.overmap_y < area.height - 1:
            set_actor_location(self, area, self.overmap_x, self.overmap_y + 1)
        else:
            print(f"You are at the southern boarder of {area.name}")
    if direction == "east":
        if self.overmap_x < area.width -1:
            set_actor_location(self, area, self.overmap_x + 1, self.overmap_y)
        else:
            print(f"You are at the eastern boarder of {area.name}")
    if direction == "west":
        if self.overmap_x > 0:
            set_actor_location(self, area, self.overmap_x - 1, self.overmap_y)
        else:
            print(f"You are at the western boarder of {area.name}")
    # if direction == "up":
    # if direction == "down":

