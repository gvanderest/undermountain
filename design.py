from utils.ansi import colorize, decolorize
import logging
import gevent
from gevent import monkey
import settings
import socket as raw_socket
import random
import json
import os
import glob

monkey.patch_all()

logger = logging.getLogger()
FORMAT = "%(asctime)-15s [%(levelname)s] " + \
    "%(filename)s.%(funcName)s:%(lineno)s %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)


class InvalidInjector(Exception):
    pass


class Unblockable(Exception):
    pass


class FuzzyResolver(object):
    def __init__(self, mapping=None):
        self.commands = {}
        if not mapping:
            mapping = {}

        for key, entry in mapping.items():
            self.add(key, entry)

    def _query_partial_names(self, name):
        """Generate the names that make up the parts of the name."""
        name = name.lower()
        partial = ""
        for char in name:
            partial += char
            yield partial

    def add(self, name, entry):
        """Add something to the Resolver by name to match entries."""
        for partial in self._query_partial_names(name):

            if partial not in self.commands:
                self.commands[partial] = []

            self.commands[partial].append((name, entry))

    # def remove(self, name, entry):
    #     """Remove something from the Resolved by name."""
    #     for partial in self._query_partial_names(name):
    #         commands = self.commands[partial]

    #         commands.remove(entry)

    #         if not commands[partial]:
    #             del commands[partial]

    def query(self, name):
        """Return the list of entries matching a name."""
        name = name.lower()
        for entry in self.commands.get(name, []):
            yield entry

    def get(self, name):
        """Return the first match for a name."""
        name = name.lower()
        for entry in self.query(name):
            return entry


class Game(object):
    def __init__(self):
        self.data = {}
        self.injectors = {}
        self.modules = []
        self.managers = []
        self.connections = {}

    def register_module(self, module):
        instance = module(self)
        self.modules.append(instance)

    def register_manager(self, manager):
        instance = manager(self)
        self.managers.append(instance)
        logging.info("Registered manager {}".format(
            instance.__class__.__name__))

    def register_injector(self, injector):
        instance = injector(self)
        self.injectors[injector.__name__] = instance
        logging.info("Registered injector {}".format(
            instance.__class__.__name__))

    def get_injector(self, name):
        if name not in self.injectors:
            raise InvalidInjector(
                "{} is not a valid injector name".format(name))
        return self.injectors[name]

    def get_injectors(self, *names):
        return map(self.get_injector, names)

    def start(self):
        self.running = True

        for manager in self.managers:
            manager.start()

        while self.running:
            gevent.sleep(1.0)
            logging.debug("Tick.")

    def stop(self):
        self.running = False


class GameComponent(object):
    def __init__(self, game):
        """Attach the Game to this Component."""
        self.game = game


class Event(object):
    def __init__(self, source, type_name, data=None, unblockable=False):
        if data is None:
            data = {}

        self.source = source
        self.type = type_name
        self.data = data
        self.unblockable = unblockable
        self.blocked = False

    def block(self):
        if self.unblockable:
            raise Unblockable("Event of type '{}' is unblockable.".format(
                self.type))
        self.blocked = True
        return self


class Module(GameComponent):
    DESCRIPTION = ""
    VERSION = "0.0.0"


class Manager(GameComponent):
    DESCRIPTION = ""

    def start(self):
        """"Execute commands when Game starts."""
        pass

    def stop(self):
        """"Execute commands when Game stops."""
        pass


class TimerManager(Manager):
    TIMER_DELAY = 1.0  # Seconds between ticks.

    def start(self):
        """Instantiate the timer loop."""
        gevent.spawn(self.start_timer_loop)

    def start_timer_loop(self):
        """Start a timer."""
        self.running = True
        while self.running:
            gevent.sleep(self.TIMER_DELAY)
            logging.debug("Ticking {}".format(self.__class__.__name__))
            self.tick()

    def tick(self):
        """Commands to run on the looped timer."""
        pass


class Command(GameComponent):
    DESCRIPTION = ""

    def execute(self, entity, args=None):
        pass


