class Client(object):
    def __init__(self, connection):
        self.connection = connection
        self.write = connection.write
        self.writeln = connection.writeln
        self.state = "login_username"
        self.init()

    def init(self):
        pass

    def get_game(self):
        server = self.connection.server
        return server.game

    def handle_input(self, message):
        game = self.get_game()
        method_name = "handle_{}".format(self.state)

        method = getattr(self, method_name)
        game.inject(method, {"message": message})
