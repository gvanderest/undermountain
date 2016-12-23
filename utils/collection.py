"""
COLLECTION
"""
from utils.hash import get_random_hash
from mud.injector import Injector


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
            if value not in index:
                index[value] = []

            if self.unique and len(index[value]) > 0:
                raise UniqueCollision("Field '{}' value '{}' for record '{}'"
                                      .format(self.field, value, id))

            index[value].append(id)

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
            ids = index[value]
            ids.remove(id)

            # Remove the key if there are no records, to reduce memory
            if not ids:
                del index[value]

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


# TODO Break this into being a GameCollection, which is an Injector, while
# being able to keep the Collection class pristine and untainted with Game-
# related logic.
class Collection(Injector):
    NAME = None
    WRAPPER_CLASS = None

    PRIMARY_KEY_FIELD = "id"
    INDEXES = []

    def __init__(self, *args, **kwargs):
        super(Collection, self).__init__(*args, **kwargs)

        state = self.game.get_state()
        self.records = state.get(self.NAME, {})
        state[self.NAME] = self.records
        self.game.set_state(state)

        self.indexes = {}

        for key, record in self.records.items():
            if self.PRIMARY_KEY_FIELD not in record:
                record[self.PRIMARY_KEY_FIELD] = key
            self.index(record)

    def get(self, id):
        """Get a specific record by its ID."""
        return self.records.get(id, None)

    def find(self, spec=None):
        """Find a Record with a specification."""
        if isinstance(spec, str):
            return self.get(spec)

        for record in self.query(spec=spec, limit=1):
            return record

    def query(self, spec=None, limit=None):
        """Generate a list of Records with a specification."""
        ids = None
        for field in spec:
            matched = False
            for indexer in self.INDEXES:
                if indexer.spec_field_matches(field):
                    matched = True
                    break
            if not matched:
                raise UnindexedField("Field '{}' must be indexed"
                                     .format(field))

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
            yield dict(self.get(id))

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
        if hasattr(record, "__dict__"):
            record = record.__dict__()
        record = dict(record)

        record, primary_key = self.hydrate_primary_key(record)

        # TODO Handle diffing the content and only deindexing/reindexing fields
        # that have actually changed.
        previous_record = self.get(primary_key)
        if previous_record:
            self.deindex(previous_record)

        self.records[primary_key] = record
        self.index(record)

    def remove(self, record):
        """Remove the record from the Collection."""
        if hasattr(record, "__dict__"):
            record = record.__dict__()
        record = dict(record)

        id = record[self.PRIMARY_KEY_FIELD]
        del self.records[id]

        self.index(record)

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
