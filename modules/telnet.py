from gevent import monkey
from mud.client import Client
from mud.inject import inject
from mud.connection import Connection
from mud.server import Server
from mud.module import Module
from utils.ansi import colorize, decolorize
from utils.hash import hash_password, password_is_valid
from utils.fuzzy_resolver import FuzzyResolver

import gevent
import settings
import socket as raw_socket

monkey.patch_all()

badusernames = "about access account accounts activate add address adm admin administration administrator adult advertising affiliate affiliates ajax analytics android anon anonymous api app apple apps arabic archive archives atom auth authentication avatar awadhi azerbaijani backup banner banners bengali better bhojpuri billing bin blog blogs board bot bots burmese business cache cadastro calendar campaign cancel careers cart cgi changelog chat checkout chinese client cliente code codereview comercial compare compras config configuration connect contact contest create css cvs dashboard data delete demo design designer dev devel dir direct direct_messages directory doc docs documentation domain download downloads dutch ecommerce edit editor edits email employment english enterprise exchange facebook faq farsi favorite favorites feed feedback feeds file files fleet fleets flog follow followers following forum forums free french friend friends ftp gadget gadgets games gan german gist git github google group groups guest gujarati hakka hausa help hindi home homepage host hosting hostmaster hostname hpg html http httpd https idea ideas image images imap img index indice info information intranet invitations invite ipad iphone irc italian japanese java javanese javascript jinyu job jobs json kannada knowledgebase korean language languages list lists local localhost log login logout logs mail mail1 mail2 mail3 mail4 mail5 mailer mailing maithili malayalam manager mandarin map maps marathi marketing master media message messenger microblog microblogs min-nan mine mis mob mobile mobilemail movie movies mp3 msg msn music musicas mysql name named net network new news newsletter nick nickname notes noticias null none ns1 ns2 ns3 ns4 oauth oauth_clients offers old online openid operator order orders organizations oriya page pager pages panel panjabi password pda perl photo photoalbum photos php pic pics plans plugin plugins polish pop pop3 popular portuguese post postfix postmaster posts privacy profile project projects promo pub public put python random recruitment register registration remove replies repo romanian root rss ruby russian sale sales sample samples save script scripts search secure security send serbo-croatian service sessions setting settings setup sftp shop signin signup sindhi site sitemap sites smtp soporte spanish sql ssh ssl ssladmin ssladministrator sslwebmaster stage staging start stat static stats status store stores stories styleguide subdomain subscribe subscriptions sunda suporte support svn sysadmin sysadministrator system tablet tablets talk tamil task tasks tech telnet telugu terms test test1 test2 test3 teste tests thai theme themes tmp todo tools tour translations trends turkish twitter twittr ukrainian unfollow unsubscribe update upload urdu url usage user username usuario vendas video videos vietnamese visitor weather web webmail webmaster website websites webstats widget widgets wiki win workshop wws www www1 www2 www3 www4 www5 www6 www7 wwws wwww xfn xiang xml xmpp xmppSuggest xpg xxx yaml yml yoruba you yourdomain yourname yoursite yourusername"

def in_edit_mode_prompt(self):
    return "> "


def output_edit_lines(self, lines):
    self.echo("###: " + ("-" * 79))

    for index, line in enumerate(lines):
        line_number = str(index + 1).rjust(3, " ")
        self.echo("{}: {}".format(line_number, line))

    self.echo("###: " + ("-" * 79))


def in_edit_mode(self, message, args, context, **kwargs):
    args = list(args)
    command = args.pop(0)

    if command in ["@", "~"]:
        self.client.end_edit_mode()
        return True
    elif message == ".h":
        self.echo("""\
String edit help (commands on blank line):
NO .r 'old' 'new'   - replace a substring
                   (requires '', "")
.h               - get help (this info)
.s               - show string so far
NO .f               - word wrap string
NO .x ##            - smart word wrap
                   ## = width, default = 70
.c               - clear string so far
.i ## string   - insert string on new line before...
                   ## = line number
.d ##            - delete line
                   ## = line number, default is last line
@ or ~           - end string
""")
        return True

    elif command == ".c":
        context["lines"] = []
        self.echo("Lines cleared.")
        return True

    elif command == ".s":
        self.echo("Lines so far:")
        output_edit_lines(self, context["lines"])
        return True

    elif command == ".d":
        line_number = int(args.pop(0))
        line_index = line_number - 1
        line = context["lines"].pop(line_index)
        self.echo("Line {} deleted: {}".format(line_number, line))
        return True

    elif command == ".i":
        line_number = int(args.pop(0))
        line_index = line_number - 1

        new_line = " ".join(args)
        old_line = context["lines"][line_index]

        context["lines"].insert(line_index, new_line)

        self.echo("Line: {}".format(new_line))
        self.echo("Insered before line {}: {}".format(line_number, old_line))

        return True

    else:
        context["lines"].append(message)
        return True

    return False


