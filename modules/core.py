from mud.module import Module
from mud.collection import Collection, Entity, FileStorage
from mud.inject import inject
from utils.hash import get_random_hash

import gevent
import settings


@inject("Areas")
def areas_command(self, Areas, **kwargs):
    """List all Areas available in the Game."""
    self.echo("List of Areas:")
    for area in Areas.query():
        self.echo("* {} (vnum '{}')".format(area.name, area.vnum))


@inject("Rooms")
def goto_command(self, args, Rooms, **kwargs):
    """Go to a certain Room by its ID or VNUM."""
    if not args:
        self.echo("Please specify a room ID or VNUM.")
        return

    room_id_or_vnum = args.pop(0)
    room = Rooms.get(room_id_or_vnum) or Rooms.get({"vnum": room_id_or_vnum})

    if not room:
        self.echo("Room not found.")
        return

    self.act("{self.name} disappears suddenly.")
    self.room_id = room.id
    self.room_vnum = room.vnum
    self.save()
    self.act("{self.name} appears suddenly.")
    self.force("look")


def fail_command(self, **kwargs):
    """Force an Exception to occur."""
    raise Exception("Testing exceptions.")


def channel_command(self, name, message, **kwargs):
    channel = settings.CHANNELS[name]

    if not message:
        self.echo("Channel toggling is not yet supported.")
        return

    def replace(template):
        template = template.replace("{name}", self.name)
        template = template.replace("{message}", message)
        return template

    self.echo(replace(channel["echo_to_self"]))
    self.game.echo(replace(channel["echo_to_others"]), exclude=[self])


@inject("Directions", "Rooms")
def unlink_command(self, args, Directions, Rooms, **kwargs):
    if not args:
        self.echo("Link which exit to which room?")
        return

    direction_id = args.pop(0)
    direction = Directions.fuzzy_get(direction_id)

    if not direction:
        self.echo("That's not a valid direction.")
        return

    room = self.room

    if not room.exits.get(direction.id, None):
        self.echo("That exit does not exist.")
        return

    other_room = Rooms.get({"vnum": room.exits[direction.id]["room_vnum"]})

    counter_exit = other_room.exits.get(direction.opposite_id, None)
    if counter_exit and counter_exit["room_vnum"] == room.vnum:
        del other_room.exits[direction.opposite_id]
        other_room.save()
        other_room.area.save()

    del room.exits[direction.id]
    room.save()
    room.area.save()

    self.echo("The link to the {} to room {} has been removed.".format(
        direction.colored_name, other_room.vnum))


@inject("Directions", "Rooms")
def link_command(self, args, Directions, Rooms, **kwargs):
    if not args:
        self.echo("Link which exit to which room?")
        return

    direction_id = args.pop(0)

    if not args:
        self.echo("Link it to which room?")
        return

    room_vnum = args.pop(0)

    direction = Directions.fuzzy_get(direction_id)
    if not direction:
        self.echo("That's not a valid direction.")
        return

    room = self.room

    if room.exits.get(direction.id, None):
        self.echo("That exit already has a room linked to it.")
        return

    other_room = Rooms.get({"vnum": room_vnum})

    if other_room.exits.get(direction.opposite_id, None):
        self.echo(
            "The other room already has an exit in the opposite direction.")
        return

    room.exits[direction.id] = {"room_vnum": other_room.vnum}
    room.save()
    room.area.save()

    other_room.exits[direction.opposite_id] = {"room_vnum": room.vnum}
    other_room.save()
    other_room.area.save()

    self.echo("A link to the {} has been created to room {}".format(
        direction.colored_name, other_room.vnum))


@inject("Areas", "Rooms", "Directions")
def dig_command(self, args, Areas, Rooms, Directions, **kwargs):
    if not args:
        self.echo("Dig in which direction?")
        return

    direction_id = args.pop(0)

    direction = Directions.fuzzy_get(direction_id)
    if not direction:
        self.echo("That's not a valid direction.")
        return

    room = self.room

    exit = room.exits.get(direction.id, None)
    if exit:
        self.echo("That direction already has an exit.")
        return

    area = room.area

    # Look up the existing Room
    if args:
        room_vnum = args.pop(0)
        new_room = Rooms.get({"vnum": room_vnum})

        if not new_room:
            self.echo("The Room VNUM you've requested does not exist.")
            return

    # Create the new Room
    else:
        new_room = Rooms.save({
            "area_id": area.id,
            "area_vnum": area.vnum,
            "vnum": get_random_hash()[:6],
            "name": "Unnamed Room",
            "description": [],
            "exits": {},
        })

    # Link the Rooms
    new_room.exits[direction.opposite_id] = {"room_vnum": room.vnum}
    new_room.save()
    room.exits[direction.id] = {"room_vnum": new_room.vnum}
    room.save()

    # Save the area.
    area.save()

    self.echo("Room {} to the {} has been created.".format(
        new_room.vnum, direction.colored_name))

    self.echo()

    self.force(direction.id)


