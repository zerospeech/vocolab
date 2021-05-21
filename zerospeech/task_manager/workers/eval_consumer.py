import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import aio_pika

from zerospeech import get_settings, exc, out
from zerospeech.task_manager.model import SubmissionEvaluationMessage, ExecutorsType
from zerospeech.task_manager.workers.abstract_worker import AbstractWorker

if TYPE_CHECKING:
    from zerospeech.task_manager.config import ServerState

_settings = get_settings()


def verify_bin(bin_path):
    """ Verifies that bin_path is in the registered bin folder of the current host """
    my_bin = _settings.REMOTE_BIN.get(_settings.hostname, None)
    if my_bin not in [bin_path, *bin_path.parents]:
        raise exc.SecurityError(f'attempting to execute a file not in authorized directory {bin_path}')


def verify_host_bin():
    """ Verifies that the current host has a valid bin directory """
    my_bin = _settings.REMOTE_BIN.get(_settings.hostname, None)
    if my_bin is None:
        raise exc.ServerError(f"No bin directory configured for current host {_settings.hostname}")


class EvalTaskWorker(AbstractWorker):

    def __init__(self, *, config, server_state: 'ServerState'):
        super(EvalTaskWorker, self).__init__(config=config)
        verify_host_bin()
        self.server_state = server_state

    def add_process_location(self, _id, submission_id: str):
        self.server_state.processes[_id] = submission_id

    def remove_process_location(self, _id):
        del self.server_state.processes[_id]

    @staticmethod
    def eval_subprocess(_cmd: SubmissionEvaluationMessage):
        """ Evaluate a subprocess type BrokerCMD """
        bin_path = Path(_cmd.exe_path)
        verify_bin(bin_path)
        script = bin_path / _cmd.p_name
        result = subprocess.run(
            [_cmd.executor.to_exec(), str(script), *_cmd.args], capture_output=True, text=True
        )
        # process results
        if result.returncode != 0:
            return result.returncode, result.stderr
        return result.returncode, result.stdout

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            pass
            # fixme repair broker messaging
            br = ...  # BrokerCMD.from_bytes(message.body)

            if not br.executor.is_subprocess:
                out.Console.Logger.error("Eval consumer cannot evaluate non subprocess packet!!!")

            # todo maybe add submission [path/id] in message
            self.add_process_location(br.job_id, br)

            status, result = self.eval_subprocess(br)
            # todo create failed_stuff && success_stuff logfile
            if status != 0:
                out.Console.error(f"Command {br} returned non 0 code")
            else:
                # eval success
                # 1. report back ?
                out.Console.info(result)

            self.remove_process_location(br.job_id)
