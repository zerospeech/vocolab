from enum import Enum
from typing import Any, Dict, TYPE_CHECKING

from urllib3.util.url import parse_url
from pydantic import BaseModel


class ExecutorsType(str, Enum):
    python = "python"
    bash = "bash"
    sbatch = "sbatch"
    function = 'function'
    docker = "docker"


class BrokerCMD(BaseModel):
    executor: ExecutorsType
    label: str
    f_name: str
    data_path: str
    args: Dict[str, Any]

    def __init__(self, cmd: str):
        url_obj = parse_url(cmd)
        # set args
        super(BrokerCMD, self).__init__(
            executor=url_obj.scheme,
            label=url_obj.auth,
            f_name=url_obj.host,
            data_path=url_obj.path,
            args={}
        )


class Executor:

    def __init__(self):
        self._match = {
            f"{ExecutorsType.python}": Executor.python_run,
            f"{ExecutorsType.bash}": Executor.bash_run,
            f"{ExecutorsType.sbatch}": Executor.sbatch_run,
            f"{ExecutorsType.docker}": Executor.docker_run,
            f"{ExecutorsType.function}": Executor.function_run,
        }

    @staticmethod
    def python_run():
        pass

    @staticmethod
    def bash_run():
        pass

    @staticmethod
    def sbatch_run():
        pass

    @staticmethod
    def function_run():
        pass

    @staticmethod
    def docker_run():
        pass

    def run(self, cmd: BrokerCMD):
        pass