@inject("Actors", "Objects", "Directions")
def look_command(self, args, Actors, Objects, Directions, **kwargs):
    room = self.room

    self.echo("{{B{} {{x[{{WLAW{{x] {{R[{{WSAFE{{R]{{x".format(room["name"]))
    self.echo("(ID: {}) (VNUM: {}) (Area: {})".format(
        room["id"], room["vnum"], room["area_vnum"]))

    for index, line in enumerate(room.description):
        if index == 0:
            line = "{x   " + line
        self.echo(line)

    self.echo()

    exit_names = []
    door_names = []

    for direction in Directions.query():
        exit = room.exits.get(direction.id, None)
        if exit:
            exit_names.append(direction.colored_name)

    exits_line = "{{x[{{GExits{{g:{{x {}{{x]   " \
        "{{x[{{GDoors{{g:{{x {}{{x]   ".format(
            " ".join(exit_names) if exit_names else "none",
            " ".join(door_names) if door_names else "none",
        )
    self.echo(exits_line)

    spec = {"room_id": room["id"]}
    for actor in Actors.query(spec):
        self.echo("{} is standing here.".format(actor["name"]))

    for obj in Objects.query(spec):
        self.echo("{} is on the ground here.".format(obj["name"]))


def quit_command(self, **kwargs):
    self.echo("You're logging out...")
    self.quit()


def say_command(self, message, **kwargs):
    if not message:
        self.echo("Say what?")
        return

    say_data = {"message": message}
    say = self.trigger("before:say", say_data)
    if say.blocked:
        return

    self.echo("{{MYou say {{x'{{m{}{{x'".format(message))
    self.act("{M{self.name} says {x'{m{message}{M{x'", {
        "message": message,
    })

    self.trigger("after:say", say_data, unblockable=True)


@inject("Directions", "Rooms")
def direction_command(self, name, Directions, Rooms, **kwargs):
    room = self.room

    if not room:
        self.echo("You aren't anywhere.")
        return

    exit = room.exits.get(name, None)
    if not exit:
        self.echo("You can't go that way.")
        return

    direction = Directions.get(name)

    walk_data = {"direction": name}
    walk = self.trigger("before:walk", walk_data)

    if walk.blocked:
        return

    new_room = Rooms.get({"vnum": exit["room_vnum"]})

    if not new_room:
        self.echo("The place you're walking to doesn't appear to exist.")
        return

    enter_data = {"direction": direction.opposite}
    enter = self.trigger("before:enter", enter_data)

    if enter.blocked:
        return

    self.act("{self.name} leaves " + direction.colored_name)
    self.room_id = new_room.id
    self.save()
    self.act("{self.name} has arrived.")

    self.trigger("after:enter", enter_data, unblockable=True)
    self.trigger("after:walk", walk_data, unblockable=True)

    self.force("look")

    return 0.5


def score_command(self, **kwargs):
    self.echo("{{GName{{g:{{x {} {}".format(self.name, self.title))
    self.echo("{{GExperience{{g:{{x {}".format(self.experience))


@inject("Characters")
def who_command(self, Characters, **kwargs):
    self.echo("{GThe Visible Mortals and Immortals of Waterdeep")
    self.echo("{g" + ("-" * 79))

    count = 0
    for actor in Characters.query({"online": True}):
        count += 1

        self.echo("{{x{} {} {} {} {{x[.{{BN{{x......] {} {}".format(
            str(actor.level).rjust(3),
            actor.gender.colored_short_name,
            actor.races[0].colored_name,
            actor.classes[0].colored_short_name,
            actor.name,
            actor.title if actor.title else "",
        ))
    self.echo()
    self.echo(
        "{{GPlayers found: {{x{}   "
        "{{GTotal online: {{x{}   "
        "{{GMost on today: {{x{}".format(
            count,
            count,
            count,
        ))


@inject("Characters")
def delete_command(self, Characters, **kwargs):
    self.echo("Removing your character from the game.")
    Characters.delete(self)
    self.quit(skip_save=True)


