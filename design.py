import logging
import gevent
from gevent import monkey
import settings
import socket as raw_socket
import random

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


class Game(object):
    def __init__(self):
        self.data = {}
        self.injectors = {}
        self.modules = []
        self.managers = []
        self.connections = []

    def register_module(self, module):
        instance = module(self)
        self.modules.append(instance)

    def register_manager(self, manager):
        logging.info("Registering manager {}".format(manager.NAME))
        instance = manager(self)
        self.managers.append(instance)

    def register_injector(self, name, injector):
        instance = injector(self)
        self.injectors[name] = instance

    def get_injector(self, name):
        if name not in self.injectors:
            raise InvalidInjector(
                "{} is not a valid injector name".format(name))
        return self.injectors[name]

    def get_injectors(self, *names):
        return map(self.get_injector, names)

    def set_data(self, key, value):
        self.data[key] = value

    def get_data(self, key):
        return self.data[key]

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


class Event(GameComponent):
    def __init__(self, game, type_name, data=None, blockable=True):
        super(Event, self).__init__(game)

        if data is None:
            data = {}
        self.type = type_name
        self.data = data
        self.blockable = blockable
        self.blocked = False

    def block(self):
        if not self.blockable:
            raise Unblockable("Event of type '{}' is unblockable.".format(
                self.type))
        self.blocked = True


class Module(GameComponent):
    NAME = None
    DESCRIPTION = ""
    VERSION = "0.0.0"


class Manager(GameComponent):
    NAME = None
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
            logging.debug("Ticking {}".format(self.NAME))
            self.tick()

    def tick(self):
        """Commands to run on the looped timer."""
        pass


class Command(GameComponent):
    NAME = ""
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


class Actor(GameComponent):
    pass


class CombatManager(TimerManager):
    NAME = "CombatManager"
    TIMER_DELAY = 1.0

    @inject("Battles")
    def tick(self, Battles):
        logging.debug("Battles!! {}".format(Battles.query()))


class Injector(GameComponent):
    NAME = None
    DESCRIPTION = ""
    pass


class Collection(Injector):
    NAME = None

    def __init__(self, game):
        super(Collection, self).__init__(game)
        name = self.NAME or self.__class__.__name__
        self.game.set_data(name, {})
        self.types = {}

    @property
    def data(self):
        name = self.NAME or self.__class__.__name__
        return self.game.data[name]

    def query(self, spec=None):
        return self.data.values()

    def get(self, id):
        return self.data[id]

    def add(self, record):
        if "id" not in record:
            record["id"] = str(random.randint(100000000000, 999999999999))
        self.data[record["id"]] = record

    def remove(self, record):
        del self.data[record["id"]]


class Battles(Collection):
    pass


class CombatModule(Module):
    NAME = "RoundBasedCombat"
    DESCRIPTION = "Add the ability to support round-based combat"

    def __init__(self, game):
        super(CombatModule, self).__init__(game)
        self.game.register_manager(CombatManager)
        self.game.register_injector("Battles", Battles)


class Connection(object):
    NEWLINE = "\r\n"

    def __init__(self, server):
        """Initialize Connection to Game and store its socket."""
        self.server = server
        self.actor = None

    @property
    def game(self):
        return self.server.game

    def set_actor(self, actor):
        """Assign the Actor to this Connection."""
        self.actor = actor

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
        self.connections = []

    def start(self):
        """Execute commands when Server starts."""
        pass

    def stop(self):
        """Execute commands when Server stops."""
        pass

    def add_connection(self, connection):
        self.connections.append(connection)
        self.game.connections.append(connection)

    def remove_connection(self, connection):
        self.game.connections.remove(connection)
        self.connections.remove(connection)


class Client(object):
    INITIAL_STATE = "null"

    def __init__(self, connection):
        self.connection = connection
        self.inputs = []
        self.parse_thread = None
        self.state = self.INITIAL_STATE

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
            delay = self.handle_input(message)
            gevent.sleep(delay if delay else 0.2)
        self.parse_thread = None

    def handle_input(self, message):
        func_name = "handle_{}_input".format(self.state)
        func = getattr(self, func_name)
        func(message)

    def write(self, message=""):
        self.connection.write(message)

    def writeln(self, message=""):
        self.write(message + "\n")


