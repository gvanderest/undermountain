from gevent import monkey
from mud.module import Module
from mud.server import Server
from mud.connection import Connection
from mud.client import Client
from mud.entities import Character
from mud.inject import inject
import logging
import gevent
import socket
import settings

monkey.patch_socket()


class TelnetServer(Server):
    def init(self):
        self.sockets = []

    def start(self):
        """Start up the server."""
        for host, port in settings.TELNET_PORTS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen()
            self.sockets.append(sock)
            logging.info("Created Telnet socket {}:{}".format(host, port))
            gevent.spawn(self.accept_connections, sock)

    def accept_connection(self, sock):
        clientsocket, address = sock.accept()
        conn = TelnetConnection(self, clientsocket, address)
        return conn

    def stop(self):
        pass


class TelnetClient(Client):
    def init(self):
        self.write("""\


            ;::::;
           ;::::; :;
         ;:::::'   :;
        ;:::::;     ;.
       ,:::::'       ;           OOO\\
       ::::::;       ;          OOOOO\\
       ;:::::;       ;         OOOOOOOO
      ,;::::::;     ;'         / OOOOOOO
    ;:::::::::`. ,,,;.        /  / DOOOOOO
  .';:::::::::::::::::;,     /  /    DOOOO
 ,::::::;::::::;;;;::::;,   /  /       DOOO
;`::::::`'::::::;;;::::: ,#/  /        DOOO
:`:::::::`;::::::;;::: ;::#  /          DOOO
::`:::::::`;:::::::: ;::::# /            DOO
`:`:::::::`;:::::: ;::::::#/             DOO
 :::`:::::::`;; ;:::::::::##              OO
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

Why have you come....go away or choose a name: """)

    @inject("Characters")
    def handle_login_name_input(self, line, Characters):
        actor = Character({"name": line})
        self.set_actor(actor)
        actor.set_client(self)

        Characters.save(actor)

        self.start_confirming_name()

    def start_confirming_name(self):
        self.state = self.STATE_CONFIRM_NAME
        self.write("""\
+------------------------[ Welcome to Waterdeep ]-------------------------+

  We are a roleplaying -encouraged- mud, meaning roleplaying is not
  required by our players but we do require non-roleplayers abide by a few
  rules and regulations.  All character names must meet a certain standard
  of quality in order to foster a more immersive and creative environment.
  The staff retains the right to make the final judgment of whether a character
  name meets the standard.
  Some guidelines:

    1. Do not use names such as Joe, Bob, Larry, Carl and so forth.
       'Exotic' proper names like 'Xavier' and such -may- be acceptable.
    2. Do not name yourself after a deity, fictional or otherwise.
    3. Do not use the names of well-known fictional characters.
    4. Names should fit with the fantasy/steampunk theme of the mud.

  If we find your name is not suitable for our environment, an immortal
  staff member will appear before you and offer you a rename.  Please be
  nice and civil, and we will return with the same. If you need help developing
  a name for your character there are many websites that generate random names.

+--------------[ This MUD is rated R for Mature Audiences ]---------------+

Did I get that right, {} (Y/N)? """.format(self.actor.name))

    def start_reprompt_for_name(self):
        self.write("So what's your name? ")
        self.state = self.STATE_LOGIN_NAME

    def handle_confirm_name_input(self, line):
        if line.lower().startswith("n"):
            self.start_reprompt_for_name()
        else:
            self.start_selecting_race()

    def start_selecting_race(self):
        self.state = self.STATE_SELECT_RACE
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

    def handle_select_race_input(self, line):
        self.actor.race_id = line
        self.start_selecting_gender()

    def start_selecting_gender(self):
        self.write("""
+--------------------------[ Pick your Gender ]---------------------------+

                                  Male
                                  Female
                                  Neutral

+-------------------------------------------------------------------------+

Please choose a gender for your character: """)
        self.state = self.STATE_SELECT_GENDER

    def handle_select_gender_input(self, line):
        self.actor.gender_id = line
        self.start_selecting_class()

    def start_selecting_class(self):
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
        self.state = self.STATE_SELECT_CLASS

    def handle_select_class_input(self, line):
        self.actor.class_id = line
        self.start_motd()

    def start_motd(self):
        self.state = self.STATE_MOTD
        self.write("""


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
""")

    def handle_motd_input(self, line):
        self.start_playing()

    def start_playing(self):
        self.actor.force("look")
        self.state = self.STATE_PLAYING

    def handle_playing_input(self, line):
        self.actor.handle_input(line)


class Telnet(Module):
    def init(self):
        self.game.add_manager(TelnetServer)


class TelnetConnection(Connection):
    CLIENT_CLASS = TelnetClient

    def __init__(self, server, sock, address):
        self.socket = sock
        self.address = address
        super(TelnetConnection, self).__init__(server)

    def read(self):
        try:
            content = self.socket.recv(4096).decode("utf-8")
            if content == "":
                return None
        except UnicodeDecodeError:
            content = ""
        except OSError:
            content = None

        return content

    def write(self, output):
        self.socket.send(output.encode("utf-8"))

    def close(self):
        self.socket.close()
