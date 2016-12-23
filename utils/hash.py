import random


def get_random_hash():
    """Get a randomized hash."""
    return "%040x" % random.getrandbits(40 * 4)
