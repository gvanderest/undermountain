import gevent


class Manager(object):
    EVENTS = []

    def handle(self, event):
        pass

    def __init__(self, game):
        self.running = False
        self.game = game
        self.init()

    def init(self):
        pass

    def start(self):
        self.running = True

    def sleep(self, seconds=0.0):
        gevent.sleep(seconds)
