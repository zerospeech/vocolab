""" Data Models used in the admin/cli functions """
from datetime import date
from typing import Optional

from pydantic import BaseModel, AnyHttpUrl

from vocolab import get_settings
from .tasks import ExecutorsType

st = get_settings()


class NewChallenge(BaseModel):
    """ Dataclass for challenge creation """
    label: str
    active: bool
    url: AnyHttpUrl
    evaluator: Optional[int]
    start_date: date
    end_date: Optional[date]
    auto_eval: bool = st.task_queue_options.AUTO_EVAL


class NewEvaluatorItem(BaseModel):
    """ Data Model used by evaluator creation process """
    label: str
    executor: ExecutorsType
    host: Optional[str]
    script_path: str
    executor_arguments: Optional[str]
