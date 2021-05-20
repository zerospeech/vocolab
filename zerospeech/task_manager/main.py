# todo Server runs the worker asynchronously
# todo Server handles shutdown calls via signals and closes all evaluations

# todo supervisor runs the server
# todo main runs all and hadnles configs
# todo config object should probably be outside of all


# todo eval worker needs to log & access inside submissions

# todo update worker needs to access only a specific module.
import argparse
import os
import sys

from zerospeech import out
from zerospeech.task_manager.server import Config, Server
from zerospeech.task_manager.supervisors import Multiprocess
from zerospeech.task_manager.workers import WORKER_TYPE


def arguments(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("worker",
                        choices=list(WORKER_TYPE.keys()), default="eval",
                        help="Worker Type")
    parser.add_argument('-w', '--number-of-workers', dest='nb_workers', type=int,
                        help="Number of processes to allow for workers")
    parser.add_argument('--prefetch-count', default=1, type=int,
                        help="Number of simultaneous messages allowed to be pulled by one process")

    if argv:
        return parser.parse_args(argv)
    return parser.parse_args()


def run(**kwargs):
    """ Run the server """
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


# noinspection PyBroadException
def entrypoint():
    try:
        args = arguments()
        run(**args.__dict__)
    except:
        out.Console.exception()
        sys.exit(1)
