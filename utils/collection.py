"""
COLLECTION
"""
from utils.entity import Entity
from utils.hash import get_random_hash


class RequiredField(Exception):
    """Exception for when a required field is not provided."""
    pass


class UniqueCollision(Exception):
    """Exception for when a unique field has a collision."""


class UnindexedField(Exception):
    """Exception for when a spec is provided that uses an unindexed field."""


class Index(object):
    def __init__(self, field, required=False, unique=False):
        self.field = field
        self.required = required
        self.unique = unique

    def check_required(self, id, record):
        if self.required and self.field not in record:
            raise RequiredField("Field '{}' is required for record '{}'"
                                .format(self.field, id))

    def index(self, indexes, id, record):
        self.check_required(id, record)
        index = indexes.get(self.field, {})
        value = record.get(self.field)

        if value is None:
            return indexes

        values = value if isinstance(value, list) else [value]
        for value in values:
            value_ids = index.get(value, [])

            if self.unique and value_ids:
                raise UniqueCollision("Field '{}' value '{}' for record '{}'"
                                      .format(self.field, value, id))

            if id not in value_ids:
                value_ids.append(id)

            index[value] = value_ids

        indexes[self.field] = index

        return indexes

    def deindex(self, indexes, id, record):
        self.check_required(id, record)

        index = indexes.get(self.field, {})
        value = record.get(self.field)

        if value is None:
            return indexes

        values = value if isinstance(value, list) else [value]

        for value in values:
            value_ids = index.get(value, [])

            if id in value_ids:
                value_ids.remove(id)

            index[value] = value_ids

        indexes[self.field] = index

        return indexes

    def query(self, indexes, spec):
        index = indexes.get(self.field, {})
        value = spec[self.field]
        if value in index:
            ids = index[value]
            for id in ids:
                yield id

    def spec_matches(self, spec):
        for field in spec:
            if self.spec_field_matches(field):
                return True
        return False

    def spec_field_matches(self, field):
        return self.field == field


class Collection(object):
    NAME = None

    PRIMARY_KEY_FIELD = "id"
    INDEXES = []

    def __init__(self, records=None):
        self.records = records
        if self.records is None:
            self.records = {}

        self.indexes = {}

        for key, record in self.records.items():
            if self.PRIMARY_KEY_FIELD not in record:
                record[self.PRIMARY_KEY_FIELD] = key
            self.index(record)

    def wrap_record(self, record):
        """Wrap the Record in some fashion."""
        return record

    def get(self, id, skip_wrap=False):
        """Get a specific record by its ID as a dictionary."""
        record = self.records.get(id, None)

        # Not found
        if record is None:
            return None

        record = dict(record)

        if skip_wrap:
            return record

        return self.wrap(record)

    def find(self, spec=None):
        """Find a Record with a specification."""
        if spec is None:
            return None

        if isinstance(spec, str):
            return self.get(spec)

        for record in self.query(spec=spec, limit=1):
            return record

        return None

    def query(self, spec=None, limit=None):
        """Generate a list of Records with a specification."""
        ids = None

        # No filter provided
        if spec is None:
            for id in self.records.keys():
                yield self.get(id)
            raise StopIteration()

        for field in spec:
            matched = False
            for indexer in self.INDEXES:
                if indexer.spec_field_matches(field):
                    matched = True
                    break
            if not matched:
                raise UnindexedField("Field '{}' must be indexed"
                                     .format(field))

        # TODO Make this faster, as it's iterating too much
        for indexer in self.INDEXES:
            if not indexer.spec_matches(spec):
                continue

            next_ids = set(indexer.query(self.indexes, spec)) or set()
            if ids is None:
                ids = next_ids
            else:
                ids &= next_ids

            if len(ids) == 0:
                break

        for id in ids:
            yield self.get(id)

    def generate_hash(self):
        """Generate a unique random hash identifier."""
        return get_random_hash()

    def hydrate_primary_key(self, record):
        primary_key = record.get(self.PRIMARY_KEY_FIELD)
        if primary_key is None:
            primary_key = self.generate_hash()
            record[self.PRIMARY_KEY_FIELD] = primary_key
        return record, primary_key

    def save(self, record):
        """Save the record to the Collection."""
        if hasattr(record, "__to_dict__"):
            record = record.__to_dict__()
        else:
            record = dict(record)

        record, primary_key = self.hydrate_primary_key(record)

        # TODO Handle diffing the content and only deindexing/reindexing fields
        # that have actually changed.
        previous_record = self.get(primary_key, skip_wrap=True)
        if previous_record:
            self.deindex(previous_record)

        self.records[primary_key] = record
        self.index(record)

        return self.wrap_record(record)

    def remove(self, record):
        """Remove the record from the Collection."""
        if hasattr(record, "__to_dict__"):
            record = record.__to_dict__()
        record = dict(record)

        id = record[self.PRIMARY_KEY_FIELD]
        del self.records[id]

        self.deindex(record)

    def deindex(self, record):
        """Remove the Record from the indexes."""
        # TODO Only deindex for diffs
        for indexer in self.INDEXES:
            record, primary_key = self.hydrate_primary_key(record)
            self.indexes = indexer.deindex(self.indexes, primary_key, record)

    def index(self, record):
        """Add the Record to the indexes for fast lookup."""
        # TODO Only index for diffs
        for indexer in self.INDEXES:
            record, primary_key = self.hydrate_primary_key(record)
            self.indexes = indexer.index(self.indexes, primary_key, record)

    def wrap(self, record):
        """Wrap the Record in its."""
        return self.WRAPPER_CLASS(record, self)


class EntityCollection(Collection):
    WRAPPER_CLASS = None

    def wrap_record(self, record):
        """Return a Record with a link back to the Collection."""
        return self.WRAPPER_CLASS(record, self)


class GameCollection(EntityCollection):
    def __init__(self, game):
        self.game = game

        state = self.game.get_state()
        records = state.get(self.NAME, {})
        state[self.NAME] = records
        self.game.set_state(state)

        super(GameCollection, self).__init__(records)


class CollectionEntity(Entity):
    def __init__(self, data, collection=None):
        super(CollectionEntity, self).__init__(data)
        self._collection = collection

    def get_injector(self, *args, **kwargs):
        return self._collection.game.get_injector(*args, **kwargs)

    def get_injectors(self, *args, **kwargs):
        return self._collection.game.get_injectors(*args, **kwargs)

    def save(self):
        """Save the Entity to the Collection."""
        self._collection.save(self._data)

    def remove(self):
        """Remove the Entity from the Collection."""
        self._collection.remove(self._data)

    def __eq__(self, other):
        if self.id is None or other.id is None:
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)
