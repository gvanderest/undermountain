from mud import module, manager, server, client, settings
from mud.utils import ansi

import asyncio
import re

NEWLINE = "\n"
TELNET_HOST = settings.get("TELNET_HOST", "0.0.0.0")
TELNET_NEWLINE = settings.get("TELNET_NEWLINE", "\r\n")
TELNET_ENCODING = settings.get("TELNET_ENCODING", "utf-8")

def is_valid_email(value):
    return re.match(r"[\w\.\+]+\@(\w+\.)+\w+", value)

ILLEGAL_NAME_PREFIXES = [
    "self",
]
BAD_WORDS = [
    "fuck",
]

def is_valid_username(value):
    # TODO: Check for bad words
    # TODO: Check for illegal name prefixes
    return re.match(r"[A-Z][a-z]+", value) and len(value) > 5

                # TODO: Move this to Core module

# TODO: Move to Core
async def quit_command(self, **kwargs):
    self.echo("""\
{RYou feel a hand grab you, you begin to fly upwards!
{BYou pass through the clouds and out of the world!
{GYou have rejoined Reality!

{WFor {RNews{W, {CRoleplaying{W and {MInfo{W, Visit our website!
{Ch{cttp://{Cw{cww.{Cw{caterdeep.{Co{crg{x""")
    self.quit()

async def tell_command(self, keyword, args, **kwargs):
    # TODO: Convert to using params
    # TODO: Convert to find Actors using clean method
    # TODO: Fuzzy search
    name = args.pop(0)

    found = None
    for conn in self.client.server.game.connections:
        if conn.actor.name.lower() == name.lower():
            found = conn.actor
            break

    if not found:
        self.echo("They couldn't be found.")
    else:
        message = " ".join(args)
        self.echo(f"{{gYou tell {found.name} '{{G{message}{{g'{{x")
        if found != self:
            found.echo(f"{{g{self.name} tells you '{{G{message}{{g'{{x")


async def who_command(self, **kwargs):
    # TODO: Add functionality to use filters
    # TODO: Cleanly request online Characters
    count = 0
    self.echo("""\
               {GThe Visible Mortals and Immortals of Waterdeep
{g-----------------------------------------------------------------------------{x""")

    self.echo("""\
IMP Creator of Worlds [...PM....B] Kelemvor Lord of Death [Software Development]
IMP M Death Act Doom  [...P.R....] Jergal the Supreme Deity [Scrivener of Doom]
CRE M Dragn God       [WI.NMR....] Bahamut, God of Dragons. [The Platinum Dragon]
DEI N Coded Bot Helpr [...NMR....] Ubtao 'tell ubtao help' [BOT]
GOD M Human Brd       [...N.R....] Finder, Community Manager [Nameless Bard]
HRO M Elf   Mer BlkCh   [.N.R...B] Brayden the Silent Crew
HRO F Thken Prs         [.N......] Chezo The Useless Priest..... ha ha hardy har har
HRO M Elf   Prs Order   [.P.R....] Heil the Rebuildable Atomizer""")
    self.echo()
    self.echo(f"{{GPlayers found{{g: {{w{count}   {{GTotal online{{g: {{W{count}   {{GMost on today{{g: {{w{count}{{x")


# TODO: Move this to Core
class Character(object):
    def __init__(self, data=None):
        if data is None:
            data = {}

        super().__setattr__("_data", data)

        self.client = None
        # TODO: Improve this logic to take into account classes, skills, level, etc.
        self.command_handlers = {
            "who": who_command,
            "tell": tell_command,
            "quit": quit_command,
        }

    def __getattr__(self, name):
        return self._data.get(name)

    def set_client(self, client):
        self.client = client

    def quit(self):
        self.client.close()

    def echo(self, message=""):
        self.client.writeln(message)

    async def handle_input(self, line):
        words = line.split(" ")
        keyword = words[0] if words else ""

        func = self.command_handlers.get(keyword)

        args = words[1:] if words else []
        remainder = " ".join(args)

        params = [] # TODO: Parse indexes, counts, keywords, etc.

        if not func:
            self.echo("Huh?")
        else:
            await func(
                self,
                line=line,

                keyword=keyword,
                remainder=remainder,

                words=words,

                args=args,
                params=params,
            )


