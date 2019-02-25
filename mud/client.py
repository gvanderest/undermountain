from mud import manager


class Client(manager.Manager):
    INITIAL_STATE = "login_username"

    def __init__(self, server):
        super().__init__(server.game)

        self.server = server
        self.state = self.INITIAL_STATE

    async def start(self):
        await super().start()

        while self.running:
            line = await self.readline()

            if line is None:
                self.stop()
                break

            await self.handle_input(line)

    async def handle_input(self, line):
        method_name = f"handle_{self.state}_input"
        method = getattr(self, method_name)
        await method(line)

    def close(self):
        self.server.game.connections.remove(self)
