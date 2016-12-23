"""
SETTINGS
Provide options and flags for users to customize.
"""
import os.path
from modules.example import ExampleModule


MODULES = (
    ExampleModule,
)

DATA_PATH = os.path.dirname(__file__) + "/data"
ROT_DATA_PATH = DATA_PATH + "/__rot__"


PID_FILE = "pid"
SHUTDOWN_FILE = 'SHUTDOWN'
REBOOT_FILE = 'REBOOT'