@inject("Rooms", "Actors", "Objects")
def look_command(self, args, Rooms, Actors, Objects, **kwargs):
    room = list(Rooms.query())[0]
    self.writeln("{} [LAW] [SAFE]".format(room["name"]))
    for index, line in enumerate(room["description"]):
        if index == 0:
            self.write("  ")
        self.writeln(line)

    spec = {"room_id": room["id"]}
    for actor in Actors.query(spec):
        self.writeln("{} is standing here.".format(actor["name"]))

    for obj in Objects.query(spec):
        self.writeln("{} is on the ground here.".format(actor["name"]))


def quit_command(self, **kwargs):
    self.writeln("You're logging out...")
    self.quit()


def who_command(self, **kwargs):
    self.writeln("The Visible Mortals and Immortals of Waterdeep")
    self.writeln("-" * 79)
    for conn in self.game.connections:
        self.writeln("  1 M Human War         [.N......] {}".format("Name"))
    self.writeln()
    self.writeln("Players found: X   Total online: X   Most on today: X")


class TelnetClient(Client):
    INITIAL_STATE = "login_username"

    def start(self):
        self.writeln("Connected.")

    def stop(self):
        self.writeln("Disconnecting..")

    def handle_login_username_input(self, message):
        self.writeln("RECEIVED {}".format(message))
        self.state = "playing"
        self.handle_playing_input("look")

    def quit(self):
        self.connection.close()
        self.connection.server.remove_connection(self.connection)

    def handle_playing_input(self, message):
        while self.inputs and not self.inputs[0]:
            self.inputs.pop(0)

        self.writeln("You typed '{}'".format(message))
        self.writeln("")

        parts = message.split(" ")
        name = parts[0]
        args = parts[1:]

        kwargs = {"args": args, "name": name}

        if message == "who":
            who_command(self, **kwargs)
        elif message == "look":
            look_command(self, **kwargs)
        elif message == "quit":
            quit_command(self, **kwargs)
        else:
            for conn in self.game.connections:
                if conn is self.connection:
                    continue
                client = conn.client
                client.writeln("Someone typed: {}".format(message))

        self.writeln("")
        self.write("PROMPT> ")


class TelnetConnection(Connection):
    NAME = "TelnetConnection"

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
            self.buffer += raw.decode("utf-8").replace("\r\n", "\n")
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
    NAME = "TelnetServer"

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
    NAME = "Telnet"
    DESCRIPTION = "Support the Telnet protocol for connections"

    def __init__(self, game):
        super(TelnetModule, self).__init__(game)
        self.game.register_manager(TelnetServer)


class Rooms(Collection):
    pass


class Actors(Collection):
    pass


class Objects(Collection):
    pass


class CoreModule(Module):
    NAME = "Core"
    DESCRIPTION = "The basics of the game, primarily data models"

    def __init__(self, game):
        super(CoreModule, self).__init__(game)
        self.game.register_injector("Rooms", Rooms)
        self.game.register_injector("Actors", Actors)
        self.game.register_injector("Objects", Objects)


GAME = Game()
GAME.register_module(CoreModule)
GAME.register_module(TelnetModule)
# GAME.register_module(CombatModule)

rooms, actors, objects = GAME.get_injectors("Rooms", "Actors", "Objects")
rooms.add({
    "vnum": "market_square",
    "name": "Market Square",
    "description": [
        "Beneath you, a rough mosaic of paving stones marks the center of the",
        "market of Westbridge.  Nearby, bakers and butchers can be seen, ",
        "hawking their wares to the passers by.",
    ],
    "exits": {
        "north": {"room_vnum": "market_square"},
        "east": {"room_vnum": "market_square"},
        "south": {"room_vnum": "market_square"},
        "west": {"room_vnum": "market_square"},
    },
})

tasks = [
    gevent.spawn(GAME.start)
]

try:
    gevent.joinall(tasks)
except KeyboardInterrupt:
    print("KILLED")
