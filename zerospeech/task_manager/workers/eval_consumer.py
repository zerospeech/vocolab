import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import aio_pika

from zerospeech import get_settings, exc, out
from zerospeech import utils
from zerospeech.task_manager.model import SubmissionEvaluationMessage, message_from_bytes
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
        super(EvalTaskWorker, self).__init__(config=config, server_state=server_state)
        verify_host_bin()

    def start_process(self, _id, submission_id: str):
        self.server_state.processes[_id] = submission_id
        with utils.submissions.SubmissionLogger(submission_id) as lg:
            lg.log(f"Starting Evaluation process jb<{_id}>")
            lg.log(f"<!-----------------------------------", append=True)

    def end_process(self, _id):
        submission_id = self.server_state.processes.get(_id)
        del self.server_state.processes[_id]
        with utils.submissions.SubmissionLogger(submission_id) as lg:
            lg.log(f"Evaluation process jb<{_id}> completed!!")
            lg.log(f"----------------------------------/>", append=True)

    @staticmethod
    def eval_subprocess(_cmd: SubmissionEvaluationMessage):
        """ Evaluate a subprocess type BrokerCMD """
        bin_path = Path(_cmd.bin_path).resolve()
        verify_bin(bin_path)
        script = bin_path / _cmd.script_name
        result = subprocess.run(
            [_cmd.executor.to_exec(), str(script), *_cmd.args], capture_output=True, text=True
        )
        # process results
        output = f"{result.stdout}\n{result.stderr}"
        return result.returncode, output

    async def _processor(self, message: aio_pika.IncomingMessage):
        async with message.process():
            br = message_from_bytes(message.body)

            if not isinstance(br, SubmissionEvaluationMessage):
                raise ValueError("Cannot process non SubmissionEvaluationMessages")

            out.Console.Logger.info(f"Received evaluation request of {br.submission_id}")
            # create a log entry
            self.start_process(br.job_id, br.submission_id)

            status, eval_output = self.eval_subprocess(br)

            if status == 0:
                out.Console.Logger.info(f"Evaluation of {br.submission_id} was completed successfully")
                # todo notify updateWorker of success
                pass
            else:
                out.Console.Logger.warning(f"Evaluation of {br.submission_id} was completed "
                                           f"with a non zero return code. see logs for details!!")
                # todo notify updateWorker of failure
                pass

            # write output in log
            with utils.submissions.SubmissionLogger(br.submission_id) as lg:
                lg.append_eval(eval_output)

            # remove process from process logs
            self.end_process(br.job_id)
