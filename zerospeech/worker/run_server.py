import os

from zerospeech import out
from zerospeech.lib.worker_lib import Config, Server, Multiprocess


def run(**kwargs):
    """ Run the server """
    out.Logger.info(f"Initiating worker server @ PID: {os.getpid()}")
    config = Config(**kwargs)
    server = Server(config=config)

    if config.nb_workers > 1:
        supervisor = Multiprocess(
            target=server.run,
            target_kwargs={},
            workers=config.nb_workers
        )
        supervisor.run()
    else:
        server.run()
