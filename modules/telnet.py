from gevent import monkey
from mud.client import Client
from mud.inject import inject
from mud.connection import Connection
from mud.server import Server
from mud.module import Module
from utils.ansi import colorize, decolorize
from utils.fuzzy_resolver import FuzzyResolver

import gevent
import settings
import socket as raw_socket

monkey.patch_all()


class TelnetClient(Client):
    INITIAL_STATE = "login_username"

    def __init__(self, *args, **kwargs):
        super(TelnetClient, self).__init__(*args, **kwargs)
        self.write_ended_with_newline = False

        self.temporary_actor = None
        self.prompt_thread = False
        self.resolver = FuzzyResolver(self.game.commands)
        self.color = True
        self.write("""


            ;::::;                             Original DIKUMUD by Hans
           ;::::; :;                         Staerfeldt, Katja Nyboe, Tom
         ;:::::'   :;                        Madsen, Michael Seirfert and
        ;:::::;     ;.                       Sebastiand Hammer. (c) 1991
       ,:::::'       ;           OOO\\
       ::::::;       ;          OOOOO\\         MERC 2.1 Code by Hatchet,
       ;:::::;       ;         OOOOOOOO      Furey and Kahn. (c) 1993
      ,;::::::;     ;'         / OOOOOOO
    ;:::::::::`. ,,,;.        /  / DOOOOOO     RoM 2.4 Code by Russ Taylor.
  .';:::::::::::::::::;,     /  /    DOOOO   (c) 1996
 ,::::::;::::::;;;;::::;,   /  /       DOOO
;`::::::`'::::::;;;::::: ,#/  /        DOOO    RoT 1.4 Code by Russ Welsh.
:`:::::::`;::::::;;::: ;::#  /          DOOO (c) 1997
::`:::::::`;:::::::: ;::::# /            DOO
`:`:::::::`;:::::: ;::::::#/             DOO   WDM 2.0 Code by Waterdeep
 :::`:::::::`;; ;:::::::::##              OO MUD Entertainmant. (c) 2007
 ::::`:::::::`;::::::::;:::#              OO
 `:::::`::::::::::::;'`:;::#              O  Owned & Operated by Kelemvor
  `:::::`::::::::;' /  / `:#                 E-Mail:  wdmudimms@gmail.com
   ::::::`:::::;'  /  /   `#
           ##    ##  ####  ###### ######  ####  ######  ###### ###### #####
           ##    ## ##  ##   ##   ##     ##  ##  ##  ## ##     ##     ##  ##
           ## ## ## ######   ##   ####   ##  ##  ##  ## ####   ####   #####
           ## ## ## ##  ##   ##   ##     #####   ##  ## ##     ##     ##
            ##  ##  ##  ##   ##   ###### ##  ## ######  ###### ###### ##
                          C I T Y  O F  S P L E N D O R S
                                   [ Est 1997 ]

What is your name, adventurer? """)

    @property
    @inject("Characters")
    def actor(self, Characters):
        return Characters.get(self.connection.actor_id)

    def stop(self):
        self.writeln("Disconnecting..")

    def handle_login_username_input(self, message):
        Characters = self.game.get_injector("Characters")
        name = message.strip().lower().title()

        found = Characters.get({"name": name})

        if not found:
            self.temporary_actor = Characters.ENTITY_CLASS({
                "name": name,
                "connection_id": self.connection.id,
            })
            self.start_verify_name()
            return

        found.online = False
        found.save()

        self.connection.actor_id = found.id

        if found.connection:
            found.echo(
                "You have been kicked off due to another logging in.")
            found.connection.close()

        self.start_motd()

    def start_verify_name(self):
        self.write("""
{{B+{{b------------------------{{B[ {{CWelcome to Waterdeep {{B]{{b\
-------------------------{{B+{{x

  We are a roleplaying -encouraged- mud, meaning roleplaying is not
  required by our players but we do require non-roleplayers abide by a few
  rules and regulations.  All character names must meet a certain standard
  of quality in order to foster a more immersive and creative environment.
  The staff retains the right to make the final judgment of whether a character
  name meets the standard.
  Some guidelines:

    {{C1{{c.{{x Do not use names such as Joe, Bob, Larry, Carl and so forth.
       'Exotic' proper names like 'Xavier' and such -may- be acceptable.
    {{C2{{c.{{x Do not name yourself after a deity, fictional or otherwise.
    {{C3{{c.{{x Do not use the names of well-known fictional characters.
    {{C4{{c.{{x Names should fit with the fantasy/steampunk theme of the mud.

  If we find your name is not suitable for our environment, an immortal
  staff member will appear before you and offer you a rename.  Please be
  nice and civil, and we will return with the same. If you need help developing
  a name for your character there are many websites that generate random names.

{{B+{{b--------------{{B[ {{RThis MUD is rated R for Mature Audiences {{B]{{b\
---------------{{B+{{x

Did I get that right, {} (Y/N)? """.format(self.temporary_actor.name))
        self.state = "verify_name"

    @inject("Characters")
    def handle_verify_name_input(self, message, Characters):
        self.start_select_password()

    def start_select_password(self):
        self.state = "select_password"
        self.write("""
A new life has been created.

Please choose a password (max 8 characters) for {}: """.format(
            self.temporary_actor.name))

    def handle_select_password_input(self, message):
        self.start_select_race()
        self.temporary_actor.password = "test"

    def start_select_race(self):
        self.state = "select_race"
        self.write("""
+---------------------------[ Pick your Race ]----------------------------+

  Welcome to the birthing process of your character.  Below you will
  find a list of available races and their basic stats.  You will gain
  an additional +2 points on a specific stat depending on your choice
  of class.  For detailed information see our website located at
  http://waterdeep.org or type HELP (Name of Race) below.

            STR INT WIS DEX CON                 STR INT WIS DEX CON
  Avian     17  19  20  16  17      HalfElf     17  18  19  18  18
  Centaur   20  17  15  13  21      HalfOrc     19  15  15  20  21
  Draconian 22  18  16  15  21      Heucuva     25  10  10  25  25
  Drow      18  22  20  23  17      Human       21  19  19  19  21
  Dwarf     20  18  22  16  21      Kenku       19  19  21  20  19
  Elf       16  20  18  21  15      Minotaur    23  16  15  16  22
  Esper     14  21  21  20  14      Pixie       14  20  20  23  14
  Giant     22  15  18  15  20      Podrikev    25  18  18  15  25
  Gnoll     20  16  15  20  19      Thri'Kreen  17  22  22  16  25
  Gnome     16  23  19  15  15      Titan       25  18  18  15  25
  Goblin    16  20  16  19  20      Satyr       23  19  10  14  21
  Halfling  15  20  16  21  18

+-------------------------------------------------------------------------+

Please choose a race, or HELP (Name of Race) for more info: """)

    def handle_select_race_input(self, message):
        self.start_select_gender()
        self.temporary_actor.race_ids = ["human"]

    def start_select_gender(self):
        self.state = "select_gender"
        self.write("""
+--------------------------[ Pick your Gender ]---------------------------+

                                  Male
                                  Female
                                  Neutral

+-------------------------------------------------------------------------+

Please choose a gender for your character: """)

    def handle_select_gender_input(self, message):
        self.start_select_class()
        self.temporary_actor.gender_id = "male"

    def start_select_class(self):
        self.state = "select_class"
        self.write("""
+--------------------------[ Pick your Class ]---------------------------+

  Waterdeep has a 101 level, 2 Tier remorting system.  After the first
  101 levels you will reroll and be able to choose a new race and class.
  2nd Tier classes are upgrades from their 1st tier counterparts.

  For more information type HELP (Name of Class) to see their help files.

                               Mage
                               Cleric
                               Thief
                               Warrior
                               Ranger
                               Druid
                               Vampire

+-------------------------------------------------------------------------+

Select a class or type HELP (Class) for details: """)

    def handle_select_class_input(self, message):
        self.temporary_actor.class_ids = ["adventurer"]
        self.start_select_alignment()

    def start_select_alignment(self):
        self.state = "select_alignment"
        self.temporary_actor.alignment = 0
        self.write("""
+------------------------[ Pick your Alignment ]-------------------------+

  Your alignment will effect how much experience you get from certain
  mobiles, such as you gain less experience if you are evil, and you kill
  evil mobiles.  You gain more for killing good mobiles.  There are spells
  available that can counter this effect.

                                  Good
                                  Neutral
                                  Evil

+-------------------------------------------------------------------------+

Choose your alignment: """)

    def handle_select_alignment_input(self, message):
        self.start_confirm_customize()

    def start_confirm_customize(self):
        self.state = "confirm_customize"
        self.write("""
+----------------------[ Character Customization ]-----------------------+

  Your character is given a basic set of skills and or spells depending
  on your choice of class.  You can customize your character which allows
  you to choose from a wider range of skills and abilities.

+-------------------------------------------------------------------------+

Do you wish to customize? (Yes or No): """)

    def handle_confirm_customize_input(self, message):
        self.start_customize()

    def start_customize(self):
        self.state = "customize"
        self.write("""
+----------------------[ Character Customization ]-----------------------+

  The following groups and skills are available to your character:
  (this list may be seen again by typing list)

  Group              CP    Group              CP    Group              CP
---------------------------------------------------------------------------------
  vampire default    40    weaponsmaster      30    attack             5
  beguiling          6     benedictions       3     combat             5
  detection          4     enhancement        6     harmful            6
  illusion           4     maladictions       5     protective         7
  transportation     4     weather            7
---------------------------------------------------------------------------------

  Skill              CP    Skill              CP    Skill              CP
---------------------------------------------------------------------------------
  axe                5     flail              5     mace               3
  polearm            5     shield block       3     spear              5
  sword              3     whip               5     dirt kicking       2
  disarm             3     dodge              2     enhanced damage    7
  envenom            3     feed               2     leech              4
  hand to hand       2     kick               2     lance              2
  parry              2     trip               3     rub                4
  second attack      2     third attack       3     hotswap            2
  butcher            3     fast healing       1     peek               4
  pick lock          8     swim               3     necroticstrike     2
---------------------------------------------------------------------------------

  Creation Points      : 0
  Experience per Level : 1000

  You already have the following skills:

  Level     Skill               %       Skill               %
-----------------------------------------------------------------
    1:      dagger             n/a      hide               n/a
            scrolls            n/a      staves             n/a
            wands              n/a      recall             n/a
    2:      sneak              n/a
-----------------------------------------------------------------

+-------------------------------------------------------------------------+


Choice (add, drop, list, help)? """)

    def handle_customize_input(self, message):
        self.start_select_weapon()

    def start_select_weapon(self):
        self.state = "select_weapon"
        self.write("""
+-------------------------[ Pick your Weapon ]---------------------------+

  Please pick a weapon to learn from the following choices:

  dagger
+-------------------------------------------------------------------------+

Your choice? """)

    @inject("Characters")
    def handle_select_weapon_input(self, message, Characters):
        actor = Characters.save(self.temporary_actor)
        self.connection.actor_id = actor.id
        self.start_motd()

    def start_motd(self):
        self.state = "motd"
        self.write(r"""

                                                          __
                                                        //  \\
                                                       // /\ \\
                                                       \\ \/ //
                                                        \\__//
                                                        [|//|]
                                                        [|//|]
               Welcome to                               [|//|]
                                                        [|//|]
            W A T E R D E E P                           [|//|]
                                                        [|//|]
            City of Splendors                /)         [|//|]        (\
                                            //\_________[|//|]________/\\
                est. 1997                   ))__________||__||_________((
                                           <_/         [  \/  ]        \_>
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
                                                       \\    //
                                                        \\  //
                                                         \\//
                                                          \/
[Hit Enter to Continue] """)

    def handle_motd_input(self, message):
        self.writeln("""
Welcome to Waterdeep 'City Of Splendors'!  Please obey the rules, (help rules).
""")
        self.start_playing()

    def start_playing(self):
        actor = self.actor
        actor.online = True
        actor.connection_id = self.connection.id
        actor.save()

        self.state = "playing"
        actor.act("{self.name} slowly fades into existence.")
        self.handle_playing_input("look")

    def quit(self):
        self.connection.close()
        self.actor.act("{self.name} slowly fades out of existence.")

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
            kwargs["name"] = real_name
            command = entry["handler"]
            break

        if command:
            try:
                self.game.wiznet(
                    "log", "{}: {}".format(actor.name, message),
                    exclude=[actor])
                delay = command(actor, **kwargs)
            except Exception as e:
                self.game.handle_exception(e)
                self.writeln("Huh?!")
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
        self.server.remove_connection(self)

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
