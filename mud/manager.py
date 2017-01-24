"""
MODULE
"""
from mud.injector import Injector


class Manager(Injector):
    """A handler of Events."""

    # The list of event types to allow to pass to handle_event, if None is set
    # then all events will filter through.
    HANDLE_EVENTS = None
    # TICK_DELAY = 1.0  # TODO Number of seconds between tick() calls

    def handle_event(self, event):
        return event

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def tick(self):
        """Fired once per second for all timing."""
        pass
