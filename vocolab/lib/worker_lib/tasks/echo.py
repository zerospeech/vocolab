import os

from vocolab import out, get_settings
from vocolab.db.models import tasks

_settings = get_settings()


def echo_fn(slm: tasks.SimpleLogMessage):
    """ Simple task that echoes a message into the log"""
    out.log.info(f"{os.getpid()} | \[{slm.timestamp.isoformat()}\] {slm.message}")
