from datetime import datetime, date
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, HttpUrl, AnyHttpUrl


# todo maybe move this ?
class UserData(BaseModel):
    username: str
    affiliation: str
    first_name: Optional[str]
    last_name: Optional[str]


# TODO: implement submission/challenge queries
class NewChallenge(BaseModel):
    """ Dataclass for challenge creation """
    label: str
    active: bool
    url: AnyHttpUrl
    backend: str
    start_date: date
    end_date: Optional[date]


class NewSubmission(BaseModel):
    user_id: int
    track_id: int