def save_command(self, **kwargs):
    self.echo("Your character has been saved.")


def title_command(self, message, **kwargs):
    self.title = message
    self.save()
    if message:
        self.echo("Title set to: {}".format(self.title))
    else:
        self.echo("Title cleared.")


class Actor(Entity):
    DEFAULT_DATA = {
        "name": "",
        "title": "",
        "bracket": "",
        "level": 1,
        "experience": 0,
        "room_id": "",
        "room_vnum": settings.INITIAL_ROOM_VNUM,
        "race_ids": ["human"],
        "class_ids": ["adventurer"],
    }

    @property
    @inject("Classes")
    def classes(self, Classes):
        return [Classes.get(class_id) for class_id in self.class_ids]

    @property
    @inject("Races")
    def races(self, Races):
        return [Races.get(race_id) for race_id in self.race_ids]

    @property
    @inject("Genders")
    def gender(self, Genders):
        return Genders.get(self.gender_id)

    @property
    @inject("Rooms")
    def room(self, Rooms):
        room = Rooms.get(self.room_id)

        save_room = False
        if not room:
            save_room = True
            room = Rooms.get({"vnum": self.room_vnum})
            if not room:
                save_room = True
                room = Rooms.get({"vnum": settings.INITIAL_ROOM_VNUM})

        if save_room:
            self.room_id = room.id
            self.room_vnum = room.vnum
            self.save()

        return room

    @property
    def connection(self):
        return self.game.connections.get(self.connection_id, None)

    @property
    def client(self):
        if not self.connection:
            return None
        return self.connection.client

    def say(self, message):
        say_command(self, message=message)

    def save(self):
        self.collection.save(self)

    def quit(self, skip_save=False):
        if not self.client:
            return
        self.client.quit()
        self.online = False

        if not skip_save:
            self.save()

    def force(self, message):
        if not self.client:
            return
        self.client.handle_input(message)

    def echo(self, message=""):
        if not self.client:
            return

        self.client.writeln(message)

    def emit_event(self, event):
        return self.room.emit_event(event)

    def trigger(self, type, data=None, unblockable=False):
        event = self.generate_event(type, data, unblockable=unblockable)
        if unblockable:
            gevent.spawn(self.emit_event, event)
            return event
        else:
            return self.emit_event(event)

    def act(self, template, data=None):
        Actors, Characters = self.game.get_injectors("Actors", "Characters")
        if data is None:
            data = {}

        data["self"] = self

        room_id = self.room_id

        message = template

        for collection in (Characters, Actors):
            for actor in collection.query({"room_id": room_id}):
                if actor == self:
                    continue

                if "{message}" in message:
                    message = message.replace("{message}", data["message"])
                if "{self.name}" in message:
                    message = message.replace("{self.name}", data["self"].name)

                actor.echo(message)


class Account(Entity):
    pass


class Accounts(Collection):
    ENTITY_CLASS = Account
    STORAGE_CLASS = FileStorage


class Object(Entity):
    pass


class Character(Actor):
    pass


class Area(Entity):
    pass


class Areas(Collection):
    ENTITY_CLASS = Area
    STORAGE_CLASS = FileStorage

    @inject("Rooms", "Actors", "Objects", "Subroutines")
    def hydrate(self, record, Rooms, Objects, Actors, Subroutines):
        """Load the Area from the file."""

        # Ensure all records have the Area's information in them
        keys = ["rooms", "actors", "objects", "subroutines"]
        for key in keys:
            for entity in record[key]:
                entity["area_vnum"] = record["vnum"]
                entity["area_id"] = record["id"]

        # Save all attached records
        [Rooms.save(room) for room in record.pop("rooms")]
        [Objects.save(obj) for obj in record.pop("objects")]
        [Actors.save(actor) for actor in record.pop("actors")]
        [Subroutines.save(subroutine) for subroutine in
            record.pop("subroutines")]

        return record

    @inject("Rooms", "Actors", "Objects", "Subroutines")
    def dehydrate(self, record, Rooms, Actors, Objects, Subroutines):
        """Save the Area to a file."""

        query_args = [{"area_vnum": record["vnum"]}]
        query_kwargs = {"as_dict": True}

        record["rooms"] = list(Rooms.query(*query_args, **query_kwargs))
        record["actors"] = list(Actors.query(*query_args, **query_kwargs))
        record["objects"] = list(Objects.query(*query_args, **query_kwargs))
        record["subroutines"] = list(Subroutines.query(
            *query_args, **query_kwargs))

        scrub_keys = ["area_id", "area_vnum"]
        keys = ["rooms", "actors", "objects", "subroutines"]
        for key in keys:
            for entity in record[key]:
                for scrub_key in scrub_keys:
                    if scrub_key in entity:
                        del entity[scrub_key]

        return record

    def post_delete(self, record):
        """Remove all related Entities."""
        pass


