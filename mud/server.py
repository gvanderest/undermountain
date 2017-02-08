import logging
from mud.manager import Manager


class Server(Manager):
    def __init__(self, game):
        super(Server, self).__init__(game)

        self.connections = []

    def add_connection(self, connection):
        """Add the Connection to the list."""
        self.connections.append(connection)
        self.game.add_connection(connection)

    def remove_connection(self, connection):
        """Remove the Connection from the list."""
        self.game.remove_connection(connection)
        self.connections.remove(connection)

    def dehydrate(self):
        """Convert this into the dumbest data possible."""
        return {
            "connections": [conn.dehydrate() for conn in self.connections]
        }

    def get_game(self):
        return self.game

    def hydrate(self, payload):
        """Convert dumb information into better."""
        self.connections = [
            self.hydrate(conn) for conn
            in payload["connections"]
        ]

    def tick(self):
        from settings import DEBUG_CONNECTION_COUNTS
        if DEBUG_CONNECTION_COUNTS:
            logging.info("Number of {} connections: {}".format(
                self.__class__.__name__,
                len(self.connections))
            )
