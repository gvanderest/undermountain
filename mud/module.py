class Module(object):
    def __init__(self, game):
        self.game = game
        self.bind = self.bind_event_handler
        self.unbind = self.unbind_event_handler
        self.register_module = self.game.register_module
        self.register_injector = self.game.register_injector
        self.register_entity = self.game.register_entity
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
        self.game.register_event_handler(pattern, func)

    def unbind_event_handler(self, pattern, func):
        self.game.remove_event_handler(pattern, func)

    def t(self, reference, **values):
        return self.game.translate(reference, **values)
