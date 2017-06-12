def columnify(strings, return_lines=False, return_serialized=False,
              max_length=None, screen_width=79, gutter_width=1):
    """
    Return a list of columns, lines, or a single string of values provided.
    @param {list<str>} strings
    @param {bool} [return_lines]
    @param {bool} [return_serialized]
    @param {int} [max_length]
    @param {int} [screen_width]
    @param {int} [gutter_width]
    """
    if max_length is None:
        max_length = screen_width

    strings = sorted(strings)
    column_width = min(max_length, max(map(len, strings)) + gutter_width)
    column_count = int(screen_width / column_width)

    rows = []

    row = []

    def finish_row():
        if return_lines or return_serialized:
            rows.append(''.join(row))
        else:
            rows.append(row)

        return []

    last_string_index = len(strings) - 1
    for index, value in enumerate(strings):
        formatted = value.ljust(column_width)[:column_width]
        row.append(formatted)

        if index > 0 and index % column_count == 0 or \
                index == last_string_index:
            row = finish_row()

    if return_serialized:
        return "\n".join(rows)

    return rows
