from mud.game_component import GameComponent
from mud.event import Event

import gevent


class Manager(GameComponent):
    DESCRIPTION = ""

    def start(self):
        """"Execute commands when Game starts."""
        pass

    def stop(self):
        """"Execute commands when Game stops."""
        pass

    def trigger(self, type, data=None, unblockable=False):
        event = self.generate_event(type, data, unblockable=unblockable)
        if unblockable:
            gevent.spawn(self.broadcast_event, event)
            return event
        else:
            return self.broadcast_event(event)

    def generate_event(self, type, data=None, unblockable=False):
        return Event(self, type, data, unblockable=unblockable)

    def broadcast_event(self, event):
        self.game.broadcast_event(event)
