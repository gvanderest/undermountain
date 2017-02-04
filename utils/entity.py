class Entity(object):
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary.")
        self._data = data

    def __getattr__(self, key):
        if key.startswith("_"):
            return super(Entity, self).__getattr__(key, None)
        return self._data.get(key, None)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super(Entity, self).__setattr__(key, value)
        else:
            self._data[key] = value

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def get(self, *args, **kwargs):
        return self._data.get(*args, **kwargs)
