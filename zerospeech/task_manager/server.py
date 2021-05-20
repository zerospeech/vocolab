import asyncio
import os
import sys
import threading
from datetime import datetime

from zerospeech import out
from zerospeech.task_manager.config import HANDLED_SIGNALS, Config, ServerState, SING_TO_STR


class Server:

    def __init__(self, *, config: Config):
        self.config = config
        self.worker = config.worker(config=config)
        self.server_state = ServerState(os.getpid(), dict())

    def run(self):
        out.Console.Logger.info(f"initiating server-{os.getpid()} components...")
        main_loop = asyncio.get_event_loop()
        self.install_signal_handlers(main_loop)

        main_loop.create_task(self.worker.run(loop=main_loop, server_state=self.server_state))
        out.Console.Logger.info(f"server-{os.getpid()} is up !!")
        main_loop.run_forever()

    def install_signal_handlers(self, loop) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        for sig in HANDLED_SIGNALS:
            loop.add_signal_handler(sig, self.handle_exit, sig, None)

    def handle_exit(self, sig, frame):
        out.Console.console.print("\n")
        out.Console.Logger.warning(f"EXIT has been requested ({SING_TO_STR.get(sig, 'SIG_XX')})")

        for _id, loc in self.server_state.processes.items():
            with (loc / 'interrupted.lock').open('w') as fp:
                fp.write(f"when: {datetime.now().isoformat()}\n")
                fp.write(f"what: {sig}\n")

        # cancel all active tasks
        for task in asyncio.Task.all_tasks():
            task.cancel()

        out.Console.Logger.info("exiting...")
        sys.exit(0)