def inject(*injector_names):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for name in injector_names:
                kwargs[name] = self.game.get_injector(name)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class CombatManager(TimerManager):
    TIMER_DELAY = 1.0

    @inject("Battles")
    def tick(self, Battles):
        logging.debug("Battles!! {}".format(Battles.query()))


class Injector(GameComponent):
    DESCRIPTION = ""
    pass


class CombatModule(Module):
    DESCRIPTION = "Add the ability to support round-based combat"

    def __init__(self, game):
        super(CombatModule, self).__init__(game)
        self.game.register_manager(CombatManager)
        self.game.register_injector(Battles)


class Connection(object):
    NEWLINE = "\r\n"
    CURRENT_ID = 0

    @classmethod
    def get_next_id(cls):
        cls.CURRENT_ID += 1
        return cls.CURRENT_ID

    def __init__(self, server):
        """Initialize Connection to Game and store its socket."""
        self.server = server
        self.id = Connection.get_next_id()
        self.actor_id = None

    @property
    def game(self):
        return self.server.game

    def start(self):
        """Execute commands for starting of Connection."""
        self.client.start()

    def close(self):
        """Execute commands to close the Connection."""
        pass

    def write(self, message=""):
        """Execute commands to send data over the socket."""
        pass

    def writeln(self, message=""):
        """Send data over the socket, with newline."""
        self.writeln(message + self.NEWLINE)

    def flush(self):
        """TODO: Confirm we need to handle this at all or if server will."""
        pass


class Server(GameComponent):
    def __init__(self, game):
        super(Server, self).__init__(game)
        self.connections = {}

    def start(self):
        """Execute commands when Server starts."""
        pass

    def stop(self):
        """Execute commands when Server stops."""
        pass

    def add_connection(self, connection):
        self.connections[connection.id] = connection
        self.game.connections[connection.id] = connection

    def remove_connection(self, connection):
        del self.game.connections[connection.id]
        del self.connections[connection.id]


class Client(object):
    INITIAL_STATE = "null"

    def __init__(self, connection):
        self.connection = connection
        self.inputs = []
        self.parse_thread = None
        self.state = self.INITIAL_STATE
        self.last_input = ""
        self.spam_count = 0

    @property
    def game(self):
        return self.connection.game

    def handle_inputs(self, inputs):
        if "clear" in inputs:
            self.inputs = []
            return

        self.inputs += inputs

        if not self.parse_thread:
            self.parse_thread = gevent.spawn(self.start_parse_thread)
        for input in inputs:
            logging.info("INPUT {}".format(input))

    def start_parse_thread(self):
        while self.inputs:
            message = self.inputs.pop(0)

            if message == "!":
                message = self.last_input
            else:
                self.last_input = message

            delay = self.handle_input(message)
            gevent.sleep(delay if delay else 0.3)
        self.parse_thread = None

    def handle_input(self, message):
        func_name = "handle_{}_input".format(self.state)
        func = getattr(self, func_name)
        return func(message)

    def write(self, message=""):
        self.connection.write(message)

    def writeln(self, message=""):
        self.write(message + "\n")


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
    say = self.emit("before:say", say_data)
    if say.blocked:
        return

    self.echo("{{MYou say {{x'{{m{}{{x'".format(message))
    self.act("{M{self.name} says {x'{m{message}{M{x'", {
        "message": message,
    })

    self.emit("after:say", say_data)


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
    walk = self.emit("before:walk", walk_data)

    if walk.blocked:
        return

    new_room = Rooms.get({"vnum": exit["room_vnum"]})

    if not new_room:
        self.echo("The place you're walking to doesn't appear to exist.")
        return

    enter_data = {"direction": direction.opposite}
    enter = self.emit("before:enter", enter_data)

    if enter.blocked:
        return

    self.act("{self.name} leaves " + direction.colored_name)
    self.room_id = new_room.id
    self.save()
    self.act("{self.name} has arrived.")

    self.emit("after:enter", enter_data, unblockable=True)
    self.emit("after:walk", walk_data, unblockable=True)

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
            "1".rjust(3),
            "{BM",
            "{CH{cuman",
            "{MA{mdv",
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


