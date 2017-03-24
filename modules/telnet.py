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
from settings import DEFAULT_TELNET_PROMPT, RACES, CLASSES, GENDERS

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

    def is_valid_username(self, username):
        from settings import BANNED_NAMES, BANNED_NAME_PREFIXES
        username = username.lower()

        if len(username) < 3:
            return False

        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyz":
                return False

        if username in BANNED_NAMES:
            return False

        for prefix in BANNED_NAME_PREFIXES:
            if username.startswith(prefix.lower()):
                return False

        return True

    def handle_login_username_input(self, message):
        """Handle logging in username prompt."""
        from modules.core import Character
        username = Character.clean_name(message)

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

        # This Character does not exist, go to creation screens
        if not actor:
            Characters = self.get_injector("Characters")
            actor = Characters.save({
                "name": self.name,
                "online": False,
                "organizations": {},
            })
            self.actor_id = actor.id
            actor.set_client(self)

            self.writeln("Thanks for providing your name, {}!".format(actor.name))
            self.writeln()

            self.start_race_selection_screen()
            return
        else:
            self.actor_id = actor.id
            actor.set_client(self)

        # That Actor is already in the Game, reconnect?
        if actor.online:

            self.write_login_reconnect_confirm_prompt()
            self.state = "login_reconnect_confirm"
            return

        self.start_motd_screen()

    def start_race_selection_screen(self):
        self.state = "race_selection"
        self.write_race_selection_screen()
        self.write_race_selection_prompt()

    def write_race_selection_screen(self):
        self.echo("""
{B+{b---------------------------{B[ {CPick your Race {B]{b----------------------------{B+
{x
  Welcome to the birthing process of your character.  Below you will
  find a list of available races and their basic stats.  You will gain
  an additional +2 points on a specific stat depending on your choice
  of class.  For detailed information see our website located at
  http://waterdeep.org or type HELP (Name of Race) below.

            {GSTR INT WIS DEX CON                 STR INT WIS DEX CON
  {CA{cvian     {g17  19  20  16  17      {CH{calfElf     {g17  18  19  18  18
  {CC{centaur   {g20  17  15  13  21      {CH{calfOrc     {g19  15  15  20  21
  {CD{craconian {g22  18  16  15  21      {CH{ceucuva     {g25  10  10  25  25
  {CD{crow      {g18  22  20  23  17      {CH{cuman       {g21  19  19  19  21
  {CD{cwarf     {g20  18  22  16  21      {CK{cenku       {g19  19  21  20  19
  {CE{clf       {g16  20  18  21  15      {CM{cinotaur    {g23  16  15  16  22
  {CE{csper     {g14  21  21  20  14      {CP{cixie       {g14  20  20  23  14
  {CG{ciant     {g22  15  18  15  20      {CP{codrikev    {g25  18  18  15  25
  {CG{cnoll     {g20  16  15  20  19      {CT{chri'Kreen  {g17  22  22  16  25
  {CG{cnome     {g16  23  19  15  15      {CT{citan       {g25  18  18  15  25
  {CG{coblin    {g16  20  16  19  20      {CS{catyr       {g23  19  10  14  21
  {CH{calfling  {g15  20  16  21  18

{B+{b-------------------------------------------------------------------------{B+{x
""")

    def write_race_selection_prompt(self):
        self.write("Please choose a race: ")

    def handle_race_selection_input(self, message):
        cleaned = message.lower().strip()

        race_found = None

        if cleaned:
            for race_id in RACES.keys():
                if race_id.startswith(cleaned):
                    race_found = race_id
                    break

        if not race_found:
            self.echo("The race you selected is not valid.")
            self.echo()
            self.write_race_selection_prompt()
            return

        actor = self.get_actor()
        actor.race_id = race_found
        actor.save()

        self.start_gender_selection_screen()

    def start_gender_selection_screen(self):
        self.state = "gender_selection"
        self.write_gender_selection_screen()
        self.write_gender_selection_prompt()

    def write_gender_selection_screen(self):
        self.echo("""
{B+{b--------------------------{B[ {CPick your Gender {B]{g---------------------------{B+

                                  {BMale
                                  {MFemale
                                  {xNeutral

{B+{b-------------------------------------------------------------------------{B+{x
""")

    def write_gender_selection_prompt(self):
        self.write("Please choose a gender for your character: ")

    def handle_gender_selection_input(self, message):
        cleaned = self.clean_message(message)

        gender_found = None

        for gender_id in GENDERS.keys():
            if gender_id.startswith(cleaned):
                gender_found = gender_id
                break

        if not gender_found:
            self.echo("The gender you selected is not available.")
            self.echo()
            self.write_gender_selection_prompt()
            return

        actor = self.get_actor()
        actor.gender_id = gender_found
        actor.save()
        self.start_class_selection_screen()

    def start_class_selection_screen(self):
        self.state = "class_selection"
        self.write_class_selection_screen()
        self.write_class_selection_prompt()

    def write_class_selection_screen(self):
        self.echo("""
{B+{b--------------------------{B[ {CPick your Class {B]{b---------------------------{B+{x

  Waterdeep has a 101 level, 2 Tier remorting system.  After the first
  101 levels you will reroll and be able to choose a new race and class.
  2nd Tier classes are upgrades from their 1st tier counterparts.

  For more information type HELP (Name of Class) to see their help files.

                               {RM{rage
                               {RC{rleric
                               {RT{rhief
                               {RW{rarrior
                               {RR{ranger
                               {RD{rruid
                               {RV{rampire

{B+{b-------------------------------------------------------------------------{B+{x
""")

    def write_class_selection_prompt(self):
        self.write("Select a class or type HELP (Class) for details: ")

    def handle_class_selection_input(self, message):
        cleaned = self.clean_message(message)

        found_class = None

        for class_id, class_details in CLASSES.items():
            if class_id.startswith(cleaned) and class_details["tier"] == 1:
                found_class = class_id
                break

        if not found_class:
            self.echo("The class you selected is not valid.")
            self.write_class_selection_prompt()
            return

        actor = self.get_actor()
        actor.class_id = found_class
        actor.save()

        self.start_motd_screen()

    def start_motd_screen(self):
        self.state = "motd"
        self.write_motd_screen()

    def write_motd_screen(self):
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

    def handle_motd_input(self, message):
        self.state = "playing"

        self.handle_input("look")
        self.handle_input("unread")
        self.handle_input("version")

        actor = self.get_actor()
        actor.online = True
        actor.save()

        self.wiznet("connect", "%s has connected" % (actor.name))

    def wiznet(self, *args, **kwargs):
        game = self.get_game()
        return game.wiznet(*args, **kwargs)

    def write_login_reconnect_confirm_prompt(self):
        self.writeln("That character is already playing.")
        self.write("Would you like to reconnect? [Y/N] ")

    @classmethod
    def clean_message(cls, message):
        return message.strip().lower()

    def handle_login_reconnect_confirm_input(self, message):
        cleaned = self.clean_message(message)

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

    def get_actor_prompt(self, actor):
        if not actor:
            return ""

        if actor.is_afk():
            prompt = "<AFK>"
        else:
            prompt = (actor.prompt or DEFAULT_TELNET_PROMPT) + "{x"

        if not prompt.endswith("\n"):
            prompt += " "

        room = actor.get_room()
        area = room.get_area()

        if "%h" in prompt:
            prompt = prompt.replace("%h", actor.get("current_hp", str(0)))

        if "%H" in prompt:
            prompt = prompt.replace("%H", actor.get("hp", str(0)))

        if "%m" in prompt:
            prompt = prompt.replace("%m", actor.get("current_mana", str(0)))

        if "%M" in prompt:
            prompt = prompt.replace("%M", actor.get("mana", str(0)))

        if "%c" in prompt:
            prompt = prompt.replace("%c", "\n")

        if "%v" in prompt:
            prompt = prompt.replace("%v", actor.get("current_moves", str(0)))

        if "%V" in prompt:
            prompt = prompt.replace("%V", actor.get("moves", str(0)))

        if "%x" in prompt:
            prompt = prompt.replace("%x", str(0))

        if "%X" in prompt:
            prompt = prompt.replace("%X", str(0))

        if "%r" in prompt:
            prompt = prompt.replace("%r", room.name)

        if "%N" in prompt:
            prompt = prompt.replace("%N", actor.name)

        if "%q" in prompt:
            prompt = prompt.replace("%q", str(0))

        if "%Q" in prompt:
            prompt = prompt.replace("%Q", str(0))

        if "%j" in prompt:
            prompt = prompt.replace("%j", str(0))

        if "%J" in prompt:
            prompt = prompt.replace("%J", str(0))

        if "%a" in prompt:
            prompt = prompt.replace("%a", str(0))

        if "%t" in prompt:
            prompt = prompt.replace("%t", "12{Bam")

        if "%g" in prompt:
            prompt = prompt.replace("%g", "{G" + str(0))

        if "%e" in prompt:
            prompt = prompt.replace("%e", "NESWDU")

        if "%R" in prompt:
            prompt = prompt.replace("%R", "0")

        if "%z" in prompt:
            prompt = prompt.replace("%R", area.name)

        return prompt

    def write_playing_prompt(self):
        conn = self.connection
        if conn.output_buffer and \
                conn.output_buffer[-2:] != (2 * self.NEWLINE):
            self.writeln()

        actor = self.get_actor()

        prompt = self.get_actor_prompt(actor)
        self.write(prompt)

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

    def handle_playing_input(self, message):
        if message == "!":
            if self.last_command is None:
                self.writeln("Huh?")
                self.write_playing_prompt()
            else:
                self.handle_playing_input(self.last_command)
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
            self.handle_flushing_output()
        except Exception:
            pass
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.socket.close()
        except Exception:
            pass

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
