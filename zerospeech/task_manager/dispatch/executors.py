""" Module that evaluates BrokerCMDs """
import subprocess
import uuid
from importlib import import_module
from pathlib import Path

from zerospeech.task_manager import BrokerCMD, ExecutorsType


def eval_function(cmd: BrokerCMD):
    """ Evaluate a function type BrokerCMD """
    mod = import_module(cmd.module_path)
    fn = getattr(mod, cmd.f_name)

    if isinstance(cmd.args, list):
        return fn(*cmd.args)
    elif isinstance(cmd.args, dict):
        return fn(**cmd.args)


def eval_subprocess(cmd: BrokerCMD):
    """ Evaluate a subprocess type BrokerCMD """
    script = Path(cmd.module_path) / cmd.f_name
    result = subprocess.run(
        [cmd.executor.to_exec(), str(script), *cmd.args], capture_output=True, text=True
    )
    if result.returncode != 0:
        return result.returncode, result.stderr
    return result.returncode, result.stdout


def eval_cmd(cmd: BrokerCMD):
    """ Evaluate a BrokerCMD

    :returns Tuple[exitcode, result<Any>]
    """
    executor = cmd.executor
    if executor == ExecutorsType.function:
        res = 0, eval_function(cmd)
    else:
        res = eval_subprocess(cmd)
    return res


if __name__ == '__main__':
    root_dir = Path(__file__).parents[2]

    # a CMD to test eval functions
    _cmd = BrokerCMD(
        job_id=str(uuid.uuid1()),
        executor=ExecutorsType.function,
        label="testing",
        f_name="dummy_function",
        module_path=f"zerospeech.task_manager.tasks",
        args=dict(where=f"{Path.home() / 'tmp/ci-m4rAPVF16M'}", lines=5, length=25)
    )
