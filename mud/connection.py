class Connection(object):
    NEWLINE = "\r\n"
    CURRENT_ID = 0

    @classmethod
    def get_next_id(cls):
        cls.CURRENT_ID += 1
        return cls.CURRENT_ID

    def __init__(self, server):
        """Initialize Connection to Game and store its socket."""
        self.server = server
        self.id = Connection.get_next_id()
        self.actor_id = None

    @property
    def game(self):
        return self.server.game

    def start(self):
        """Execute commands for starting of Connection."""
        self.client.start()

    def close(self):
        """Execute commands to close the Connection."""
        pass

    def write(self, message=""):
        """Execute commands to send data over the socket."""
        pass

    def writeln(self, message=""):
        """Send data over the socket, with newline."""
        self.writeln(message + self.NEWLINE)

    def flush(self):
        """TODO: Confirm we need to handle this at all or if server will."""
        pass
