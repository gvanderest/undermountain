class Unblockable(Exception):
    pass


class Event(object):

    def __init__(self, source, type_name, data=None, unblockable=False):
        if data is None:
            data = {}

        self.source = source
        self.type = type_name
        self.data = data
        self.unblockable = unblockable
        self.blocked = False

    def block(self):
        if self.unblockable:
            raise Unblockable(
                "Event of type '{}' is unblockable.".format(self.type)
            )
        self.blocked = True
        return self
