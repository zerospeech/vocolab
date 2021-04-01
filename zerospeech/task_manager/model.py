import json
from enum import Enum
from shutil import which
from typing import Any, Dict, Optional, List, Union

from pydantic import BaseModel, ValidationError


class QueuesNames(str, Enum):
    eval_queue = "eval_queue"
    update_queue = "update_queue"


class ExecutorsType(str, Enum):
    python = "python"
    bash = "bash"
    sbatch = "sbatch"
    function = 'function'
    docker = "docker"

    def to_exec(self):
        """ Returns absolute path to executable or None"""
        if self == ExecutorsType.function:
            raise ValueError('function does not execute!!')
        return which(self)


class BrokerCMD(BaseModel):
    executor: ExecutorsType
    label: str
    job_id: str
    f_name: str
    module_path: Optional[str]
    args: Union[List[str], Dict[str, Any]]

    @classmethod
    def from_bytes(cls, byte_cmd: bytes):
        try:
            url_obj = json.loads(str(byte_cmd.decode("utf-8")))
            return cls(**url_obj)
        except (json.JSONDecodeError, ValidationError):
            print("error while parsing command")
            raise ValueError("command not valid!!")