class Room(Entity):
    DEFAULT_DATA = {
        "name": "",
        "exits": {},
        "description": [],
    }

    @property
    @inject("Actors", "Characters", "Objects")
    def children(self, Actors, Characters, Objects):
        # TODO Make this flexible, to define model relationships?
        for collection in (Actors, Characters, Objects):
            for entity in collection.query({"room_id": self.id}):
                yield entity

    def emit_event(self, event):
        """Handle the Event for this level and its children, then emit up."""
        for entity in self.children:
            event = entity.handle_event(event)

            if event.blocked:
                return event

        # TODO get the event back from the Area
        event = self.handle_event(event)

        return event

    @property
    @inject("Areas")
    def area(self, Areas):
        """Get the Room's Area."""
        return Areas.get(self.area_id) or Areas.get({"vnum": self.area_vnum})


class Direction(Entity):
    pass


class Rooms(Collection):
    ENTITY_CLASS = Room


class Subroutine(Entity):
    def execute(self, entity, event):
        try:
            compiled = \
                compile(self.code, "subroutine:{}".format(self.id), "exec")

            def wait(duration):
                gevent.sleep(duration)

            context = dict(event.data)
            context.update({
                "self": entity,
                "target": event.source,
                "event": event,
                "wait": wait,
            })

            exec(compiled, context, context)
        except Exception as e:
            self.game.handle_exception(e)


class Subroutines(Collection):
    ENTITY_CLASS = Subroutine


class Behavior(Entity):
    @property
    @inject("Subroutines")
    def subroutine(self):
        return Subroutines.get({"vnum": self.subroutine_vnum})


class Behaviors(Collection):
    ENTITY_CLASS = Behavior
    STORAGE_CLASS = FileStorage


class Characters(Collection):
    STORAGE_CLASS = FileStorage
    STORAGE_FILENAME_FIELD = "name"
    ENTITY_CLASS = Character


class Genders(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage


class Classes(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage


class Races(Collection):
    ENTITY_CLASS = Entity
    STORAGE_CLASS = FileStorage


class Actors(Collection):
    ENTITY_CLASS = Actor


class Objects(Collection):
    pass


class Directions(Collection):
    STORAGE_CLASS = FileStorage
    ENTITY_CLASS = Direction

    def fuzzy_get(self, name):
        name = name.lower()
        for direction in self.query():
            if direction.id.startswith(name):
                return direction


class CoreModule(Module):
    DESCRIPTION = "The basics of the game, primarily data models"

    def __init__(self, game):
        super(CoreModule, self).__init__(game)
        self.game.register_injector(Rooms)
        self.game.register_injector(Actors)
        self.game.register_injector(Objects)
        self.game.register_injector(Characters)
        self.game.register_injector(Directions)
        self.game.register_injector(Subroutines)
        self.game.register_injector(Behaviors)
        self.game.register_injector(Genders)
        self.game.register_injector(Classes)
        self.game.register_injector(Races)
        self.game.register_injector(Areas)

        for dir_name in settings.DIRECTIONS:
            self.game.register_command(dir_name, direction_command)

        for channel_name in settings.CHANNELS:
            self.game.register_command(channel_name, channel_command)

        self.game.register_command("look", look_command)
        self.game.register_command("who", who_command)
        self.game.register_command("title", title_command)
        self.game.register_command("score", score_command)
        self.game.register_command("delete", delete_command)
        self.game.register_command("say", say_command)
        self.game.register_command("quit", quit_command)
        self.game.register_command("fail", fail_command)
        self.game.register_command("dig", dig_command)
        self.game.register_command("link", link_command)
        self.game.register_command("unlink", unlink_command)
        self.game.register_command("areas", areas_command)
        self.game.register_command("goto", goto_command)

        directions, characters = \
            self.game.get_injectors("Directions", "Characters")

        directions.data = settings.DIRECTIONS

        for actor in characters.query():
            actor.online = False
            actor.connection_id = None
            characters.save(actor)
