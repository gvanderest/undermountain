import logging


class Unblockable(Exception):
    pass


class Event(object):
    def __init__(self, type, data=None, blockable=True):
        self.type = type
        self.data = data
        self.blockable = blockable
        self.blocked = False

    def block(self):
        if not self.blockable:
            raise Unblockable(f"Event '{self.type}' is not blockable.")

        logging.debug(f"Event '{self.type}' blocked.")

        self.blocked = True
