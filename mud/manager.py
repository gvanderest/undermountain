"""
MODULE
"""
from mud.injector import Injector


class Manager(Injector):
    """A handler of Events."""
    HANDLE_EVENTS = []

    def handle_event(self, event):
        return event
