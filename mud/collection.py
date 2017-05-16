from utils.collection import EntityCollection, CollectionEntity
import logging
import json


class Collection(EntityCollection):
    def __init__(self, game):
        self.game = game

        state = self.game.get_state()
        records = state.get(self.NAME, {})
        state[self.NAME] = records
        self.game.set_state(state)
        logging.info("LOADED {} OBJECTS".format(len(records)))

        super(Collection, self).__init__(records)

    def wrap_record(self, record):
        wrapped = super(Collection, self).wrap_record(record)
        wrapped._game = self.game
        return wrapped

    def get_game(self):
        """Return the Game."""
        return self.game


class FileCollection(Collection):
    FILE_FORMAT = "json"

    def __init__(self, game):
        super(FileCollection, self).__init__(game)
        logging.info('FILE COLLECTION BOYEE')

    def get_record_filename(self, record):
        """Return the filename that represents a record."""
        return record["id"] + self.FILE_FORMAT

    def dehydrate(self, record):
        """Return a dehydrated version of the record for serializing."""
        return record

    def serialize(self, record):
        """Return a serialized version of the record."""
        return json.dumps(record)

    def deserialize(self, contents):
        """Return a dictionary from a serialized version."""
        return json.loads(contents)

    def hydrate(self, record):
        """Return a hydrated version of the record after deserializing."""
        return record


class Entity(CollectionEntity):
    def get_game(self):
        """Return the Game."""
        return self._game
