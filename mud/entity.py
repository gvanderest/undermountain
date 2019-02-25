class Entity(object):
    def __init__(self, data=None):
        if data is None:
            data = {}
        super().__setattr__("data", data)

    def __eq__(self, other):
        if not other or other.id is None:
            return False
        return self.id == other.id

    def __neq__(self, other):
        return not self.__eq__(other)

    def __getattr__(self, name):
        return self.data.get(name)

    def __setattr__(self, name, value):
        self.data[name] = value

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        return self.__setattr__(name, value)
