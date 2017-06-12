"""
EVENT
A method for passing around Events and their data.
"""


class Unblockable(Exception):
    """Exception to raise if an unblockable Event attempts blocking."""
    pass


class Event(object):
    """An Event which can occur, and sometimes can be blocked."""
    def __init__(self, type, data=None, blockable=False):
        if data is None:
            data = {}

        self.type = type
        self.data = data
        self.blocked = False
        self.blockable = blockable

    def is_blockable(self):
        return self.blockable

    def is_blocked(self):
        return self.blocked

    def block(self):
        if not self.blockable:
            raise Unblockable("The event is unblockable.")
        self.blocked = True
