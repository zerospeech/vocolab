import asyncio
import signal
from zerospeech.task_manager.supervisors import Multiprocess, SingleProcess
from zerospeech.task_manager.workers import EchoWorker, UpdateTaskWorker, EvalTaskWorker

SUPERVISORS = {f"multiprocess": Multiprocess, f"singleprocess": SingleProcess}
WORKER_TYPE = {f"eval": EvalTaskWorker, "update": UpdateTaskWorker, "echo": EchoWorker}

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class Config:

    def __init__(self, **kwargs):
        # Supervisor class
        supervisor = kwargs.get("supervisor", "singleprocess")
        self.supervisor_class = SUPERVISORS.get(supervisor)
        # Worker class
        worker = kwargs.get("worker", "eval")
        self.worker = WORKER_TYPE.get(worker)
        # setup channel
        self.channel = kwargs.get('channel')


class Server:

    def __init__(self, config: Config):
        self.config = config
        self.started = False
        self.should_exit = False
        self.force_exit = False

    def run(self):

        # self.wo
        main_loop = asyncio.get_event_loop()





