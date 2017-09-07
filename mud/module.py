import gevent


class Module(object):
    def __init__(self, game):
        self.game = game
        self.init()

    def init(self):
        pass


class Manager(object):
    EVENTS = tuple()

    def __init__(self, game):
        self.running = False
        self.game = game
        self.init()

    def init(self):
        """Steps to perform once created."""
        pass

    def start(self):
        self.running = True

    def sleep(self, seconds=0.0):
        gevent.sleep(seconds)

    def handle(self, event):
        pass
