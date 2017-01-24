def listify(items=None):
    """Return the items provided as a list.  If None, empty list."""
    if items is None:
        return []

    if isinstance(items, (list, set, tuple)):
        return list(items)

    return [items]
