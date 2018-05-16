def tablefy(data, column=None, gutter=1, width=79):
    """
    Convert a list of strings into being a table, displaying in a left-to-right
    and top-to-bottom pattern.  This does not sort the values.

    :param data: list of strings
    :param column: width of column, if None, detected
    :param gutter: width of gutter
    :param width: width of entire table to fill
    :returns: newline separated string
    """

    if not data:
        return ""

    lines = []

    if column is None:
        column = max([len(s) for s in data])

    per_line = max(int(width / column), 1)

    gutter_chars = " " * gutter

    items = []
    for entry in data:
        items.append(entry.ljust(column))
        if len(items) == per_line:
            lines.append(gutter_chars.join(items))
            items = []

    if items:
        lines.append(gutter_chars.join(items))

    return "\n".join(lines)
