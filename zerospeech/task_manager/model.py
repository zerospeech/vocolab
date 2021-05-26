import json
import uuid
from enum import Enum
from shutil import which
from typing import List, Union

from pydantic import BaseModel, ValidationError

from zerospeech import out


class QueuesNames(str, Enum):
    eval_queue = "eval_queue"
    update_queue = "update_queue"


class BrokerMessage(BaseModel):
    """ A Generic description of a Broker Message Object """
    label: str
    job_id: str = str(uuid.uuid4())

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> {self.label}"


class ExecutorsType(str, Enum):
    python = "python"
    bash = "bash"
    sbatch = "sbatch"
    docker = "docker"

    def to_exec(self):
        """ Returns absolute path to executable or None"""
        return which(self)


class SubmissionEvaluationMessage(BrokerMessage):
    """ A Broker Message that contains a subprocess task to be run"""
    executor: ExecutorsType = ExecutorsType.bash
    submission_id: str
    bin_path: str
    script_name: str
    args: List[str]

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> " \
               f"{self.submission_id}@{self.label}:: " \
               f"{self.executor} {self.bin_path}/{self.script_name} {self.args} --"


class UpdateType(str, Enum):
    evaluation_complete = "evaluation_complete"


class SubmissionUpdateMessage(BrokerMessage):
    """ A Broker Message that contains a python function to execute """
    submission_id: str
    updateType: UpdateType
    success: bool

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> " \
               f"{self.submission_id}@{self.label}:: " \
               f"{self.updateType}(success: {self.success}) --"


class SimpleLogMessage(BrokerMessage):
    """ A Broker Message that contains a simple string message """
    message: str

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> {self.label}:: {self.message}"


def message_from_bytes(byte_msg: bytes) -> Union[BrokerMessage,
                                                 SubmissionEvaluationMessage,
                                                 SubmissionUpdateMessage, SimpleLogMessage]:
    """ Convert a bytes object to the correct corresponding Message object """

    try:
        url_obj = json.loads(str(byte_msg.decode("utf-8")))

        if list(url_obj.keys()) == list(BrokerMessage.__fields__.keys()):
            return BrokerMessage(**url_obj)
        elif list(url_obj.keys()) == list(SubmissionEvaluationMessage.__fields__.keys()):
            return SubmissionEvaluationMessage(**url_obj)
        elif list(url_obj.keys()) == list(SubmissionUpdateMessage.__fields__.keys()):
            return SubmissionUpdateMessage(**url_obj)
        elif list(url_obj.keys()) == list(SimpleLogMessage.__fields__.keys()):
            return SimpleLogMessage(**url_obj)
        else:
            out.Console.Logger.error(f"Unknown message type: {str(byte_msg.decode('utf-8'))}")
            raise ValueError(f"Unknown message type {str(byte_msg.decode('utf-8'))}")

    except (json.JSONDecodeError, ValidationError):
        out.Console.Logger.error(f"error while parsing command: {str(byte_msg.decode('utf-8'))}")
        raise ValueError(f"command {str(byte_msg.decode('utf-8'))} not valid!!")
