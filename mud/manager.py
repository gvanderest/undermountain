"""
MODULE
"""
from mud.injector import Injector


class Manager(Injector):
    """A handler of Events."""

    # The list of event types to allow to pass to handle_event, if None is set
    # then all events will filter through.
    HANDLE_EVENTS = None

    def handle_event(self, event):
        return event

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
