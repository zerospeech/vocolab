# todo Server runs the worker asynchronously
# todo Server handles shutdown calls via signals and closes all evaluations

# todo supervisor runs the server
# todo main runs all and hadnles configs
# todo config object should probably be outside of all


# todo eval worker needs to log & access inside submissions

# todo update worker needs to access only a specific module.
import os

from zerospeech import out
from zerospeech.task_manager.server import Config, Server
from zerospeech.task_manager.supervisors import Multiprocess


def run(**kwargs):
    out.Console.Logger.info(f"Initiating worker server @ PID: {os.getpid()}")
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


if __name__ == '__main__':
    run(
        channel='zerospeech',
        worker='echo',
        nb_workers=3
    )