class Telnet(module.Module):
    def setup(self):
        self.add_module(self.TelnetServer)

    class TelnetServer(server.Server):
        def __init__(self, game):
            super().__init__(game)

            self.servers = []

        async def handle_connection(self, reader, writer):
            """Instantiate a connection and attach a client."""
            client = self.generate_client(self, reader, writer)
            self.game.connections.append(client)
            await client.start()

        async def start(self):
            """Open ports."""
            for port in settings.get("TELNET_PORTS", ()):
                server = await asyncio.start_server(
                    client_connected_cb=self.handle_connection,
                    host=TELNET_HOST,
                    port=port,
                )

        def generate_client(self, server, reader, writer):
            return Telnet.TelnetClient(server, reader, writer)

        def stop(self):
            """Close ports."""
            pass


    class TelnetClient(client.Client):
        DEFAULT_STATE = "login_username"

        def __init__(self, server, reader, writer):
            super().__init__(server)

            self.reader = reader
            self.writer = writer

            self.username = None
            self.email = None
            self.account = None

            self.actor = None

        async def start(self):
            """Start with a login prompt."""
            self.start_login_username()
            await super().start()

        def close(self):
            self.writer.close()

        def write(self, message=""):
            """Write to the writer."""
            # TODO: Disable colors if player has setting
            try:
                cleaned = message.replace(NEWLINE, TELNET_NEWLINE)
                colorized = ansi.colorize(cleaned)
                encoded = colorized.encode(TELNET_ENCODING)
                self.writer.write(encoded)
            except Exception:
                self.close()

        def writeln(self, message=""):
            """Write to the writer, with a newline on the end."""
            self.write(message + TELNET_NEWLINE)

        async def readline(self):
            """Read a line from the reader."""
            raw_line = await self.reader.readline()
            if not raw_line:
                return None
            return raw_line.decode(TELNET_ENCODING).strip()

        def start_login_username(self):
            """Display login username prompt."""
            self.state = "login_username"
            self.write("What is your character name or email address? ")

        async def handle_login_username_input(self, message):
            # TODO: Search for a pfile for this username
            # TODO: Search for an account with this email address
            # TODO: If one found, hold it temporarily in memory and prompt for password
            # TODO: If none found, go start creating one

            if is_valid_email(message):
                self.writeln("Cool, you used a valid email addess! But they're not yet supported!")
                self.username = message.lower()
                self.start_account_menu()
                return

            if is_valid_username(message):
                self.writeln("You wrote: " + message)

                # TODO: Only fetch information to check account exists
                actor = Character({"name": message})
                actor.set_client(self)
                self.actor = actor

                self.start_login_password()
            else:
                self.write("Your name is invalid, please provide a valid name or email? ")

        def start_account_menu(self):
            self.writeln(f"""\
Account Menu

Email Address: {self.email}

(N) Create a new character
(E) Change email address
(P) Change password""")

            self.state = "account_menu"

        async def handle_account_menu_input(self, message):
            if message == "n":
                self.start_new_character_name()

        def start_new_character_name(self):
            self.writeln("Creating a new character.")
            self.write("What is their name? ")
            self.state = "new_character_name"

        async def handle_new_character_name_input(self, message):
            # TODO: Validate name
            self.username = message
            self.writeln(f"Your name is {self.username}")

            self.actor = Character({"name": self.username})
            self.actor.set_client(self)

            self.start_login_password()

        def start_login_password(self):
            self.write("Password: ")
            self.state = "login_password"
            # TODO: Load Character here and attach
            # TODO: Prevent echo and logging

        async def handle_login_password_input(self, message):
            self.writeln("You wrote: " + message)
            self.start_motd()

        def start_motd(self):
            self.writeln("Message of the day goes here.")
            self.state = "motd"

        async def handle_motd_input(self, message):
            self.start_playing()

        def start_playing(self):
            self.writeln("Fading into the world..")
            self.state = "playing"

        async def handle_playing_input(self, message):
            self.writeln("You typed the following: " + message)

            await self.actor.handle_input(message)
