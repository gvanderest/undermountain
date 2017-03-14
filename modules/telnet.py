"""
TELNET MODULE
"""
import logging
import gevent
import socket
import gevent.monkey
from mud.client import Client
from mud.connection import Connection
from mud.module import Module
from mud.server import Server
from utils.ansi import Ansi

gevent.monkey.patch_socket()


class TelnetClient(Client):
    """Wrapper for how our Game works."""
    def init(self):
        self.last_command = None
        self.actor_id = None
        self.name = None

    def hide_next_input(self):
        self.write("<TODO HIDE> ")

    def start(self):
        self.write_login_banner()
        self.write_login_username_prompt()

    def write_login_banner(self):
        self.writeln("""\


            ;::::;
           ;::::; :;
         ;:::::'   :;
        ;:::::;     ;.
       ,:::::'       ;           OOO\\
       ::::::;       ;          OOOOO\\
       ;:::::;       ;         OOOOOOOO
      ,;::::::;     ;'         / OOOOOOO
    ;:::::::::`. ,,,;.        /  / DOOOOO
  .';:::::::::::::::::;,     /  /    DOOOO
 ,::::::;::::::;;;;::::;,   /  /       DOOO
;`::::::`'::::::;;;::::: ,#/  /        DOOO
:`:::::::`;::::::;;::: ;::#  /          DOOO
::`:::::::`;:::::::: ;::::# /            DOO
`:`:::::::`;:::::: ;::::::#/             DOO
 :::`:::::::`;; ;:::::::::##              OO
 ::::`:::::::`;::::::::;:::#              OO
 `:::::`::::::::::::;'`:;::#              O
  `:::::`::::::::;' /  / `:#
   ::::::`:::::;'  /  /   `#
           ##    ##  ####  ###### ######  ####  ######  ###### ###### #####
           ##    ## ##  ##   ##   ##     ##  ##  ##  ## ##     ##     ##  ##
           ## ## ## ######   ##   ####   ##  ##  ##  ## ####   ####   #####
           ## ## ## ##  ##   ##   ##     #####   ##  ## ##     ##     ##
            ##  ##  ##  ##   ##   ###### ##  ## ######  ###### ###### ##
                          C I T Y  O F  S P L E N D O R S
                                   [ Est 1997 ]
""")

    def write_login_username_prompt(self):
        self.write("What is your name, adventurer? ")

    def get_character(self, name):
        game = self.get_game()
        Characters = game.get_injector("Characters")
        return Characters.find({"name": name})

    def create_character(self, data):
        game = self.get_game()
        Characters = game.get_injector("Characters")
        return Characters.save(data)

    def get_cleaned_name(self, name):
        return name.strip().lower().title()

    def is_valid_username(self, username):
        from settings import BANNED_NAMES
        username = username.lower()

        if username in BANNED_NAMES:
            return False

        if len(username) < 3:
            return False

        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyz":
                return False

        return True

    def handle_login_username(self, message):
        """Handle logging in username prompt."""
        username = self.get_cleaned_name(message)

        if not self.is_valid_username(username):
            self.writeln("The name you provided is not valid.")
            self.writeln("* Must be at least 3 characters in length")
            self.writeln("* Must only contain letters")
            self.writeln("* Must not be a reserved or banned name")
            self.writeln()
            self.write_login_username_prompt()
            return

        self.name = username

        if not message:
            self.writeln("Please pick a name, even if it's short.")
            self.write_login_username_prompt()
            return

        actor = self.get_character(self.name)

        # That Actor is already in the Game, reconnect?
        if actor:
            if actor.online:
                self.write_login_reconnect_confirm_prompt()
                self.state = "login_reconnect_confirm"
                return

            actor.online = True
            actor.save()
        else:
            # Create the Character and bind to client
            # TODO Make this a constant for starting room?
            data = {
                "name": self.name,
                "room_id": "market_square",
                "online": True,
                "password": "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                "organizations": {
                    # "clan": "vector",
                },
            }
            actor = self.create_character(data)

        self.state = "playing"
        self.actor_id = actor.id
        actor.set_client(self)

        self.writeln("Thanks for providing your name, {}!".format(actor.name))
        self.writeln()
        self.write_motd_prompt()
        self.state = "motd"

    def write_motd_prompt(self):
        self.writeln("""\

                                                          __
                                                        //  \\\\
                                                       // /\\ \\\\
                                                       \\\\ \\/ //
                                                        \\\\__//
                                                        [|//|]
                                                        [|//|]
               Welcome to                               [|//|]
                                                        [|//|]
            W A T E R D E E P                           [|//|]
                                                        [|//|]
            City of Splendors                /)         [|//|]        (\\
                                            //\\_________[|//|]________/\\\\
                est. 1997                   ))__________||__||_________((
                                           <_/         [  \\/  ]        \\_>
                                                       ||    ||
                                                       ||    ||
                                                       ||    ||
 [x] Waterdeep is rated [R] for Mature Audiences Only. ||    ||
 [x] Please follow the rules of the game. [Help Rules] ||    ||
 [x] Check the News Board for game info.               ||    ||
                                                       ||    ||
 [x] Type HELP for our directory of help files.        ||    ||
 [x] Type HELP NEWBIE for basic directions and help.   ||    ||
                                                       ||    ||
                                                       ||    ||
                                                       ||    ||
         Waterdeep Entertainment                       ||    ||
            www.waterdeep.org                          ||    ||
                                                       ||    ||
                                                       ||    ||
                                                       ||    ||
                                                       \\\\    //
                                                        \\\\  //
                                                         \\\\//
                                                          \\/
[Hit Enter to Continue]


Welcome to Waterdeep 'City Of Splendors'!  Please obey the rules, (help rules).
""")

    def handle_motd(self, message):
        self.state = "playing"

        self.handle_input("look")
        self.handle_input("unread")
        self.handle_input("version")

        actor = self.get_actor()
        self.wiznet("connect", "%s has connected" % (actor.name))

    def wiznet(self, *args, **kwargs):
        game = self.get_game()
        return game.wiznet(*args, **kwargs)

    def write_login_reconnect_confirm_prompt(self):
        self.writeln("That character is already playing.")
        self.write("Would you like to reconnect? [Y/N] ")

    def handle_login_reconnect_confirm(self, message):
        cleaned = message.strip().lower()

        if not cleaned:
            self.write_login_reconnect_confirm_prompt()
            return

        if not cleaned.startswith("y"):
            self.write_login_username_prompt()
            self.state = "login_username"
            return

        game = self.get_game()
        actor = self.get_character(self.name)

        # Cycle through Connections and disconnect existing ones
        connection = None
        for connection in game.get_connections():
            client = connection.get_client()
            client_actor = client.get_actor()
            if not client_actor:
                continue

            if client_actor == actor:
                connection.destroy()

            # TODO Echo that a disconnect occurred (from host)
            # TODO Wiznet that a disconnect occurred (with host)

        # Bind the Actor to this Client
        self.set_actor(actor)
        actor.set_client(self)

        # TODO Echo that a reconnect occurred (from host)
        # TODO Wiznet that a reconnect occurred (with host)
        self.writeln("Reconnected..")
        self.state = "playing"
        self.handle_input("look")
        self.wiznet("connect", "%s has reconnected" % (actor.name))

    def write_login_password_prompt(self):
        self.write("Password: ")
        self.hide_next_input()

    def write_playing_prompt(self):
        conn = self.connection
        if conn.output_buffer and \
                conn.output_buffer[-2:] != (2 * self.NEWLINE):
            self.writeln()
        self.write("> ")

    def no_handler(self, arguments):
        self.writeln("Invalid command.")

    def get_connection(self):
        return self.connection

    def get_game(self):
        connection = self.get_connection()
        if not connection:
            return None
        return connection.get_game()

    def set_actor(self, actor):
        if actor:
            self.actor_id = actor.id
        else:
            self.actor_id = None

    def get_actor(self):
        Characters = self.get_injector("Characters")
        actor = Characters.get(self.actor_id)

        if not actor:
            return None

        actor.set_client(self)
        return actor

    def handle_playing(self, message):
        if message == "!":
            if self.last_command is None:
                self.writeln("Huh?")
                self.write_playing_prompt()
            else:
                self.handle_playing(self.last_command)
            return

        self.last_command = message
        actor = self.get_actor()
        game = self.get_game()
        game.inject(
            actor.handle_command,
            message=message,
            ignore_aliases=False
        )

        self.write_playing_prompt()

    def gecho(self, message, emote=False):
        this_conn = self.connection
        game = self.get_game()
        actor = self.get_actor()

        template = "{}<#{}>: {}"
        if emote:
            template = "{}<#{}> {}"

        output = template.format(
            actor.name,
            this_conn.id,
            message
        )

        connections = game.get_connections()

        for connection in connections:
            client = connection.client

            if client.state != "playing":
                continue

            connection.writeln(output)

    def disconnect(self):
        actor = self.get_actor()
        self.wiznet("connect", "%s has disconnected" % (actor.name))

    def reconnect(self):
        self.gecho("reconnected to the chat", emote=True)

    def get_injector(self, *args, **kwargs):
        """Return an Injector from the Game."""
        game = self.get_game()
        return game.get_injector(*args, **kwargs)

    def quit(self):
        # Remove the Actor from the Game
        actor = self.get_actor()
        actor.online = False
        actor.save()
        self.set_actor(None)

        self.connection.destroy(clean=True)

        self.wiznet("connect", "%s has quit" % (actor.name))


