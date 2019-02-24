from data.settings import *
import sys

def get(name: str, default=None):
    return getattr(sys.modules[__name__], name, default)