class TelnetClient(Client):
    INITIAL_STATE = "login_username"

    def __init__(self, *args, **kwargs):
        super(TelnetClient, self).__init__(*args, **kwargs)
        self.write_ended_with_newline = False

        self.edit_data = []
        self.edit_callback = None

        self.temporary_actor = None
        self.prompt_thread = False
        self.resolver = FuzzyResolver(self.game.commands)
        self.color = True
        self.write_from_random_template("banners")
        self.write("What is your name, adventurer? ")

    def log(self, message):
        identifier = self.actor.name if self.actor \
            else self.connection.hostname
        super(TelnetClient, self).log("{}: {}".format(identifier, message))

    def start_proxy_command(
            self, command, callback=None, context=None, prompt=None):
        self.proxy_commands.append(command)
        self.proxy_callbacks.append(callback)
        self.proxy_contexts.append(context)
        self.proxy_prompts.append(prompt)

    def end_proxy_command(self, command=None):
        index = len(self.proxy_commands) - 1
        if command:
            index = self.proxy_commands.index(command)

        self.proxy_commands.pop(index)

        callback = self.proxy_callbacks.pop(index)
        context = self.proxy_contexts.pop(index)
        self.proxy_prompts.pop(index)

        if callback:
            callback(context)

        return context

    def start_edit_mode(self, callback, context=None):
        self.writeln("""\
-=======- Entering APPEND Mode -========-
    Type .h on a new line for help
 Terminate with a ~ or @ on a blank line.
-=======================================-
""")
        if not context:
            context = {}

        if "lines" not in context:
            context["lines"] = []

        self.start_proxy_command(
            command=in_edit_mode,
            callback=callback,
            context=context,
            prompt=in_edit_mode_prompt,
        )
        output_edit_lines(self.actor, context["lines"])

    def end_edit_mode(self):
        return self.end_proxy_command(in_edit_mode)

    @property
    @inject("Characters")
    def actor(self, Characters):
        return Characters.get(self.connection.actor_id)

    def stop(self):
        self.writeln("Disconnecting..")

    def restart_login_username(self):
        self.temporary_actor.name = ""
        self.write("What is your name? ")
        self.state = "login_username"

    def handle_login_username_input(self, message):
        Characters = self.game.get_injector("Characters")
        name = message.strip().lower().title()

        found = Characters.get({"name": name})

        if not found:
            self.temporary_actor = Characters.ENTITY_CLASS({
                "name": name,
                "tier": 0,
                "connection_id": self.connection.id,
                "stats": {
                    "level": 1,
                    "current_hp": 100,
                    "hp": 100,
                    "current_mana": 100,
                    "mana": 100,
                },
            })
            self.start_verify_name()
            return
        else:
            self.temporary_actor = found
            self.start_login_password()

    def start_login_password(self):
        self.write("Password: ")
        self.state = "login_password"
        self.hide_next_input()

    def handle_login_password_input(self, message):
        actor_password = self.temporary_actor.password

        if not password_is_valid(message, actor_password):
            self.writeln("Sorry, that is not the correct password.")
            self.connection.close()
            return

        found = self.temporary_actor

        if found.connection:
            found.echo(
                "You have been kicked off due to another logging in.")
            found.connection.close()

        found.online = False
        found.save()

        self.connection.actor_id = found.id

        self.temporary_actor = None

        self.start_motd()

    def start_verify_name(self):
        if len(self.temporary_actor.name) < 3:
            self.writeln("You name does not meet the length requirement. (Minimum 4).")
            self.writeln("What is your true name, adventurer? ")
            self.temporary_actor.name = None
            self.start_verify_name()
        elif badusernames.find(self.temporary_actor.name.lower()) >= 0:
            self.writeln("You name was less than appropriate. (Reserved word).")
            self.writeln("What is your true name, adventurer? ")
            self.temporary_actor.name = None
            self.start_verify_name()
        else:
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
        if message.lower().startswith("y"):
            self.writeln("A new life has been created.")
            self.writeln()
            self.start_select_password()
        elif message.lower().startswith("n"):
            self.restart_login_username()
        else:
            self.write("Is your name {} (Y/N)? ".format(
                self.temporary_actor.name))

    def start_select_password(self):
        self.state = "select_password"
        self.write(
            """Please choose a password (max 8 characters) for {}: """.format(
                self.temporary_actor.name))
        self.hide_next_input()

    def handle_select_password_input(self, message):
        if len(message) < 3:
            self.writeln("You password does not meet the length requirement. (Minimum 4)")
            self.start_select_password()
        elif self.temporary_actor.name.lower() == message.lower():
            self.writeln("Your password should not match your name.")
            self.start_select_password()
        else:
            self.temporary_actor.password = hash_password(message)
            self.start_confirm_password()

    def start_confirm_password(self):
        self.state = "confirm_password"
        self.write("Please confirm your password: ")
        self.hide_next_input()

    def handle_confirm_password_input(self, message):
        if self.temporary_actor.password != hash_password(message):
            self.writeln(
                "You did not type the same password, please try again.")
            self.start_select_password()
        else:
            self.start_select_race()

    @inject("Races")
    def start_select_race(self, Races):
        self.state = "select_race"
        output = """
+---------------------------[ Pick your Race ]----------------------------+

  Welcome to the birthing process of your character.  Below you will
  find a list of available races and their basic stats.  You will gain
  an additional +2 points on a specific stat depending on your choice
  of class.  For detailed information see our website located at
  http://waterdeep.org or type HELP (Name of Race) below.

            STR INT WIS DEX CON
"""

        for race in Races.query():
            output += "            {} 0 0 0 0 0\n".format(race.name)

        output += """

+-------------------------------------------------------------------------+

Please choose a race, or HELP (Name of Race) for more info: """
        self.write(output)

    @inject("Races")
    def handle_select_race_input(self, message, Races):
        race = Races.fuzzy_get(message)

        if not race:
            self.writeln("That race does not exist, please try again.")
            return

        self.start_select_gender()
        self.temporary_actor.race_ids = [race.id]

    @inject("Genders")
    def start_select_gender(self, Genders):
        self.state = "select_gender"
        output = """
+--------------------------[ Pick your Gender ]---------------------------+
"""

        for gender in Genders.query():
            output += "        {}\n".format(gender.name)

        output += """
+-------------------------------------------------------------------------+

Please choose a gender for your character: """

        self.write(output)

    @inject("Genders")
    def handle_select_gender_input(self, message, Genders):

        gender = Genders.fuzzy_get(message)
        if not gender:
            self.writeln("That is not a valid gender, please try again.")
            return

        self.temporary_actor.gender_id = gender.id
        self.start_select_class()

    @inject("Classes")
    def start_select_class(self, Classes):
        self.state = "select_class"
        output = """
+--------------------------[ Pick your Class ]---------------------------+

  Waterdeep has a 101 level, 2 Tier remorting system.  After the first
  101 levels you will reroll and be able to choose a new race and class.
  2nd Tier classes are upgrades from their 1st tier counterparts.

  For more information type HELP (Name of Class) to see their help files.
"""
        classes = list(Classes.query({"tier": self.temporary_actor.tier}))
        if len(classes) == 1:
            self.handle_select_class_input(classes[0].id)
            return

        for cls in classes:
            output += "{}{}\n".format(" " * 20, cls.name)

        output += """

+-------------------------------------------------------------------------+

Select a class or type HELP (Class) for details: """

        self.write(output)

    @inject("Classes")
    def handle_select_class_input(self, message, Classes):
        message = message.strip().lower()
        cls = Classes.fuzzy_get(message)
        if cls:
            self.temporary_actor.class_ids = [cls.id]
            self.save_temporary_actor()
            self.start_motd()
        else:
            self.write("""
That's not a valid class.
Try again: """)

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

    def handle_select_weapon_input(self, message):
        self.save_temporary_actor()
        self.start_motd()

    @inject("Characters")
    def save_temporary_actor(self, Characters):
        actor = Characters.save(self.temporary_actor)
        self.connection.actor_id = actor.id

    def start_motd(self):
        self.state = "motd"
        self.write_from_random_template("motds")

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
        actor.act("{actor.name} slowly fades into existence.")
        self.handle_playing_input("look")

    def quit(self):
        self.connection.close()
        self.actor.act("{actor.name} slowly fades out of existence.")

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

    def format_prompt_template(self, template):
        output = template

        """
        |      %e : Displays the exits from the room in NESWDU style.        |
        |      %R : Displays the vnum you are in (Immortal Only).            |
        |      %z : Displays the area name you are in (Immortal Only).       |
        """

        actor = self.actor
        stats = actor.stats
        room = actor.room

        level = actor.stats.level.base
        total_xp = ((level - 1) * actor.experience_per_level) + \
            actor.experience
        xp_tnl = actor.experience_per_level - actor.experience

        hp_color = "{G"
        hp = stats.hp.total
        current_hp = stats.current_hp.total
        hp_percent = (float(current_hp) / float(hp)) if hp else 0.0
        if hp_percent < (1.0 / 3.0):
            hp_color = "{R"
        elif hp_percent < (2.0 / 3.0):
            hp_color = "{Y"

        colored_hp = "{}{}".format(hp_color, current_hp)

        values = {
            "%N": actor.name,
            "%H": hp,
            "%g": colored_hp,
            "%h": current_hp,
            "%M": stats.mana.total,
            "%m": stats.current_mana.total,
            "%V": stats.moves.total,
            "%v": stats.current_moves.total,
            "%x": total_xp,
            "%X": xp_tnl,
            "%a": stats.alignment.total,
            "%q": stats.next_quest_time.total,
            "%Q": stats.quest_time.total,
            "%r": room.name,
            "%c": "\n",
            "%t": "12{Bam",
        }

        for key, value in values.items():
            output = output.replace(key, str(value))

        if output[-1] != "\n":
            output += " "
        output += "{x"

        return output

    def write_prompt(self):
        if self.state != "playing":
            return

        prompt_function = None
        for proxy_prompt in reversed(self.proxy_prompts):
            if proxy_prompt:
                prompt_function = proxy_prompt
                break

        if prompt_function:
            template = prompt_function(self)
        else:
            actor = self.actor

            targets = list(actor.targets)
            if targets:
                target = targets[0]

                current_hp = target.stats.current_hp.total
                total_hp = target.stats.hp.total
                health_text = "now considers you a force to be reckoned with"

                percent = (current_hp / total_hp) if total_hp else 0
                display_percent = "%0.1f" % (percent * 100)

                self.write("{{R{} {}. {{x[{{R{}%{{x]".format(
                    target.name, health_text, display_percent))

            self.writeln()

            template = (
                "{8[{R%h{8/{r%H{8h {B%m{8/{b%M{8m {M%v{8v {W%N{8({Y%X{8) "
                "{W%r{8({w%q{8/{w%t{8) {W%a{8]{x")

        self.write(self.format_prompt_template(template))

    @inject("Characters")
    def handle_playing_input(self, message, Characters, allow_proxy=True):
        actor = Characters.get(self.connection.actor_id)
        delay = None

        parts = message.split(" ") if message else []

        proxy_command = \
            self.proxy_commands[-1] if self.proxy_commands else None
        if proxy_command:
            context = self.proxy_contexts[-1]
            result = proxy_command(
                self=actor,
                message=message,
                args=list(parts),
                context=context,
            )
            if result is not False:
                return result

        name = parts[0].lower() if parts else ""
        args = list(parts[1:] if parts else [])

        # Detect and use an alias, if triggered
        aliases = actor.settings.get("aliases", {})
        alias = aliases.get(name, None)
        if alias:
            parts = alias.split(" ")
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

        elif message:
            self.writeln("Huh?")
        else:
            self.writeln()

        return delay


