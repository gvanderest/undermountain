"""ANSI MUD Colorization."""
import random


class Ansi(object):
    """
    ANSI MUD Colorization.

    Colorization library for helping with MUD-style color symbols to transform
    them to/from their special escape codes.
    """

    ESCAPE = chr(27)
    CSI = ESCAPE + '['
    REAL_BRACKET_SYMBOL = '((bracket))'

    REMAPS = {
        "{r": CSI + "0;31m", "{1": CSI + "0;31m",  # Red
        "{R": CSI + "1;31m", "{!": CSI + "1;31m",  # Bright Red
        "{g": CSI + "0;32m", "{2": CSI + "0;32m",  # Green
        "{G": CSI + "1;32m", "{@": CSI + "1;32m",  # Bright Green
        "{y": CSI + "0;33m", "{3": CSI + "0;33m",  # Yellow
        "{Y": CSI + "1;33m", "{#": CSI + "1;33m",  # Bright Yellow
        "{b": CSI + "0;34m", "{4": CSI + "0;34m",  # Blue
        "{B": CSI + "1;34m", "{$": CSI + "1;34m",  # Bright Blue
        "{m": CSI + "0;35m", "{5": CSI + "0;35m",  # Magenta
        "{M": CSI + "1;35m", "{%": CSI + "1;35m",  # Bright Magenta
        "{c": CSI + "0;36m", "{6": CSI + "0;36m",  # Cyan
        "{C": CSI + "1;36m", "{^": CSI + "1;36m",  # Bright Cyan
        "{w": CSI + "0;37m", "{7": CSI + "0;37m",  # White
        "{W": CSI + "1;37m", "{&": CSI + "1;37m",  # Bright White
        "{8": CSI + "1;30m", "{*": CSI + "1;30m", '{D': CSI + '1;30m',  # Grey
        "{0": CSI + "0m", "{x": CSI + "0m", '{.': CSI + '0m',  # Reset

        # Extended Color Reference:
        # http://www.calmar.ws/vim/256-xterm-24bit-rgb-color-chart.html
        "{o": CSI + "38;5;130m" + CSI + "38;5;130m",  # Dark Orange
        "{O": CSI + "38;5;202m" + CSI + "38;5;202m",  # Bright Orange
        "{p": CSI + "38;5;55m" + CSI + "38;5;55m",  # Dark Purple
        "{P": CSI + "38;5;129m" + CSI + "38;5;129m",  # Bright Purple

        # Extra Special
        "{H": CSI + "25l",  # Hide Cursor
    }

    @classmethod
    def decolorize(cls, in_string):
        """Convert a color-coded string to remove all color codes."""
        return cls.colorize(in_string, strip_colors=True)

    @classmethod
    def colorize(cls, in_string, strip_colors=False):
        """Convert a color-coded string to ANSI-encoded."""
        out_string = in_string

        # Replace "brackets" with a placeholder
        out_string = out_string.replace('{{', cls.REAL_BRACKET_SYMBOL)

        # Replace out bracket colors with ANSI
        for key in cls.REMAPS:
            color = cls.REMAPS[key]
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

                ansi = cls.CSI + brightness + ";" + color + "m"

                # One random at a time
                out_string = out_string.replace("{-", ansi, 1)
        else:
            # Remove all random colors
            out_string = out_string.replace("{-", '')

        # Replace the previous placeholders with the brackets
        out_string = out_string.replace(cls.REAL_BRACKET_SYMBOL, "{")

        return out_string

    @classmethod
    def pad_left(cls, message, length, symbol=" "):
        """Pad a colorized string's left."""
        stripped = cls.decolorize(message)
        return (symbol * max(0, length - len(stripped))) + message

    @classmethod
    def pad_right(cls, message, length, symbol=" "):
        """Pad a colorized string's right."""
        stripped = cls.decolorize(message)
        return message + (symbol * max(0, length - len(stripped)))