def title_command(self, message, **kwargs):
    self.title = message
    if message:
        self.echo("Title set to: {}".format(self.title))
    else:
        self.echo("Title cleared.")


def save_command(self, **kwargs):
    self.echo("Your character has been saved.")


@inject("Characters")
def delete_command(self, Characters, **kwargs):
    self.echo("Removing your character from the game.")
    Characters.delete(self)
    self.quit(skip_save=True)


COMMANDS_MAP = {
    "north": {"handler": direction_command},
    "east": {"handler": direction_command},
    "south": {"handler": direction_command},
    "west": {"handler": direction_command},
    "up": {"handler": direction_command},
    "down": {"handler": direction_command},

    "say": {"handler": say_command},
    "who": {"handler": who_command},
    "delete": {"handler": delete_command},
    "look": {"handler": look_command},
    "save": {"handler": save_command},
    "title": {"handler": title_command},
    "score": {"handler": score_command},
    "quit": {"handler": quit_command},
}


class TelnetClient(Client):
    INITIAL_STATE = "login_username"

    def __init__(self, *args, **kwargs):
        super(TelnetClient, self).__init__(*args, **kwargs)
        self.write_ended_with_newline = False
        self.prompt_thread = False
        self.resolver = FuzzyResolver(COMMANDS_MAP)
        self.color = True
        self.writeln("Connected to {rU{8nd{wer{Wmou{wnt{8ai{rn{x.")
        self.writeln()
        self.write("What is your name, adventurer? ")

    @inject("Characters")
    @property
    def actor(self, Characters):
        return Characters.get(self.connection.actor_id)

    def stop(self):
        self.writeln("Disconnecting..")

    def handle_login_username_input(self, message):
        Characters = self.game.get_injector("Characters")
        name = message.strip().lower().title()

        found = Characters.get({"name": name})
        if not found:
            found = Characters.save(Character({
                "room_id": "abc123",
                "name": name,
            }))
        elif found.connection:
            found.echo("You have been kicked off due to another logging in.")
            found.connection.close()

        found.online = True
        found.connection_id = self.connection.id
        found.save()

        self.connection.actor_id = found.id

        self.state = "playing"
        self.handle_playing_input("look")

    def quit(self):
        self.connection.close()
        self.connection.server.remove_connection(self.connection)

    def write(self, message=""):
        if self.state == "playing" and not self.write_ended_with_newline:
            message = "\n" + message

        if self.color:
            message = colorize(message)
        else:
            message = decolorize(message)

        self.write_ended_with_newline = message[-1] == "\n"

        super(TelnetClient, self).write(message)
        if not self.prompt_thread:
            self.prompt_thread = gevent.spawn(self.write_prompt)

    def write_prompt(self):
        if self.state != "playing":
            return
        self.writeln()
        self.write("{x> ")

    @inject("Characters")
    def handle_playing_input(self, message, Characters):
        actor = Characters.get(self.connection.actor_id)
        delay = None

        while self.inputs and not self.inputs[0]:
            self.inputs.pop(0)

        parts = message.split(" ")
        name = parts[0].lower()
        args = parts[1:]

        kwargs = {"args": args, "name": name, "message": " ".join(args)}

        command = None
        for real_name, entry in self.resolver.query(name):
            min_level = entry.get("min_level", 0)
            max_level = entry.get("max_level", 9999)
            fake_level = 1
            if fake_level < min_level or fake_level > max_level:
                continue
            kwargs["name"] = real_name
            command = entry["handler"]
            break

        if command:
            # TODO Handle command exceptions.
            # try:
            delay = command(actor, **kwargs)
            # except Exception as e:
            #     self.writeln(repr(e))
            #     self.writeln("Huh?!")
        else:
            self.writeln("Huh?")

        return delay


