import signal

from zerospeech import get_settings
from .worker_types import WORKER_TYPE, ServerState

_settings = get_settings()

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

SING_TO_STR = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
                   if v.startswith('SIG') and not v.startswith('SIG_'))


class Config:

    def __init__(self, **kwargs):
        # Worker class
        worker = kwargs.get("worker", "eval")
        self.worker = WORKER_TYPE.get(worker)
        # setup channel
        self.channel = kwargs.get('channel', None)
        if self.channel is None:
            self.channel = _settings.QUEUE_CHANNELS.get(worker)

        # nb workers
        self.nb_workers = kwargs.get('nb_workers', 1)
        # Prefetch count
        self.prefetch_count = kwargs.get("prefetch_count", 3)
