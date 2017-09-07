import gevent


class Server(object):
    def __init__(self, game):
        self.game = game
        self.connections = []
        self.init()

    def init(self):
        pass

    def add_connection(self, connection):
        self.connections.append(connection)
        self.game.add_connection(connection)

    def remove_connection(self, connection):
        self.game.remove_connection(connection)
        self.connections.remove(connection)

    def start(self):
        pass

    def stop(self):
        pass

    def tick(self):
        pass

    def accept_connections(self, sock):
        """Listen to the socket for connections and spawn them."""
        while True:
            conn = self.accept_connection(sock)
            gevent.spawn(self.handle_connection, conn)

    def handle_connection(self, conn):
        """Handle the new connection."""
        gevent.spawn(conn.start)

    def get_game(self):
        return self.game
