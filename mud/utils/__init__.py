def listify(items):
    if items is None:
        return []
    elif isinstance(items, list):
        return items
    else:
        return [items]
