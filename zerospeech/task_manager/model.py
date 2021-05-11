import json
import uuid
from enum import Enum
from shutil import which
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError, validator
from zerospeech import out


class QueuesNames(str, Enum):
    eval_queue = "eval_queue"
    update_queue = "update_queue"


class ExecutorsType(str, Enum):
    python = "python"
    bash = "bash"
    sbatch = "sbatch"
    function = 'function'
    docker = "docker"
    messenger = "messenger"

    def to_exec(self):
        """ Returns absolute path to executable or None"""
        if not self.is_subprocess:
            raise ValueError('function does not execute!!')
        return which(self)

    @property
    def is_subprocess(self) -> bool:
        return self in {self.python, self.bash, self.sbatch, self.docker}


class BrokerCMD(BaseModel):
    """ A Generic description of a Broker Message Object """
    executor: ExecutorsType
    label: str
    job_id: str = str(uuid.uuid4())

    @classmethod
    def from_bytes(cls, byte_cmd: bytes):
        try:
            url_obj = json.loads(str(byte_cmd.decode("utf-8")))
            exe = url_obj["executor"]
            _cls = get_broker_cmd_type(ExecutorsType(exe))
            return _cls(**url_obj)
        except (json.JSONDecodeError, ValidationError):
            out.Console.Logger.error(f"error while parsing command: {str(byte_cmd.decode('utf-8'))}")
            raise ValueError(f"command {str(byte_cmd.decode('utf-8'))} not valid!!")

    def to_str(self):
        """ Stringify the message for logging"""
        return f"{self.job_id}@{self.label}:: {self.executor} ..."


class Function(BrokerCMD):
    """ A Broker Message that contains a python function to execute """
    executor: ExecutorsType = ExecutorsType.function
    f_name: str
    args: Dict[str, Any]

    def to_str(self):
        """ Stringify the message for logging"""
        return f"{self.job_id}@{self.label}:: {self.f_name}({self.args}) --"


class SubProcess(BrokerCMD):
    """ A Broker Message that contains a subprocess task to be run"""
    p_name: str
    exe_path: str
    args: List[str]

    @validator('executor')
    def executor_must_be_subprocess(cls, v):
        assert v.is_subprocess, "executor must be a subprocess"
        return v

    def to_str(self):
        """ Stringify the message for logging"""
        return f"{self.job_id}@{self.label}:: {self.executor} {self.exe_path}/{self.p_name} {self.args} --"


class Messenger(BrokerCMD):
    """ A Broker Message that contains a simple string message """
    executor: ExecutorsType = ExecutorsType.messenger
    message: str

    def to_str(self):
        """ Stringify the message for logging"""
        return f"{self.job_id}@{self.label}:: <{self.message}>"


def get_broker_cmd_type(exe: ExecutorsType):
    """ Identify correct subclass of BrokerCMD"""

    if exe == ExecutorsType.function:
        return Function
    elif exe == ExecutorsType.messenger:
        return Messenger
    elif exe.is_subprocess:
        return SubProcess
    else:
        raise ValueError('unknown message type')
