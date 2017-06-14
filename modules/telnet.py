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
from modules.core import Character

gevent.monkey.patch_socket()


class TelnetClient(Client):
    """Wrapper for how our Game works."""
    def init(self):
        self.last_command = None
        self.actor_id = None
        self.username = None

    def hide_next_input(self):
        super(TelnetClient, self).hide_next_input()
        self.connection.flush()
        self.connection.hide_next_input()

    def show_next_input(self):
        super(TelnetClient, self).show_next_input()
        self.connection.flush()
        self.connection.show_next_input()
        self.writeln()

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
        username = Character.clean_name(message)

        if not self.is_valid_username(username):
            self.writeln("The name you provided is not valid.")
            self.writeln("* Must be at least 3 characters in length")
            self.writeln("* Must only contain letters")
            self.writeln("* Must not be a reserved or banned name")
            self.writeln()
            self.write_login_username_prompt()
            return

        self.username = username

        if not message:
            self.writeln("Please pick a name, even if it's short.")
            self.write_login_username_prompt()
            return

        actor = self.get_character(self.username)

        # This Character does not exist, go to creation screens
        if actor:
            self.start_login_password_screen()
        else:
            self.start_name_creation_screen()

    def start_login_password_screen(self):
        self.state = "login_password"
        self.write_login_password_prompt()

    def write_login_password_prompt(self):
        self.write("Password: ")
        self.hide_next_input()

    def handle_login_password_input(self, message, Characters):
        actor = Characters.find({"name": self.username})

        if not actor:
            self.echo("Somehow, your Character disappeared.")
            self.state = "login_username"
            self.write("Who are you again? ")
            return

        password = Character.generate_password(message)
        if actor.password != password:
            self.echo("The password you provided is incorrect.")
            self.connection.destroy()
            return

        if actor.online:
            self.start_login_reconnect_screen()
            return

        self.set_actor(actor)
        actor.set_client(self)

        self.start_motd_screen()

    def start_login_reconnect_screen(self):
        self.echo("That character is already logged in.")
        self.write("Would you like to replace them? [y/N] ")
        self.state = "login_reconnect"

    def handle_login_reconnect_input(self, message, Characters):
        game = self.get_game()
        actor = Characters.find({"name": self.username})

        if message.lower().startswith('y'):
            self.echo("Attempting reconnect..")
            existing_connection = game.get_actor_connection(actor)
            existing_actor = existing_connection.get_actor()

            existing_actor.set_client(self)
            self.set_actor(existing_actor)

            existing_connection.destroy()
            self.state = 'playing'
        else:
            self.write("Who are you? ")
            self.state = "login_username"

    def start_name_creation_screen(self):
        self.state = "name_creation"
        self.write_name_creation_screen()
        self.write_name_creation_prompt()

    def write_name_creation_screen(self):
        self.echo("""
{B+{b------------------------{B[ {CWelcome to Waterdeep {B]{b-------------------------{B+{x

  We are a roleplaying -encouraged- mud, meaning roleplaying is not
  required by our players but we do require non-roleplayers abide by a few
  rules and regulations.  All character names must meet a certain standard
  of quality in order to foster a more immersive and creative environment.
  The staff retains the right to make the final judgment of whether a character
  name meets the standard.
  Some guidelines:

    {C1{c.{x Do not use names such as Joe, Bob, Larry, Carl and so forth.
       'Exotic' proper names like 'Xavier' and such -may- be acceptable.
    {C2{c.{x Do not name yourself after a deity, fictional or otherwise.
    {C3{c.{x Do not use the names of well-known fictional characters.
    {C4{c.{x Names should fit with the fantasy/steampunk theme of the mud.

  If we find your name is not suitable for our environment, an immortal
  staff member will appear before you and offer you a rename.  Please be
  nice and civil, and we will return with the same. If you need help developing
  a name for your character there are many websites that generate random names.

{B+{b---------------{B[ {RThis MUD is rated for Mature Audiences {B]{b----------------{B+{x
""")

    def write_name_creation_prompt(self):
        self.write("Did I get that right, %s (Y/N)? " % (self.username))

    def handle_name_creation_input(self, message):
        cleaned = self.clean_message(message)
        if cleaned.startswith("y"):
            self.start_password_creation_screen()

        elif cleaned.startswith("n"):
            self.username = None
            self.state = "login_username"
            self.write_login_username_prompt()

        else:
            self.write_name_creation_prompt()

    def start_password_creation_screen(self):
        self.state = "password_creation"
        self.write("Pick your password: ")
        self.hide_next_input()

    def handle_password_creation_input(self, message):
        if not message:
            self.writeln("Password must be provided.")
            self.write("Pick your password: ")
            return

        self.password = Character.generate_password(message)

        self.start_password_verification_screen()

    def start_password_verification_screen(self):
        self.state = "password_verification"
        self.write("Verify your password: ")
        self.hide_next_input()

    def handle_password_verification_input(self, message, Characters):
        password = Character.generate_password(message)

        if password != self.password:
            self.writeln("The two passwords provided do not match.")
            self.writeln()
            self.password = None
            self.start_password_creation_screen()
            return

        self.password = None

        actor = Characters.save({
            "name": self.username,
            "password": password
        })

        self.set_actor(actor)
        actor.set_client(self)

        self.start_race_selection_screen()

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
        actor.login()
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
        actor = self.get_character(self.username)

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

    def get_actor_prompt(self):
        actor = self.get_actor()
        if not actor:
            return ""

        if actor.has_flag("cinematic"):
            return ""

        lines = []

        if actor.is_afk():
            prompt = "<AFK>"
        else:
            prompt = (actor.prompt or DEFAULT_TELNET_PROMPT) + "{x"

        if not prompt.endswith("\n"):
            prompt += " "

        room = actor.get_room()
        area = room.get_area()

        if "%h" in prompt:
            prompt = prompt.replace(
                "%h", str(actor.get_stat_total('current_hp')))

        if "%H" in prompt:
            prompt = prompt.replace("%H", str(actor.get_stat_total('hp')))

        if "%m" in prompt:
            prompt = prompt.replace(
                "%m", str(actor.get_stat_total('current_mana')))

        if "%M" in prompt:
            prompt = prompt.replace("%M", str(actor.get_stat_total('mana')))

        if "%c" in prompt:
            prompt = prompt.replace("%c", "\n")

        if "%v" in prompt:
            prompt = prompt.replace(
                "%v", str(actor.get_stat_total('current_moves')))

        if "%V" in prompt:
            prompt = prompt.replace("%V", str(actor.get_stat_total('moves')))

        if "%x" in prompt:
            prompt = prompt.replace("%x", str(actor.get_experience()))

        if "%X" in prompt:
            prompt = prompt.replace(
                "%X", str(actor.get_level_experience_remaining()))

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

        # If in combat, add information on the target
        if actor.is_fighting():
            primary_target = actor.get_targets()[0]
            hp = primary_target.get_stat_total("hp")
            current_hp = primary_target.get_stat_total("current_hp")
            percent = (current_hp / hp) if hp != 0 else 0

            if percent <= 0.333:
                color = "{R"
            elif percent <= 0.666:
                color = "{Y"
            else:
                color = "{G"

            line = "{R%s {Ris in excellent condition. {x[%s%0.1f%%{x]" % (
                primary_target.format_name_to(actor),
                color,
                percent * 100)
            lines.append(line)

        lines.append(prompt)

        return "\n\n".join(lines)

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
        actor.logout()
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

    def hide_next_input(self):
        self.socket.sendall(b"\xFF\xFB\x01")

    def show_next_input(self):
        self.socket.sendall(b"\xFF\xFC\x01")

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
            self.flush()
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

    def flush(self):
        if not self.output_buffer:
            return

        message = self.output_buffer
        self.output_buffer = ""

        # Prefix with newlines and append prompt
        actor = self.get_actor()
        if actor and actor.is_online():
            prompt = self.client.get_actor_prompt()
            if message.endswith("\n"):
                message = "\n" + message
            else:
                message = "\n\n" + message
            message += "\n" + prompt

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
                connection.flush()
            gevent.sleep(0.01)


class Telnet(Module):
    MODULE_NAME = "Telnet"
    VERSION = "0.1.0"

    MANAGERS = [
        TelnetServer,
    ]
