import gevent


class Connection(object):
    CLIENT_CLASS = None

    def __init__(self, server):
        self.server = server
        self.client = self.CLIENT_CLASS(self)
        self.init()

    def init(self):
        pass

    def start(self):
        self.server.add_connection(self)
        self.client.init()

        while True:
            content = self.read()

            if content is None:
                break

            self.client.handle_input(content)
            gevent.sleep()

        self.close()
        self.server.remove_connection(self)

    def read(self):
        return ""

    def write(self, message):
        pass

    def writeln(self, message):
        self.write(message + "\n")

    def get_game(self):
        return self.server.get_game()

    def get_actor(self):
        return self.client.get_actor()
