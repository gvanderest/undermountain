from mud import module, manager, server, client, settings, inject
import traceback
from mud.utils import ansi

import asyncio
import re

NEWLINE = "\n"
TELNET_HOST = settings.get("TELNET_HOST", "0.0.0.0")
TELNET_NEWLINE = settings.get("TELNET_NEWLINE", "\r\n")
TELNET_ENCODING = settings.get("TELNET_ENCODING", "utf-8")

IAC_WILL_ECHO = b"\xff\xfb\x01"
IAC_WONT_ECHO = b"\xff\xfc\x01"

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


class Telnet(module.Module):
    def setup(self):
        self.register_module(self.TelnetServer)

    class TelnetServer(server.Server):
        def __init__(self, game):
            super().__init__(game)

            self.servers = []

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

            (host, port) = self.writer.get_extra_info("peername")
            self.host = host
            self.port = port

        def stop_echo(self):
            super().stop_echo()
            self.write(IAC_WILL_ECHO)

        def start_echo(self):
            super().start_echo()
            self.write(IAC_WONT_ECHO)

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
                if isinstance(message, bytes):
                    self.writer.write(message)
                else:
                    cleaned = message.replace(NEWLINE, TELNET_NEWLINE)
                    colorized = ansi.colorize(cleaned)
                    encoded = colorized.encode(TELNET_ENCODING)
                    self.writer.write(encoded)
            except Exception as e:
                self.game.handle_exception(e)
                self.close()

        def writeln(self, message=""):
            """Write to the writer, with a newline on the end."""
            self.write(message + TELNET_NEWLINE)

        async def readline(self):
            """Read a line from the reader."""
            raw_line = await self.reader.readline()
            if not raw_line:
                return None
            return raw_line.decode(encoding=TELNET_ENCODING, errors="ignore").strip()

        def start_login_username(self):
            """Display login username prompt."""
            self.state = "login_username"
            self.write("What is your character name or email address? ")

        @inject("Characters")
        async def handle_login_username_input(self, message, Characters):
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
                actor = Characters.save({"name": message})
                actor.set_client(self)
                self.actor = actor

                self.start_login_password()
            else:
                self.write("Your name is invalid, please provide a valid name or email? ")

        def start_account_menu(self):
            self.writeln(f"""\
Account Menu

Email Address: {self.email}
""")

            for x in range(1, 4):
                self.writeln(f"({x}) 101 Human Mer | Character     | Westbridge")

            self.writeln("""
(N) Create a new character
(E) Change email address
(P) Change password""")

            self.state = "account_menu"

        async def handle_account_menu_input(self, message):
            if message == "n":
                self.start_new_character_name()
            else:
                self.writeln("Not yet supported.")

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
            self.stop_echo()
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
            await self.start_playing()

        async def start_playing(self):
            self.writeln("Fading into the world..")
            self.state = "playing"
            await self.actor.force("look")

        async def handle_playing_input(self, message):
            await self.actor.handle_input(message)
