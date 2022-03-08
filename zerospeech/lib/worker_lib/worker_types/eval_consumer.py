import shlex
import subprocess
from pathlib import Path
from typing import List

import aio_pika

from zerospeech import get_settings, exc, out
from zerospeech.db.models.tasks import SubmissionEvaluationMessage, message_from_bytes, UpdateType, ExecutorsType
from zerospeech.lib import submissions_lib
from .abstract_worker import AbstractWorker, ServerState
from ..msg import send_update_message

_settings = get_settings()


def verify_bin(bin_path):
    """ Verifies that bin_path is in the registered bin folder of the current host """
    my_bin = _settings.REMOTE_BIN.get(_settings.hostname, None)
    all_parents = [p.resolve() for p in bin_path.parents]
    if my_bin.resolve() not in [bin_path.resolve(), *all_parents]:
        raise exc.SecurityError(f'attempting to execute a file not in authorized directory {bin_path}')


def verify_host_bin():
    """ Verifies that the current host has a valid bin directory """
    my_bin = _settings.REMOTE_BIN.get(_settings.hostname, None)
    if my_bin is None:
        raise exc.ServerError(f"No bin directory configured for current host {_settings.hostname}")


def build_cmd(_cmd: SubmissionEvaluationMessage) -> List[str]:
    """ Build a subprocess command from an evaluation message """

    executor = _cmd.executor.to_exec()
    if executor is None:
        raise ValueError(f'{_cmd.executor} is not present in system')

    sub_dir = submissions_lib.get_submission_dir(_cmd.submission_id)
    bin_path = Path(_cmd.bin_path).resolve()
    verify_bin(bin_path)
    script = bin_path / _cmd.script_name

    cmd_list = [executor]
    if _cmd.executor == ExecutorsType.sbatch:
        cmd_list.extend([
            f"--job-name='{_cmd.label}'",  # name the job on slurmDB
            f"--output={sub_dir}/slurm.log",
            "--wait",  # wait for the process to complete
        ])
    elif _cmd.executor == ExecutorsType.docker:
        raise NotImplementedError("should add some verification for docker-run support")

    # custom executor args from DB
    cmd_list.extend(_cmd.executor_args)

    # script to run + args
    cmd_list.append(str(script))
    cmd_list.extend(_cmd.cmd_args)

    return cmd_list


class EvalTaskWorker(AbstractWorker):

    def __init__(self, *, config, server_state: ServerState):
        super(EvalTaskWorker, self).__init__(config=config, server_state=server_state)
        verify_host_bin()

    def start_process(self, _id, submission_id: str):
        self.server_state.processes[_id] = submission_id
        with submissions_lib.SubmissionLogger(submission_id) as lg:
            lg.log(f"Starting Evaluation process jb<{_id}>")
            lg.log(f"<!-----------------------------------", append=True)

    def end_process(self, _id):
        submission_id = self.server_state.processes.get(_id)
        del self.server_state.processes[_id]
        with submissions_lib.SubmissionLogger(submission_id) as lg:
            lg.log(f"Evaluation process jb<{_id}> completed!!")
            lg.log(f"----------------------------------/>", append=True)

    @staticmethod
    def eval_subprocess(_cmd: SubmissionEvaluationMessage):
        """ Evaluate a subprocess type BrokerCMD """
        cmd_array = build_cmd(_cmd)
        out.log.debug(f"$> {shlex.join(cmd_array)}")
        # run cmd as subprocess
        result = subprocess.run(
            cmd_array,
            capture_output=True, text=True
        )
        # process results
        output = f"{result.stdout}\n{result.stderr}"
        return result.returncode, output

    async def _processor(self, message: aio_pika.IncomingMessage):
        try:
            # todo: check if async is messing with stuff ?
            async with message.process():
                br = message_from_bytes(message.body)

                if not isinstance(br, SubmissionEvaluationMessage):
                    raise ValueError("Cannot process non SubmissionEvaluationMessages")

                submission_fs = submissions_lib.get_submission_dir(br.submission_id, as_obj=True)
                if submission_fs.eval_lock.is_file():
                    return None  # if already evaluating should exit
                # create eval lock
                submission_fs.eval_lock.touch()

                out.log.info(f"Received evaluation request of {br.submission_id}")
                # create a log entry
                self.start_process(br.job_id, br.submission_id)

                status, eval_output = self.eval_subprocess(br)
                if status == 0:
                    out.log.info(f"Evaluation of {br.submission_id} was completed successfully")
                else:
                    out.log.warning(f"Evaluation of {br.submission_id} was completed "
                                    f"with a non zero return code. see logs for details!!")

                # write output in log
                with submissions_lib.SubmissionLogger(br.submission_id) as lg:
                    lg.append_eval(eval_output)

                # Notify updater
                if status == 0:
                    await send_update_message(
                        submission_id=br.submission_id, hostname=_settings.hostname,
                        update_type=UpdateType.evaluation_complete,
                        label=f"{_settings.hostname}-completed-{br.submission_id}"
                    )
                else:
                    await send_update_message(
                        submission_id=br.submission_id, hostname=_settings.hostname,
                        update_type=UpdateType.evaluation_failed,
                        label=f"{_settings.hostname}-failed-{br.submission_id}"
                    )

                # remove process from process logs
                self.end_process(br.job_id)
        except Exception as e:
            if br is not None and hasattr(br, "submission_id"):
                submission_dir = submissions_lib.get_submission_dir(br.submission_id, as_obj=True)
                submission_dir.error_lock.touch()

                # send message to client that submission failed to evaluate
                await send_update_message(
                    submission_id=br.submission_id, hostname=_settings.hostname,
                    update_type=UpdateType.evaluation_failed,
                    label=f"{_settings.hostname}-failed-{br.submission_id}"
                )
            raise e
        finally:
            # clear lock once process is completed
            if submission_fs:
                submission_fs.eval_lock.unlink()
