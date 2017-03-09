"""
COMMAND RESOLVER

A dictionary-like object that indexes the key to help with command-resolution,
always returns a list, even if you don't put a list in, to help with secondary
resolution layers for finding matching command based on level/etc.

Example:
x = CommandResolver({
    "laugh": laugh_command,
    "look": look_command,
})

assert look_command is in x["l"]
assert laugh_command is in x["l"]

assert look_command is in x["lo"]
assert laugh_command is not in x["lo"]

assert look_command is not in x["la"]
assert laugh_command is in x["la"]
"""
class CommandResolver(object):
    def __init__(self, data):
        self.data = {}
        for key, value in data.items():
            self.add(key, value)

    def get(self, key, default=None):
        return self.data.get(key, [])

    def __getitem__(self, key):
        return self.data.get(key, [])

    def _get_subkeys(self, key):
        for x in range(len(key)):
            yield key[:x]

    def add(self, key, value):
        for subkey in self._get_subkeys(key):
            results = self.data.get(subkey, [])
            results.append(value)
            self.data[subkey] = results

    def __setitem__(self, key, value):
        self.add(key, value)

    def remove(self, key, value):
        for subkey in self._get_subkeys(key):
            results = self.data.get(subkey, [])

            if value in results:
                results.remove(value)

            if results:
                self.data[subkey] = results
            else:
                del self.data[subkey]
