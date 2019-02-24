from logging import *
from mud import settings

basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=settings.get("LOGGING_LEVEL", INFO),
)
