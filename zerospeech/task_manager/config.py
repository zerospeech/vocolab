import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

SING_TO_STR = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                   if v.startswith('SIG') and not v.startswith('SIG_'))


@dataclass
class ServerState:
    pid: int
    processes: Dict[str, str]
    should_exit: bool = False


class Config:

    def __init__(self, **kwargs):
        from .workers import WORKER_TYPE

        # Worker class
        worker = kwargs.get("worker", "eval")
        self.worker = WORKER_TYPE.get(worker)
        # setup channel
        self.channel = kwargs.get('channel')
        # nb workers
        self.nb_workers = kwargs.get('nb_workers', 1)
        # Prefetch count
        self.prefetch_count = kwargs.get("prefetch_count", 3)
