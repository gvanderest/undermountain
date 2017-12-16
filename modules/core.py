from mud.module import Module
from mud.collection import Collection, Entity, FileStorage
from mud.inject import inject

import gevent
import settings


def fail_command(self, **kwargs):
    """Force an Exception to occur."""
    raise Exception("Testing exceptions.")


@inject("Actors", "Objects", "Directions")
def look_command(self, args, Actors, Objects, Directions, **kwargs):
    room = self.room

    self.echo("{{B{} {{x[{{WLAW{{x] {{R[{{WSAFE{{R]{{x".format(room["name"]))
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


class Direction(Entity):
    pass


class Rooms(Collection):
    ENTITY_CLASS = Room
    STORAGE_CLASS = FileStorage


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
    STORAGE_CLASS = FileStorage


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
    STORAGE_CLASS = FileStorage


class Objects(Collection):
    STORAGE_CLASS = FileStorage
    ENTITY_CLASS = Object


class Directions(Collection):
    STORAGE_CLASS = FileStorage
    ENTITY_CLASS = Direction


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

        for dir_name in settings.DIRECTIONS:
            self.game.register_command(dir_name, direction_command)

        self.game.register_command("look", look_command)
        self.game.register_command("who", who_command)
        self.game.register_command("score", score_command)
        self.game.register_command("delete", delete_command)
        self.game.register_command("say", say_command)
        self.game.register_command("quit", quit_command)
        self.game.register_command("fail", fail_command)

        directions, characters = \
            self.game.get_injectors("Directions", "Characters")

        directions.data = settings.DIRECTIONS

        for actor in characters.query():
            actor.online = False
            actor.connection_id = None
            characters.save(actor)