class TelnetConnection(Connection):
    def __init__(self, server, socket, address):
        super(TelnetConnection, self).__init__(server)
        self.read_buffer = ""
        self.write_buffer = ""
        self.socket = socket
        self.hostname = address[0]
        self.port = address[1]
        self.flush_thread = None

    @property
    def actor(self):
        client = self.client

        if not client:
            return None

        return client.actor

    def start(self):
        self.client = TelnetClient(self)
        gevent.spawn(self.read)

    def close(self):
        try:
            self.flush()
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
                self.read_buffer += raw.decode("utf-8").replace("\r\n", "\n")
            except Exception:
                pass

            if "\n" in self.read_buffer:
                split = self.read_buffer.split("\n")
                inputs = split[:-1]
                self.read_buffer = split[-1]

                self.client.handle_inputs(inputs)

    def write(self, message=""):
        if not self.socket:
            return

        message = message.replace("\n", "\r\n")
        self.write_buffer += message

        if not self.flush_thread:
            self.flush_thread = gevent.spawn(self.start_flush_thread)

    def start_flush_thread(self):
        gevent.sleep(0.05)
        self.flush()

    def flush(self):
        if not self.socket:
            return

        self.socket.send(self.write_buffer.encode())
        self.write_buffer = ""
        self.flush_thread = None


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
