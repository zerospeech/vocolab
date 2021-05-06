import multiprocessing
import os
import signal
import threading
from typing import Callable, Dict

from zerospeech import out

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


# supervisor
class Multiprocess:
    """ A class to cleanly manage multiple workers running a task """

    def __init__(self, target: Callable, target_kwargs: Dict, workers: int = 4):
        self.workers = workers
        self.target = target
        self.target_kwargs = target_kwargs
        self.processes = []
        self.should_exit = threading.Event()
        self.pid = os.getpid()
        self.spawn = multiprocessing.get_context("spawn")

    def signal_handler(self, sig, frame):
        """
        A signal handler that is registered with the parent process.
        """
        self.should_exit.set()

    def run(self):
        self.startup()
        self.should_exit.wait()
        self.shutdown()

    def startup(self):
        out.Console.Logger.info(f"Started parent process [{self.pid}]")

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self.signal_handler)

        # todo check if child process needs any global state (Config object or arguments)
        for _ in range(self.workers):
            process = self.spawn.Process(target=self.target, kwargs=self.target_kwargs)
            process.start()
            self.processes.append(process)

    def shutdown(self):
        out.Console.Logger.info(f"Graceful shutdown initiated: sending SIGTERM to children")
        # todo check how to handle terminate process in child
        for process in self.processes:
            process.terminate()

        for process in self.processes:
            process.join()

        out.Console.Logger.info(f"Stopping parent process [{self.pid}]")


class SingleProcess:
    """ ... """
    pass
