from mud.injector import Injector
from mud.event import Event
from mud.inject import inject
from utils.hash import get_random_hash

import glob
import json
import logging
import os
import settings


class CollectionStorage(object):
    def __init__(self, collection):
        self.collection = collection

    def post_save(self, record):
        pass

    def post_delete(self, record):
        pass


class MemoryStorage(CollectionStorage):
    pass


class FileStorage(CollectionStorage):
    def __init__(self, *args, **kwargs):
        super(FileStorage, self).__init__(*args, **kwargs)
        name = self.collection.__class__.__name__.lower()
        self.folder = "{}/{}".format(settings.DATA_FOLDER, name)

        self.load_initial_data()

    def load_initial_data(self):
        pattern = "{}/*".format(self.folder)
        for path in glob.glob(pattern):
            with open(path, "r") as fh:
                try:
                    data = json.loads(fh.read())
                    self.collection.save(data, skip_storage=True)
                    self.collection.hydrate(data)

                except Exception as e:
                    self.collection.game.handle_exception(e)
                    logging.error("Unable to parse file: {}".format(path))

    def get_record_path(self, record):
        filename = record[self.collection.STORAGE_FILENAME_FIELD]
        format_name = self.collection.STORAGE_FORMAT

        suffix = self.collection.STORAGE_FILENAME_SUFFIX
        if suffix != "":
            if suffix is None:
                suffix = format_name
            suffix = "." + suffix

        return "{}/{}{}".format(
            self.folder,
            filename,
            suffix)

    def post_save(self, record):
        path = self.get_record_path(record)
        folders = path.split("/")
        folder = "/".join(folders[:-1])

        os.makedirs(folder, exist_ok=True)

        with open(path, "w") as fh:
            fh.write(json.dumps(record, indent=4, sort_keys=True))

    def post_delete(self, record):
        path = self.get_record_path(record)
        os.remove(path)


class Entity(object):
    DEFAULT_DATA = {}

    # FIXME Move this out of Collection, which is meant to be more generic
    @inject("Subroutines", "Behaviors")
    def handle_event(self, event, Subroutines, Behaviors):
        if self == event.source:
            return event

        # TODO HAVE COLLECTION CREATE DEEPCOPIES OF EVERYTHING
        handlers = list(self.event_handlers or [])

        for behavior_vnum in (self.behaviors or []):
            behavior = Behaviors.get({"vnum": behavior_vnum})
            handlers.append({
                "type": behavior.type,
                "subroutine_vnum": behavior.subroutine_vnum,
            })

        if handlers:
            for entry in handlers:
                if entry["type"] != event.type:
                    continue

                subroutine = \
                    Subroutines.get({"vnum": entry["subroutine_vnum"]})
                subroutine.execute(self, event)

        return event

    def generate_event(self, type, data=None, unblockable=False):
        return Event(self, type, data, unblockable=unblockable)

    def __eq__(self, other):
        return other.id == self.id

    def __neq__(self, other):
        return not self.__eq__(other)

    def __init__(self, data=None, collection=None):
        merged_data = dict(self.DEFAULT_DATA)
        if data:
            merged_data.update(data)
        data = merged_data

        super(Entity, self).__setattr__("_data", data)
        super(Entity, self).__setattr__("_collection", collection)

    @property
    def game(self):
        return self._collection.game

    @property
    def collection(self):
        return self._collection

    def __setattr__(self, name, value):
        return self.set(name, value)

    def __getattr__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, default=None):
        return self._data.get(name, None)

    def set(self, name, value):
        self._data[name] = value

    def set_data(self, data):
        super(Entity, self).__setattr__("_data", data)

    def get_data(self):
        return self._data

    def save(self):
        return self._collection.save(self)


class Collection(Injector):
    PERSISTENT = False
    ENTITY_CLASS = Entity
    STORAGE_CLASS = MemoryStorage
    STORAGE_FORMAT = "json"
    STORAGE_FILENAME_FIELD = "vnum"
    STORAGE_FILENAME_SUFFIX = None
    DATA_NAME = None

    def __init__(self, game):
        super(Collection, self).__init__(game)
        name = self.DATA_NAME or self.__class__.__name__
        self.game.data[name] = {}
        self.storage = self.STORAGE_CLASS(self)

    @property
    def data(self):
        name = self.DATA_NAME or self.__class__.__name__
        return self.game.data[name]

    @data.setter
    def data(self, data):
        name = self.DATA_NAME or self.__class__.__name__
        self.game.data[name] = data

    def query(self, spec=None, as_dict=False):
        def _filter_function(record):
            if spec is None:
                return True
            else:
                for key in spec:
                    if key not in record or spec[key] != record[key]:
                        return False
                return True

        filtered = filter(_filter_function, self.data.values())
        for record in list(filtered):
            if as_dict:
                yield dict(record)
            else:
                yield self.wrap_record(record)

    def get(self, spec):
        if isinstance(spec, str):
            record = self.data.get(spec, None)
            if not record:
                return None
            return self.wrap_record(record)
        else:
            for record in self.query(spec):
                return record

    def save(self, record, skip_storage=False):
        record = self.unwrap_record(record)

        if "id" not in record:
            record["id"] = get_random_hash()
        self.data[record["id"]] = record

        if not skip_storage:
            storage_record = self.dehydrate(record)
            self.storage.post_save(storage_record)

        return self.get(record["id"])

    def unwrap_record(self, record):
        if isinstance(record, Entity):
            return dict(record.get_data())
        return record

    def wrap_record(self, record):
        if isinstance(record, dict):
            return self.ENTITY_CLASS(data=dict(record), collection=self)
        return record

    def delete(self, record):
        record = self.unwrap_record(record)
        del self.data[record["id"]]
        self.storage.post_delete(record)
        self.post_delete(record)

    def post_delete(self):
        """Handle a record being removed from the Collection."""
        pass

    def dehydrate(self, record):
        """Prepare data for cold storage."""
        return record

    def hydrate(self, record):
        """Load data for Game usage."""
        return record
