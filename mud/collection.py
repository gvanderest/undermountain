from utils.collection import EntityCollection, CollectionEntity
import logging
import json
from glob import glob


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
    FILENAME_FIELD = "id"

    def __init__(self, game):
        super(FileCollection, self).__init__(game)
        self.load_from_files()

    def load_from_files(self):
        """Go to the data directory and load the files available."""
        print("LOADING FROM FILES")
        for file_path in self.query_files_list():
            filename = file_path.split("/")[-1]
            with open(file_path, "r") as fh:
                contents = fh.read()
                self.ingest_contents(contents, filename)

    def ingest_contents(self, contents, name):
        """Process the contents of a file into the Collection."""
        record = self.deserialize(contents)
        hydrated = self.hydrate(record)
        self.save(hydrated)

    def query_files_list(self):
        """Yield the paths to the file documents."""
        data_path = "{}/{}/*.{}".format(
            self.game.get_data_path(),
            self.NAME,
            self.FILE_FORMAT)

        for path in glob(data_path):
            yield path

    def get_record_filename(self, record):
        """Return the filename that represents a record."""
        return record[self.FILENAME_FIELD] + self.FILE_FORMAT

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
