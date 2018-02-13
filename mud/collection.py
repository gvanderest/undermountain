from mud.injector import Injector
from mud.event import Event
from mud.inject import inject
from utils.hash import get_random_hash

import gevent
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
                    record = self.collection.save(data, skip_storage=True)
                    self.collection.hydrate(data)
                    logging.debug("Stored {}: {}".format(
                        self.collection.__class__.__name__, record.vnum))

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

        temp_path = path + ".TMP"

        with open(temp_path, "w") as fh:
            fh.write(json.dumps(record, indent=4, sort_keys=True))

        os.rename(temp_path, path)

    def post_delete(self, record):
        path = self.get_record_path(record)
        os.remove(path)


class Entity(object):
    DEFAULT_DATA = {
        "flags": [],
    }

    @property
    def children(self):
        return []

    @property
    def parents(self):
        return []

    def add_flag(self, flag):
        flags = self.flags or []
        if flag not in flags:
            flags.append(flag)
        self.flags = flags

    def remove_flag(self, flag):
        flags = self.flags or []
        if flag in flags:
            flags.remove(flag)
        self.flags = flags

    def toggle_flag(self, flag):
        flags = self.flags or []
        if flag in flags:
            flags.remove(flag)
        else:
            flags.append(flag)
        self.flags = flags

    def has_flag(self, flag):
        flags = self.flags or []
        return flag in flags

    def emit(self, type, data=None, unblockable=False):
        event = self.generate_event(type, data, unblockable=unblockable)
        if unblockable:
            gevent.spawn(self.emit_event, event)
            return event
        else:
            return self.emit_event(event)

    def trigger(self, type, data=None, unblockable=False):
        event = self.generate_event(type, data, unblockable=unblockable)
        level = self.room
        if unblockable:
            gevent.spawn(level.broadcast_event, event)
            return event
        else:
            return level.broadcast_event(event)

    def broadcast(self, type, data=None, unblockable=False):
        event = self.generate_event(type, data, unblockable=unblockable)
        if unblockable:
            gevent.spawn(self.broadcast_event, event)
            return event
        else:
            return self.broadcast_event(event)

    def broadcast_event(self, event):
        event = self.handle_event(event)

        if event.blocked:
            return event

        for child in self.children:
            event = child.broadcast_event(event)
            if event.blocked:
                return event

        return event

    def emit_event(self, event):
        event = self.handle_event(event)

        if event.blocked:
            return event

        for parent in self.parents:
            event = parent.emit_event(event)
            if event.blocked:
                return event

        return event

    # FIXME Move this out of Collection, which is meant to be more generic
    @inject("Scripts", "Behaviors")
    def handle_event(self, event, Scripts, Behaviors):
        # TODO HAVE COLLECTION CREATE DEEPCOPIES OF EVERYTHING
        triggers = list(self.triggers or [])

        for behavior_vnum in (self.behaviors or []):
            behavior = Behaviors.get({"vnum": behavior_vnum})
            triggers.append({
                "type": behavior.type,
                "script_vnum": behavior.script_vnum,
            })

        if triggers:
            for entry in triggers:
                if entry["type"] != event.type:
                    continue

                script = Scripts.get({"vnum": entry["script_vnum"]})
                script.execute(self, event)

        return event

    def generate_event(self, type, data=None, unblockable=False):
        return Event(self, type, data, unblockable=unblockable)

    def __eq__(self, other):
        if not other:
            return False
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

    def _get_property(self, name):
        prop_check = getattr(self.__class__, name, None)
        if isinstance(prop_check, property):
            return prop_check
        return None

    def __setattr__(self, name, value):
        return self.set(name, value)

    def __getattr__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        return self.set(name, value)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, default=None):
        prop = self._get_property(name)
        if prop:
            return prop.fget(self, default)
        else:
            return self._data.get(name, default)

    def set(self, name, value):
        prop = self._get_property(name)
        if prop:
            prop.fset(self, value)
        else:
            self._data[name] = value

    def set_data(self, data):
        super(Entity, self).__setattr__("_data", data)

    def get_data(self):
        return self._data

    def refresh(self):
        self.set_data(self._collection.data.get(self.id, {}))

    def save(self):
        return self._collection.save(self)

    def delete(self):
        return self._collection.delete(self)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self.set_data(data)


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

    def fuzzy_get(self, identifier):
        """Look up an Entity, using fuzzier logic."""
        cleaned = identifier.strip().lower()
        for entry in self.query():
            compare = entry.name.lower()
            if compare.startswith(cleaned):
                return entry

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
                yield record
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
        logging.debug("Saving {} record {}".format(
            self.__class__.__name__, record.get("vnum", None)))
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
            return record.get_data()
        return record

    def wrap_record(self, record):
        if isinstance(record, dict):
            return self.ENTITY_CLASS(data=record, collection=self)
        return record

    def delete(self, record):
        record = self.unwrap_record(record)
        del self.data[record["id"]]
        self.storage.post_delete(record)
        self.post_delete(record)

    def post_delete(self, record):
        """Handle a record being removed from the Collection."""
        pass

    def dehydrate(self, record):
        """Prepare data for cold storage."""
        return record

    def hydrate(self, record):
        """Load data for Game usage."""
        return record
