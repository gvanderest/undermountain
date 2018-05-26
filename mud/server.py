from mud.game_component import GameComponent


class Server(GameComponent):

    def __init__(self, game):
        super(Server, self).__init__(game)
        self.connections = {}

    def start(self):
        """Execute commands when Server starts."""
        pass

    def stop(self):
        """Execute commands when Server stops."""
        pass

    def add_connection(self, connection):
        self.connections[connection.id] = connection
        self.game.connections[connection.id] = connection

    def remove_connection(self, connection):
        if connection.id in self.game.connections:
            del self.game.connections[connection.id]

        if connection.id in self.connections:
            del self.connections[connection.id]
