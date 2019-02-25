from mud import manager


class Client(manager.Manager):
    INITIAL_STATE = "login_username"

    def __init__(self, server):
        super().__init__(server.game)

        self.server = server
        self.state = self.INITIAL_STATE
        self.allow_echo = True

    def stop_echo(self):
        self.allow_echo = False

    def start_echo(self):
        self.allow_echo = True

    async def start(self):
        await super().start()

        while self.running:
            line = await self.readline()

            if line is None:
                self.stop()
                break

            await self.handle_input(line)

    async def handle_input(self, line):
        if not self.allow_echo and line.strip():
            self.start_echo()

        method_name = f"handle_{self.state}_input"
        method = getattr(self, method_name)
        await method(line)

    def close(self):
        self.server.game.connections.remove(self)
