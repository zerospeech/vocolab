""" Module that evaluates BrokerCMDs """
import subprocess
from importlib import import_module
from pathlib import Path

from zerospeech.task_manager import (
    ExecutorsType,
    Function, SubProcess,
    Messenger
)










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