class TelnetConnection(Connection):
    def __init__(self, server, socket, address):
        super(TelnetConnection, self).__init__(server)
        self.socket = socket
        self.client = TelnetClient(self)
        self.address = address
        self.buffer = ""

    def start(self):
        gevent.spawn(self.read)

    def close(self):
        try:
            self.socket.flush()
        except Exception:
            pass

        try:
            self.socket.shutdown(raw_socket.SHUT_WR)
        except Exception:
            pass

        try:
            self.socket.close()
        except Exception:
            pass

        self.socket = None

    def read(self):
        """Listen for commands/etc."""
        while self.socket:
            try:
                raw = self.socket.recv(4096)
            except Exception:
                raw = None
            if not raw:
                self.close()
                break

            try:
                self.buffer += raw.decode("utf-8").replace("\r\n", "\n")
            except Exception:
                pass

            if "\n" in self.buffer:
                split = self.buffer.split("\n")
                inputs = split[:-1]
                self.buffer = split[-1]

                self.client.handle_inputs(inputs)

    def write(self, message=""):
        if not self.socket:
            return
        message = message.replace("\n", "\r\n")
        self.socket.send(message.encode())


class TelnetServer(Server):
    def __init__(self, game):
        super(TelnetServer, self).__init__(game)
        self.ports = []

    def start(self):
        """Instantiate the ports to listen on."""
        for host, port in settings.TELNET_PORTS:
            socket = raw_socket.socket(
                raw_socket.AF_INET,
                raw_socket.SOCK_STREAM,
            )
            socket.setsockopt(
                raw_socket.SOL_SOCKET,
                raw_socket.SO_REUSEADDR,
                1,
            )
            socket.bind((host, port))
            self.ports.append(socket)
            gevent.spawn(self.accept, socket)

    def accept(self, port):
        """Listen and handle Connections on port."""
        port.listen()
        while True:
            socket, address = port.accept()
            conn = TelnetConnection(self, socket, address)
            self.add_connection(conn)
            gevent.spawn(conn.start)


class TelnetModule(Module):
    DESCRIPTION = "Support the Telnet protocol for connections"

    def __init__(self, game):
        super(TelnetModule, self).__init__(game)
        self.game.register_manager(TelnetServer)


class Entity(object):
    DEFAULT_DATA = {}

    @inject("Subroutines", "Behaviors")
    def handle_event(self, event, Subroutines, Behaviors):
        if self == event.source:
            return event

        # TODO HAVE COLLECTION CREATE DEEPCOPIES OF EVERYTHING
        handlers = list(self.event_handlers or [])

        for behavior_id in (self.behaviors or []):
            behavior = Behaviors.get(behavior_id)
            handlers.append({
                "type": behavior.type,
                "subroutine_id": behavior.subroutine_id,
            })

        if handlers:
            for entry in handlers:
                if entry["type"] != event.type:
                    continue

                subroutine = Subroutines.get(entry["subroutine_id"])
                subroutine.execute(self, event)

        return event

    def generate_event(self, type, data=None, unblockable=False):
        return Event(self, type, data, unblockable=unblockable)

    def __eq__(self, other):
        return other.id == self.id

    def __neq__(self, other):
        return not self.__eq__(other)

    def __init__(self, data=None, collection=None):
        merged_data = dict(self.DEFAULT_DATA)
        if data:
            merged_data.update(data)
        data = merged_data

        super(Entity, self).__setattr__("_data", data)
        super(Entity, self).__setattr__("_collection", collection)

    @property
    def game(self):
        return self._collection.game

    @property
    def collection(self):
        return self._collection

    def __setattr__(self, name, value):
        return self.set(name, value)

    def __getattr__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, default=None):
        return self._data.get(name, None)

    def set(self, name, value):
        self._data[name] = value

    def set_data(self, data):
        super(Entity, self).__setattr__("_data", data)

    def get_data(self):
        return self._data


class CollectionStorage(object):
    def __init__(self, collection):
        self.collection = collection

    def post_save(self, record):
        pass

    def post_delete(self, record):
        pass


class MemoryStorage(CollectionStorage):
    pass


