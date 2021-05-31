from typing import Optional

from pydantic import BaseModel

from zerospeech.task_manager import ExecutorsType


class NewEvaluatorItem(BaseModel):
    label: str
    executor: ExecutorsType
    host: Optional[str]
    script_path: str
    base_arguments: Optional[str]
