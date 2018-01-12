"""
ANSI MUD Colorization.

Colorization library for helping with MUD-style color symbols to transform
them to/from their special escape codes.
"""
import collections
import random


ESCAPE = chr(27)
CSI = ESCAPE + '['
REAL_BRACKET_SYMBOL = '((bracket))'

REMAPS = {
    "{r": CSI + "0;31m",  # Red
    "{1": CSI + "0;31m",  # Red
    "{R": CSI + "1;31m",  # Bright Red
    "{!": CSI + "1;31m",  # Bright Red
    "{g": CSI + "0;32m",  # Green
    "{2": CSI + "0;32m",  # Green
    "{G": CSI + "1;32m",  # Bright Green
    "{@": CSI + "1;32m",  # Bright Green
    "{y": CSI + "0;33m",  # Yellow
    "{3": CSI + "0;33m",  # Yellow
    "{Y": CSI + "1;33m",  # Bright Yellow
    "{#": CSI + "1;33m",  # Bright Yellow
    "{b": CSI + "0;34m",  # Blue
    "{4": CSI + "0;34m",  # Blue
    "{B": CSI + "1;34m",  # Bright Blue
    "{$": CSI + "1;34m",  # Bright Blue
    "{m": CSI + "0;35m",  # Magenta
    "{5": CSI + "0;35m",  # Magenta
    "{M": CSI + "1;35m",  # Bright Magenta
    "{%": CSI + "1;35m",  # Bright Magenta
    "{c": CSI + "0;36m",  # Cyan
    "{6": CSI + "0;36m",  # Cyan
    "{C": CSI + "1;36m",  # Bright Cyan
    "{^": CSI + "1;36m",  # Bright Cyan
    "{w": CSI + "0;37m",  # White
    "{7": CSI + "0;37m",  # White
    "{W": CSI + "1;37m",  # Bright White
    "{&": CSI + "1;37m",  # Bright White
    "{8": CSI + "1;30m",  # Grey
    "{*": CSI + "1;30m",  # Grey
    '{D': CSI + '1;30m',  # Grey
    "{0": CSI + "0m",  # Reset
    "{x": CSI + "0m",  # Reset
    '{.': CSI + '0m',  # Reset

    # Extended Color Reference:
    # http://www.calmar.ws/vim/256-xterm-24bit-rgb-color-chart.html
    "{o": CSI + "38;5;130m",  # Dark Orange
    "{O": CSI + "38;5;202m",  # Bright Orange
    "{p": CSI + "38;5;55m",  # Dark Purple
    "{P": CSI + "38;5;129m",  # Bright Purple
}


def decolorize(in_string):
    """Convert a color-coded string to remove all color codes."""
    return colorize(in_string, strip_colors=True)


def escape(message):
    return message.replace("{", "{{")


def colorize(in_string, strip_colors=False):
    """Convert a color-coded string to ANSI-encoded."""
    out_string = in_string

    # Replace "brackets" with a placeholder
    out_string = out_string.replace('{{', REAL_BRACKET_SYMBOL)

    # Replace out bracket colors with ANSI
    for key in REMAPS:
        color = REMAPS[key]
        ansi = color

        if not strip_colors:
            out_string = out_string.replace(key, ansi)
        else:
            out_string = out_string.replace(key, '')

    # Replace random color codes with random ANSI colors
    if not strip_colors:
        random_count = out_string.count("{-")
        for _ in range(0, random_count):
            color = 30 + random.randint(0, 7)

            if color == 30:
                brightness = 1
            else:
                brightness = random.randint(0, 1)

            color = str(color)
            brightness = str(brightness)

            ansi = CSI + brightness + ";" + color + "m"

            # One random at a time
            out_string = out_string.replace("{-", ansi, 1)
    else:
        # Remove all random colors
        out_string = out_string.replace("{-", '')

    # Replace the previous placeholders with the brackets
    out_string = out_string.replace(REAL_BRACKET_SYMBOL, "{")

    return out_string


def pad_left(message, length, symbol=" "):
    """Pad a colorized string's left."""
    stripped = decolorize(message)
    return (symbol * max(0, length - len(stripped))) + message


def pad_right(message, length, symbol=" "):
    """Pad a colorized string's right."""
    stripped = decolorize(message)
    return message + (symbol * max(0, length - len(stripped)))


def stop_color_bleed(message):
    """
    Iterates over a message or list of messages to stop color bleeds.

    Color bleeds could be caused by future surrounding content, so this
    will ensure that the lines properly start with the correct colors and
    end with the correct colors.
    """
    # Convert to a list, to iterate over content.
    is_list = True
    lines = message
    if not isinstance(lines, collections.Iterable):
        is_list = False
        lines = [lines]

    RESET_COLOR = "{x"
    last_color = RESET_COLOR
    for line in lines:
        cleaned = "{}{}{}".format(last_color, line, RESET_COLOR)

        if not is_list:
            return cleaned

        yield cleaned

        # Find the last color of the line, store it for the next line
        for index, char in enumerate(line):
            if char == "{":
                whole_color = line[index:index+2]
                if whole_color != "{{":
                    last_color = whole_color
