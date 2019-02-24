import logging

NAME = "Waterdeep: City of Splendors"
NAME_SHORT = "Waterdeep"

LOGGING_LEVEL = logging.DEBUG

MODULES = (
    "mud.modules.core.Core",
    "mud.modules.telnet.Telnet",
)

TELNET_HOST = "0.0.0.0"
TELNET_PORTS = (
    4200,
    4201,
)
