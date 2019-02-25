from mud import entity
from mud.utils import hash


ID_FIELD_NAME = "id"

SPEC_MATCH_FUNCTION = {
    "startswith": lambda record_value, spec_value: record_value.startswith(spec_value),
    "endswith": lambda record_value, spec_value: record_value.endswith(spec_value),

    "istartswith": lambda record_value, spec_value: record_value.lower().startswith(spec_value.lower()),
    "iendswith": lambda record_value, spec_value: record_value.lower().endswith(spec_value.lower()),

    "gt": lambda record_value, spec_value: record_value > spec_value,
    "gte": lambda record_value, spec_value: record_value >= spec_value,

    "lt": lambda record_value, spec_value: record_value < spec_value,
    "lte": lambda record_value, spec_value: record_value <= spec_value,

    "eq": lambda record_value, spec_value: record_value == spec_value,
    "neq": lambda record_value, spec_value: record_value != spec_value,

    "in": lambda record_value, spec_value: spec_value.includes(record_value),
    "nin": lambda record_value, spec_value: not spec_value.includes(record_value),
}

class Collection(object):
    ENTITY_CLASS = None

    def __init__(self, records=None):
        if records is None:
            records = {}
        self.records = records

    @classmethod
    def record_matches_spec(cls, record, spec):
        """Return True if a record matches the requested spec."""
        if not spec:
            return True

        for (field, value) in spec.items():
            parts = field.split("__")

            field_name = parts.pop(0)
            func_name = parts.pop(0) if parts else "eq"

            value = record.get(field_name, None)

            func = SPEC_MATCH_FUNCTION.get(func_name)

            if not func:
                raise ValueError(f"Comparison function of '{func_name}' is not valid.")

            if not func(value, spec[field]):
                return False

        return True

    def query(self, spec=None):
        for record in self.records.values():
            if self.record_matches_spec(record, spec):
                yield self.wrap(record)

    def find(self, spec=None):
        for record in self.query(spec):
            return record

    def get(self, identifier):
        record = self.records.get(identifier)
        return self.wrap(record)

    def wrap(self, record):
        if self.ENTITY_CLASS:
            record = self.ENTITY_CLASS(record)
        return record

    def unwrap(self, record):
        return record if isinstance(record, dict) else record.data

    def save(self, record):
        data = self.unwrap(record)

        if not ID_FIELD_NAME in data:
            data[ID_FIELD_NAME] = hash.get_random_hash()

        self.records[data[ID_FIELD_NAME]] = data

        return self.wrap(data)
