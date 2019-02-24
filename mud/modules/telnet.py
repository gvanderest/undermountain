from mud import module, manager, server, client, settings

import asyncio

NEWLINE = "\n"
TELNET_HOST = settings.get("TELNET_HOST", "0.0.0.0")
TELNET_NEWLINE = settings.get("TELNET_NEWLINE", "\r\n")
TELNET_ENCODING = settings.get("TELNET_ENCODING", "utf-8")


class Telnet(module.Module):
    def setup(self):
        self.add_module(self.TelnetServer)

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

        async def handle_connection(self, reader, writer):
            """Instantiate a connection and attach a client."""
            client = Telnet.TelnetClient(self, reader, writer)
            self.game.add_client(client)
            await client.start()

        def stop(self):
            """Close ports."""
            pass


    class TelnetClient(client.Client):
        DEFAULT_STATE = "login_username"

        def __init__(self, server, reader, writer):
            super().__init__(server.game)
            self.server = server
            self.reader = reader
            self.writer = writer

        async def start(self):
            self.start_login_username()
            await super().start()

        def write(self, message):
            self.writer.write(message.replace(NEWLINE, TELNET_NEWLINE).encode(TELNET_ENCODING))

        def writeln(self, message):
            self.write(message + TELNET_NEWLINE)

        async def readline(self):
            raw_line = await self.reader.readline()
            return raw_line.decode(TELNET_ENCODING).strip()

        def start_login_username(self):
            self.state = "login_username"
            self.write("Username: ")

        async def handle_login_username_input(self, message):
            self.writeln("You wrote: " + message)
            self.start_login_password()

        def start_login_password(self):
            self.state = "login_password"
            self.write("Password: ")
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
