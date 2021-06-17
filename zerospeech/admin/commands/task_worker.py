import sys

from zerospeech import out
from zerospeech.admin import cmd_lib
from zerospeech.worker.run_server import run as tasks_run


class TaskWorkerCMD(cmd_lib.CMD):
    """ Administrate Task Workers """

    def __init__(self, root, name, cmd_path):
        super(TaskWorkerCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()


class RunTaskWorkerCMD(cmd_lib.CMD):
    """ Execute Task Workers Processes """

    def __init__(self, root, name, cmd_path):
        super(RunTaskWorkerCMD, self).__init__(root, name, cmd_path)

    def run(self, argv):
        _ = self.parser.parse_args(argv)
        self.parser.print_help()


class EchoTaskWorkerCMD(cmd_lib.CMD):
    """ Run echo task worker (used as debug worker)"""

    def __init__(self, root, name, cmd_path):
        super(EchoTaskWorkerCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-w', '--number-of-workers', dest='nb_workers', default=1, type=int,
                                 help="Number of processes to allow for workers")
        self.parser.add_argument('--prefetch-count', default=1, type=int,
                                 help="Number of simultaneous messages allowed to be pulled by one process")

    # noinspection PyBroadException
    def run(self, argv):
        args = self.parser.parse_args(argv)
        try:
            tasks_run(worker='echo', **args.__dict__)
        except Exception:
            out.Console.exception()
            sys.exit(1)


class EvaluationTaskWorkerCMD(cmd_lib.CMD):
    """ Run evaluation task worker """

    def __init__(self, root, name, cmd_path):
        super(EvaluationTaskWorkerCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-w', '--number-of-workers', dest='nb_workers', default=1, type=int,
                                 help="Number of processes to allow for workers")
        self.parser.add_argument('--prefetch-count', default=1, type=int,
                                 help="Number of simultaneous messages allowed to be pulled by one process")

    # noinspection PyBroadException
    def run(self, argv):
        args = self.parser.parse_args(argv)
        try:
            tasks_run(worker='eval', **args.__dict__)
        except Exception:
            out.Console.exception()
            sys.exit(1)


class UpdateTaskWorkerCMD(cmd_lib.CMD):
    """ Run update task worker """

    def __init__(self, root, name, cmd_path):
        super(UpdateTaskWorkerCMD, self).__init__(root, name, cmd_path)
        self.parser.add_argument('-w', '--number-of-workers', dest='nb_workers', default=1, type=int,
                                 help="Number of processes to allow for workers")
        self.parser.add_argument('--prefetch-count', default=1, type=int,
                                 help="Number of simultaneous messages allowed to be pulled by one process")

    # noinspection PyBroadException
    def run(self, argv):
        args = self.parser.parse_args(argv)
        try:
            tasks_run(worker='update', **args.__dict__)
        except Exception:
            out.Console.exception()
            sys.exit(1)