class FileStorage(CollectionStorage):
    def __init__(self, *args, **kwargs):
        super(FileStorage, self).__init__(*args, **kwargs)
        name = self.collection.__class__.__name__.lower()
        self.folder = "{}/{}".format(settings.DATA_FOLDER, name)

        self.load_initial_data()

    def load_initial_data(self):
        pattern = "{}/*".format(self.folder)
        for path in glob.glob(pattern):
            with open(path, "r") as fh:
                data = json.loads(fh.read())
                self.collection.save(data, skip_storage=True)

    def get_record_filename(self, record):
        filename = record[self.collection.STORAGE_FILENAME_FIELD]
        format_name = self.collection.STORAGE_FORMAT

        suffix = self.collection.STORAGE_FILENAME_SUFFIX
        if suffix != "":
            if suffix is None:
                suffix = format_name
            suffix = "." + suffix

        return "{}/{}{}".format(
            self.folder,
            filename,
            suffix)

    def post_save(self, record):
        path = self.get_record_filename(record)
        with open(path, "w") as fh:
            fh.write(json.dumps(record))

    def post_delete(self, record):
        path = self.get_record_filename(record)
        os.remove(path)


class Collection(Injector):
    PERSISTENT = False
    ENTITY_CLASS = Entity
    STORAGE_CLASS = MemoryStorage
    STORAGE_FORMAT = "json"
    STORAGE_FILENAME_FIELD = "name"
    STORAGE_FILENAME_SUFFIX = ""
    DATA_NAME = None

    def __init__(self, game):
        super(Collection, self).__init__(game)
        name = self.DATA_NAME or self.__class__.__name__
        self.game.data[name] = {}
        self.storage = self.STORAGE_CLASS(self)

    @property
    def data(self):
        name = self.DATA_NAME or self.__class__.__name__
        return self.game.data[name]

    @data.setter
    def data(self, data):
        name = self.DATA_NAME or self.__class__.__name__
        self.game.data[name] = data

    def query(self, spec=None):
        def _filter_function(record):
            if spec is None:
                return True
            else:
                for key in spec:
                    if key not in record or spec[key] != record[key]:
                        return False
                return True

        filtered = filter(_filter_function, self.data.values())
        for record in filtered:
            yield self.wrap_record(record)

    def get(self, spec):
        if isinstance(spec, str):
            record = self.data.get(spec, None)
            if not record:
                return None
            return self.wrap_record(record)
        else:
            for record in self.query(spec):
                return record

    def save(self, record, skip_storage=False):
        record = self.unwrap_record(record)

        if "id" not in record:
            record["id"] = str(random.randint(100000000000, 999999999999))
        self.data[record["id"]] = record

        if not skip_storage:
            self.storage.post_save(record)

        return self.get(record["id"])

    def unwrap_record(self, record):
        if isinstance(record, Entity):
            return record.get_data()
        return record

    def wrap_record(self, record):
        if isinstance(record, dict):
            return self.ENTITY_CLASS(data=record, collection=self)
        return record

    def delete(self, record):
        record = self.unwrap_record(record)
        del self.data[record["id"]]
        self.storage.post_delete(record)


class Battles(Collection):
    pass


class Actor(Entity):
    DEFAULT_DATA = {
        "name": "",
        "title": "",
        "experience": 0,
        "room_id": "",
        "room_vnum": settings.INITIAL_ROOM_VNUM,
    }

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

    def emit(self, type, data=None, unblockable=False):
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


class Object(Entity):
    pass


class Character(Actor):
    pass


class Area(Entity):
    pass


class Areas(Collection):
    ENTITY_CLASS = Area


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


class Subroutine(Entity):
    def execute(self, entity, event):
        compiled = compile(self.code, "subroutine:{}".format(self.id), "exec")

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


class Subroutines(Collection):
    ENTITY_CLASS = Subroutine


class Behavior(Entity):
    @property
    @inject("Subroutines")
    def subroutine(self):
        return Subroutines.get(self.subroutine_id)


class Behaviors(Collection):
    ENTITY_CLASS = Behavior


