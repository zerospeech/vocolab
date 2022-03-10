from datetime import datetime

import json
import uuid
from enum import Enum
from shutil import which
from typing import List, Union, Optional

from pydantic import BaseModel, ValidationError, Field, root_validator

from zerospeech import out


class QueuesNames(str, Enum):
    eval_queue = "eval_queue"
    update_queue = "update_queue"


class BrokerMessage(BaseModel):
    """ A Generic description of a Broker Message Object """
    message_type: Optional[str]
    label: str
    job_id: str = str(uuid.uuid4())
    timestamp: datetime = Field(default_factory=datetime.now)

    @root_validator(pre=True)
    def set_message_type(cls, values):
        values["message_type"] = str(cls.__name__)
        return values

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
    executor_args: List[str]
    cmd_args: List[str]

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> " \
               f"{self.submission_id}@{self.label}:: " \
               f"{self.executor} {self.bin_path}/{self.script_name} {self.cmd_args} --"


class UpdateType(str, Enum):
    evaluation_complete = "evaluation_complete"
    evaluation_failed = "evaluation_failed"
    evaluation_canceled = "evaluation_canceled"
    evaluation_undefined = "evaluation_undefined"


class SubmissionUpdateMessage(BrokerMessage):
    """ A Broker Message that contains a python function to execute """
    submission_id: str
    updateType: UpdateType
    hostname: str

    def __repr__(self):
        """ Stringify the message for logging"""
        return f"{self.job_id} >> " \
               f"{self.submission_id}@{self.label}:: " \
               f"{self.updateType}@{self.hostname}--"


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

        message_type = url_obj.get('message_type', None)

        # if type is not specified raise error
        if message_type is None:
            out.log.error(f"Message does not specify type: {str(byte_msg.decode('utf-8'))}")
            raise ValueError(f"Message does not specify type: {str(byte_msg.decode('utf-8'))}")

        # try and match type with known types
        if message_type == "SubmissionEvaluationMessage":
            return SubmissionEvaluationMessage(**url_obj)
        elif message_type == "SubmissionUpdateMessage":
            return SubmissionUpdateMessage(**url_obj)
        elif message_type == "SimpleLogMessage":
            return SimpleLogMessage(**url_obj)
        elif message_type == "BrokerMessage":
            return BrokerMessage(**url_obj)

        # raise error if matching failed
        out.log.error(f"Unknown message type: {str(byte_msg.decode('utf-8'))}")
        raise ValueError(f"Unknown message type {str(byte_msg.decode('utf-8'))}")

    except (json.JSONDecodeError, ValidationError):
        out.log.error(f"error while parsing command: {str(byte_msg.decode('utf-8'))}")
        raise ValueError(f"command {str(byte_msg.decode('utf-8'))} not valid!!")
