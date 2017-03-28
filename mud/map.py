import math


class Map(object):
    def __init__(self, data, width, height, origin=None):
        self.data = data
        self.origin = origin
        self.width = width
        self.height = height

    """
    --- --- --- ---
    . . . . . . . . . .
    --- ---         ---
           |. . . .|
    """
    def format_walls(self, endcaps=False):
        origin = self.origin or (None, None)
        origin_y, origin_x = origin

        rows = len(self.data)
        columns = len(self.data[0]) if rows else 0
        if rows == 0 or columns == 0:
            return ""

        inflated_height = rows * 2
        inflated_width = columns * 4

        formatted = self.get_grid(inflated_height, inflated_width, value=" ")
        grid = self.data
        for y, row in enumerate(grid):
            for x, room in enumerate(row):

                if room is None:
                    continue

                actual_y = y * 2
                actual_x = x * 4

                # If there is no north exit, draw a wall
                if not room.get_exit("north"):
                    formatted[actual_y - 1][actual_x - 1] = "-"
                    formatted[actual_y - 1][actual_x] = "-"
                    formatted[actual_y - 1][actual_x + 1] = "-"

                # If there is no north exit, draw a wall
                if not room.get_exit("south"):
                    formatted[actual_y + 1][actual_x - 1] = "-"
                    formatted[actual_y + 1][actual_x] = "-"
                    formatted[actual_y + 1][actual_x + 1] = "-"

                # If there is no east exit, draw a wall
                if not room.get_exit("east"):
                    formatted[actual_y][actual_x + 2] = "|"

                # If there is no west exit, draw a wall
                if not room.get_exit("west"):
                    formatted[actual_y][actual_x - 2] = "|"

                # The room we're in
                formatted[actual_y][actual_x - 1] = "."
                formatted[actual_y][actual_x + 1] = "."

                if x == origin_x and y == origin_y:
                    formatted[actual_y][actual_x] = "{R@{x"

        # Add some end-caps to walls
        for y, row in enumerate(formatted):
            for x, symbol in enumerate(row):
                if symbol == "|":
                    try:
                        if formatted[y+2][x] == symbol:
                            formatted[y+1][x] = symbol
                    except IndexError:
                        pass

                    if endcaps:
                        try:
                            if formatted[y+1][x+1] == "-":
                                formatted[y+1][x] = "+"
                        except IndexError:
                            pass

                        try:
                            if formatted[y+1][x-1] == "-":
                                formatted[y+1][x] = "+"
                        except IndexError:
                            pass

                elif symbol == "-":
                    try:
                        if formatted[y][x+2] == symbol:
                            formatted[y][x+1] = symbol
                    except IndexError:
                        pass

                    if endcaps:
                        try:
                            if formatted[y+1][x-1] == "|":
                                formatted[y][x-1] = "+"
                        except IndexError:
                            pass

                        try:
                            if formatted[y+1][x+1] == "|":
                                formatted[y][x+1] = "+"
                        except IndexError:
                            pass

        top_padding = math.floor((inflated_height - self.height) / 2)
        left_padding = math.floor((inflated_width - self.width) / 2)
        cropped = [
            row[left_padding:left_padding + self.width] for row in
            formatted[top_padding:top_padding + self.height]
        ]
        return cropped

    def format_normal(self):
        origin = self.origin or (None, None)

        rows = len(self.data)
        columns = len(self.data[0]) if rows else 0
        if rows == 0 or columns == 0:
            return ""

        formatted = self.get_grid(rows * 2, columns * 2, value=" ")
        grid = self.data
        for y, row in enumerate(grid):
            for x, room in enumerate(row):
                if room is None:
                    continue
                actual_y = y * 2
                actual_x = x * 2

                # TODO Make use of the existing grid instead of lookups
                if room.get_exit("north"):
                    formatted[actual_y - 1][actual_x] = "|"
                if room.get_exit("east"):
                    formatted[actual_y][actual_x + 1] = "-"
                if room.get_exit("south"):
                    formatted[actual_y + 1][actual_x] = "|"
                if room.get_exit("west"):
                    formatted[actual_y][actual_x - 1] = "-"
                if room.get_exit("up"):
                    formatted[actual_y - 1][actual_x + 1] = "{Y,{x"
                if room.get_exit("down"):
                    formatted[actual_y + 1][actual_x - 1] = "{Y'{x"

                formatted[actual_y][actual_x] = \
                    "{R@{x" if (origin[0] == y and origin[1] == x) else "{C#{x"

        return formatted

    def format_lines(self, style="walls"):
        if style == "walls":
            formatted = self.format_walls()
        else:
            formatted = self.format_normal()
        return ["".join(row[:self.width]) for row in formatted[:self.height]]

    def format_string(self):
        return "\n".join(self.format_lines)

    @classmethod
    def get_grid(cls, rows, columns, value=None):
        """Return a 2-dimension dictionary of value."""
        grid = []
        for cy in range(rows):
            row = []
            for cx in range(columns):
                row.append(value)
            grid.append(row)
        return grid

    @classmethod
    def generate_from_room(cls, origin_room, height=25, width=50):
        POSITION_MODIFIERS = {
            "north": (-1, 0),
            "east": (0, 1),
            "south": (1, 0),
            "west": (0, -1)
        }

        columns = math.ceil(width / 2)
        rows = math.ceil(height / 2)

        grid = cls.get_grid(rows, columns)

        origin_x = math.floor(columns / 2)
        origin_y = math.floor(rows / 2)

        room_ids = []
        stack = [
            (origin_y, origin_x, origin_room)
        ]
        while stack:
            y, x, room = stack.pop()
            grid[y][x] = room
            room_ids.append(room.id)

            for exit in room.get_exits():
                if exit.direction_id not in POSITION_MODIFIERS:
                    continue
                modifier = POSITION_MODIFIERS[exit.direction_id]
                next_y = y + modifier[0]
                next_x = x + modifier[1]
                if next_x > 0 and next_x < columns and \
                        next_y > 0 and next_y < rows:
                    next_room = exit.get_room()
                    if next_room.id in room_ids:
                        continue
                    stack.append((next_y, next_x, next_room))

        return cls(grid, width=width, height=height,
                   origin=(origin_y, origin_x))
