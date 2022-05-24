import shlex
import subprocess
from pathlib import Path
from typing import List

from vocolab import out, get_settings, exc
from vocolab.db.models import tasks
from vocolab.lib import submissions_lib

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


def build_cmd(_cmd: tasks.SubmissionEvaluationMessage) -> List[str]:
    """ Build a subprocess command from an evaluation message """

    executor = _cmd.executor.to_exec()
    if executor is None:
        raise ValueError(f'{_cmd.executor} is not present in system')

    sub_dir = submissions_lib.get_submission_dir(_cmd.submission_id)
    bin_path = Path(_cmd.bin_path).resolve()
    verify_bin(bin_path)
    script = bin_path / _cmd.script_name

    cmd_list = [executor]
    if _cmd.executor == tasks.ExecutorsType.sbatch:
        cmd_list.extend([
            f"--job-name='{_cmd.label}'",  # name the job on slurmDB
            f"--output={sub_dir}/slurm.log",
            "--wait",  # wait for the process to complete
        ])
    elif _cmd.executor == tasks.ExecutorsType.docker:
        raise NotImplementedError("should add some verification for docker-run support")

    # custom executor args from DB
    cmd_list.extend(_cmd.executor_args)

    # script to run + args
    cmd_list.append(str(script))
    cmd_list.extend(_cmd.cmd_args)

    return cmd_list


def eval_subprocess(_cmd: tasks.SubmissionEvaluationMessage):
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


def post_eval_update(status: int, sem: tasks.SubmissionEvaluationMessage):
    """ Send message to update queue that evaluation is completed. """
    from vocolab.worker.server import update
    from vocolab.db.models.tasks import SubmissionUpdateMessage, UpdateType

    sum_ = SubmissionUpdateMessage(
        label=f"{_settings.hostname}-completed-{sem.submission_id}",
        submission_id=sem.submission_id,
        updateType=UpdateType.evaluation_undefined,
        hostname=f"{_settings.hostname}"
    )
    if status == 0:
        sum_.updateType = UpdateType.evaluation_complete
    else:
        sum_.updateType = UpdateType.evaluation_failed

    # send update to channel
    update.delay(sum_=sum_.dict())


def evaluate_submission_fn(sem: tasks.SubmissionEvaluationMessage):
    status, eval_output = eval_subprocess(sem)
    if status == 0:
        out.log.info(f"Evaluation of {sem.submission_id} was completed successfully")
    else:
        out.log.warning(f"Evaluation of {sem.submission_id} was completed "
                        f"with a non zero return code. see logs for details!!")

    # write output in log
    with submissions_lib.SubmissionLogger(sem.submission_id) as lg:
        lg.append_eval(eval_output)

    # send submission evaluation result
    post_eval_update(status, sem)
