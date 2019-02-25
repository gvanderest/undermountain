from mud import module

class Server(module.Module):
    def __init__(self, game):
        super().__init__(game)

        self.connections = []

    async def handle_connection(self, reader, writer):
        """Instantiate a connection and attach a client."""
        client = self.generate_client(self, reader, writer)
        self.add_connection(client)
        await client.start()
        self.remove_connection(client)

    def add_connection(self, client):
        self.connections.append(client)
        self.game.connections.append(client)

    def remove_connection(self, client):
        self.connections.remove(client)
        self.game.connections.remove(client)
