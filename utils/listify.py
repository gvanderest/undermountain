def listify(maybe_list):
    if isinstance(maybe_list, list):
        return maybe_list
    elif isinstance(maybe_list, tuple):
        return list(maybe_list)
    else:
        return [maybe_list]
