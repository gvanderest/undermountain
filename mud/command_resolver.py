class CommandResolver(object):
    def __init__(self, data=None):
        self.data = {}

        if data:
            for key, value in data.items():
                self.add(key, value)

    def _get_subkeys(self, key):
        key = key.lower()
        for x in range(len(key) + 1):
            yield key[:x]

    def add(self, key, value):
        for subkey in self._get_subkeys(key):
            if not subkey in self.data:
                self.data[subkey] = []
            self.data[subkey].append(value)

    def remove(self, key, value):
        for subkey in self._get_subkeys(key):
            if subkey in self.data:
                self.data[subkey].remove(value)

    def update(self, values):
        for key, value in values.items():
            self.add(key, value)

    def get(self, key):
        return self.data.get(key, [])
