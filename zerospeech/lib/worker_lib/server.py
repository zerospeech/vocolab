import asyncio
import os
import sys
import threading
from datetime import datetime

from zerospeech import out, get_settings
from zerospeech.db.models.tasks import UpdateType
from zerospeech.lib import submissions_lib, misc
from .config import HANDLED_SIGNALS, Config, ServerState, SING_TO_STR
from .msg import send_update_message

_settings = get_settings()


class Server:

    def __init__(self, *, config: Config):
        self.config = config
        self.server_state = ServerState(os.getpid(), dict())
        self.worker = config.worker(config=config, server_state=self.server_state)

    def run(self):
        out.Console.Logger.info(f"initiating server-{os.getpid()} components...")
        main_loop = asyncio.get_event_loop()
        self.install_signal_handlers(main_loop)

        main_loop.create_task(self.worker.run(loop=main_loop))
        out.Console.Logger.info(f"server-{os.getpid()} is up on listening on {self.config.channel} !!")
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

        for _id, sub_id in self.server_state.processes.items():
            sub_loc = submissions_lib.get_submission_dir(sub_id)

            with (sub_loc / 'interrupted.lock').open('w') as fp:
                fp.write(f"when: {datetime.now().isoformat()}\n")
                fp.write(f"what: {sig}\n")

            misc.run_with_loop(send_update_message,
                               submission_id=sub_id, hostname=_settings.hostname,
                               update_type=UpdateType.evaluation_canceled,
                               label=f"{_settings.hostname}-canceled-{sub_id}"
                               )

        # cancel all active tasks
        for task in asyncio.Task.all_tasks():
            task.cancel()

        out.Console.Logger.info("exiting...")
        sys.exit(0)
