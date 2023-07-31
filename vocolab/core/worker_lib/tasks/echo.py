import os

from vocolab import out, get_settings
from vocolab.data import models

_settings = get_settings()


def echo_fn(slm: models.tasks.SimpleLogMessage):
    """ Simple task that echoes a message into the log"""
    out.log.info(f"{os.getpid()} | \[{slm.timestamp.isoformat()}\] {slm.message}")
