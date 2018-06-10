class FuzzyResolver(object):
    def __init__(self, mapping=None):
        self.commands = {}
        if not mapping:
            mapping = {}

        for key, entry in mapping.items():
            self.add(key, entry)

    def _query_partial_names(self, name):
        """Generate the names that make up the parts of the name."""
        name = name.lower()
        partial = ""
        for char in name:
            partial += char
            yield partial

    def add(self, name, entry):
        """Add something to the Resolver by name to match entries.
        :rtype:
        """
        for partial in self._query_partial_names(name):

            if partial not in self.commands:
                self.commands[partial] = []

            self.commands[partial].append((name, entry))

    # def remove(self, name, entry):
    #     """Remove something from the Resolved by name."""
    #     for partial in self._query_partial_names(name):
    #         commands = self.commands[partial]

    #         commands.remove(entry)

    #         if not commands[partial]:
    #             del commands[partial]

    def query(self, name):
        """Return the list of entries matching a name."""
        name = name.lower()
        for entry in self.commands.get(name, []):
            yield entry

    def get(self, name):
        """Return the first match for a name."""
        name = name.lower()
        for entry in self.query(name):
            return entry