class Characters(Collection):
    STORAGE_CLASS = FileStorage
    ENTITY_CLASS = Character


class Actors(Collection):
    ENTITY_CLASS = Actor


class Objects(Collection):
    ENTITY_CLASS = Object


class Directions(Collection):
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

        directions, characters = \
            self.game.get_injectors("Directions", "Characters")

        directions.data = settings.DIRECTIONS

        for actor in characters.query():
            actor.online = False
            actor.connection_id = None
            characters.save(actor)


GAME = Game()
GAME.register_module(CoreModule)
GAME.register_module(TelnetModule)
GAME.register_module(CombatModule)

rooms, actors, objects, characters, subroutines, behaviors = \
    GAME.get_injectors(
        "Rooms", "Actors", "Objects", "Characters", "Subroutines", "Behaviors")

ms = rooms.save({
    "vnum": "market_square",
    "name": "Market Square",
    "description": [
        "Beneath you, a rough mosaic of paving stones marks the center of the",
        "market of Westbridge.  Nearby, bakers and butchers can be seen, ",
        "hawking their wares to the passers by.",
    ],
    "exits": {
        "north": {"room_vnum": "north_ms"},
        "east": {"room_vnum": "east_ms"},
        "south": {"room_vnum": "south_ms"},
        "west": {"room_vnum": "west_ms"},
    },
})

rooms.save({
    "vnum": "east_ms",
    "name": "East of Market Square",
    "description": [],
    "exits": {
        "west": {"room_vnum": "market_square"},
        "east": {"room_vnum": "east_path"},
    },
})

rooms.save({
    "vnum": "north_ms",
    "name": "North of Market Square",
    "description": [],
    "exits": {
        "south": {"room_vnum": "market_square"},
    },
})

rooms.save({
    "vnum": "south_ms",
    "name": "South of Market Square",
    "description": [],
    "exits": {
        "north": {"room_vnum": "market_square"},
    },
})

rooms.save({
    "vnum": "west_ms",
    "name": "West of Market Square",
    "description": [],
    "exits": {
        "east": {"room_vnum": "market_square"},
    },
})

east_path = rooms.save({
    "vnum": "east_path",
    "name": "The Forest Path",
    "description": [
        "To the west, you can see the makeshift wooden walls surrounding the",
        "small village of Westbridge.  To the east, the forest looms "
            "menacingly,",
        "its thick canopy enveloping the ground in near darkness.",
    ],
    "exits": {
        "east": {"room_vnum": "east_path"},
        "west": {"room_vnum": "east_ms"},
    },
})

actors.save({
    "name": "Bill, the guard",
    "room_vnum": east_path.vnum,
    "room_id": east_path.id,
    "event_handlers": [
        {"type": "before:walk", "subroutine_id": "bill_stops_you"},
    ]
})

actors.save({
    "name": "the town crier",
    "room_vnum": ms.vnum,
    "room_id": ms.id,
    "behaviors": ["happy"],
    "event_handlers": [
        {"type": "after:enter", "subroutine_id": "greetings"},
    ],
})


behaviors.save({
    "id": "happy",
    "type": "after:enter",
    "subroutine_id": "happy",
})

objects.save({
    "name": "a piece of bread",
    "room_vnum": ms.vnum,
    "room_id": ms.id,
})

subroutines.save({
    "id": "happy",
    "code": """
wait(1)
self.say("Boy golly, am I a happy fella!")
    """
})

subroutines.save({
    "id": "greetings",
    "code": """
wait(0.2)
self.say("Hello {}!".format(target.name))
    """
})

subroutines.save({
    "id": "bill_stops_you",
    "code": """
if direction == "east":
    event.block()
    self.say("There's no way I'm letting you go into the forest.")
    self.say("It's too dangerous.. plus, the mayor would kill me.")
    """
})

tasks = [
    gevent.spawn(GAME.start)
]

try:
    gevent.joinall(tasks)
except KeyboardInterrupt:
    logging.info("Process killed by CTRL+C")
