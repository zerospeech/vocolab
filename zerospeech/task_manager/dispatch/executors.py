""" Module that evaluates BrokerCMDs """
import subprocess
from importlib import import_module
from pathlib import Path

from zerospeech.task_manager import (
    ExecutorsType,
    Function, SubProcess
)


def eval_function(cmd: Function):
    """ Evaluate a function type BrokerCMD """
    mod = import_module(cmd.module)
    fn = getattr(mod, cmd.f_name)
    return fn(**cmd.args)


def eval_subprocess(cmd: SubProcess):
    """ Evaluate a subprocess type BrokerCMD """
    script = Path(cmd.exe_path) / cmd.p_name
    result = subprocess.run(
        [cmd.executor.to_exec(), str(script), *cmd.args], capture_output=True, text=True
    )
    if result.returncode != 0:
        return result.returncode, result.stderr
    return result.returncode, result.stdout


def eval_cmd(cmd):
    """ Evaluate a BrokerCMD

    :returns Tuple[exitcode, result<Any>]
    """
    executor = cmd.executor
    if executor == ExecutorsType.function:
        res = 0, eval_function(cmd)
    elif executor == ExecutorsType.messenger:
        res = 0, cmd.message
    elif executor.is_subprocess:
        res = eval_subprocess(cmd)
    else:
        raise ValueError('unknown message type')
    return res
