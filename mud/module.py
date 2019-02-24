class Module(object):
    def __init__(self, game):
        self.game = game
        self.bind = self.bind_event_handler
        self.unbind = self.unbind_event_handler
        self.add_module = self.game.add_module
        self.running = False

    def setup(self):
        pass

    def teardown(self):
        pass

    async def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def bind_event_handler(self, pattern, func):
        self.game.add_event_handler(pattern, func)

    def unbind_event_handler(self, pattern, func):
        self.game.remove_event_handler(pattern, func)

    def t(self, reference, **values):
        return self.game.translate(reference, **values)
