""" Data Models used in the admin/cli functions """
from datetime import date
from typing import Optional

from pydantic import BaseModel, AnyHttpUrl

from zerospeech.task_manager import ExecutorsType


class NewChallenge(BaseModel):
    """ Dataclass for challenge creation """
    label: str
    active: bool
    url: AnyHttpUrl
    evaluator: Optional[int]
    start_date: date
    end_date: Optional[date]


class NewEvaluatorItem(BaseModel):
    """ Data Model used by evaluator creation process """
    label: str
    executor: ExecutorsType
    host: Optional[str]
    script_path: str
    base_arguments: Optional[str]