class TelnetConnection(Connection):
    TYPE = "Telnet"
    READ_SIZE = 1024

    def __init__(self, the_socket, addr, *args, **kwargs):
        super(TelnetConnection, self).__init__(*args, **kwargs)

        self.socket = the_socket  # Raw socket
        self.client = TelnetClient(self)
        self.color = True

        self.ip = socket.gethostbyname(addr[0])  # Connection IP
        self.hostname = addr[0]  # Connection hostname
        self.port = addr[1]  # Connection port

    def enable_color(self):
        self.color = True

    def disable_color(self):
        self.color = False

    def read(self):
        try:
            message = self.socket.recv(self.READ_SIZE)
        except OSError:
            message = None

        if message is None or not message:
            return None

        message = message \
            .decode("utf-8", errors="ignore") \
            .replace("\r\n", "\n")
        return message

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
        except OSError:
            pass

        self.socket.close()

    def flush(self, message):
        if self.color:
            message = Ansi.colorize(message)
        else:
            message = Ansi.decolorize(message)

        try:
            self.socket.sendall(message.encode())
        except OSError:
            pass


class TelnetServer(Server):

    CONNECTION_CLASS = TelnetConnection

    def init(self):
        self.ports = []

    def create_server(self, entry):
        """Create a port to listen on."""
        host = entry["host"]
        port = entry["port"]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind((host, port))
        sock.listen(1)

        self.ports.append(sock)
        gevent.spawn(self.accept_port_connections, sock)

        logging.info("Started telnet server: {}:{}".format(host, port))

    def handle_connection(self, sock, addr):
        connection = self.CONNECTION_CLASS(sock, addr, self)
        self.add_connection(connection)
        connection.start()

    def get_port_entries(self):
        from settings import TELNET_PORTS
        return TELNET_PORTS

    def accept_port_connections(self, port):
        while self.running:
            sock, addr = port.accept()
            gevent.spawn(self.handle_connection, sock, addr)
            gevent.sleep(0.1)

    def start(self):
        """Instantiate the servers/ports and sockets."""
        super(TelnetServer, self).start()

        port_infos = self.get_port_entries()

        self.running = True

        for entry in port_infos:
            self.create_server(entry)

        while self.running:
            for connection in self.connections:
                connection.handle_next_input()
                connection.handle_flushing_output()
            gevent.sleep(0.01)


class Telnet(Module):
    MODULE_NAME = "Telnet"
    VERSION = "0.1.0"

    MANAGERS = [
        TelnetServer,
    ]
