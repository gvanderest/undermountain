class Entity(object):
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary.")
        self._data = data

    def __getattr__(self, key):
        if key.startswith("_"):
            try:
                return super(Entity, self).__getattribute__(key)
            except AttributeError:
                return None
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

    def __to_dict__(self):
        return dict(self._data)

    def __from_dict__(self, data):
        self._data = dict(data)

    def get(self, *args, **kwargs):
        return self._data.get(*args, **kwargs)
