from datetime import date
from typing import Optional, Dict

from pydantic import BaseModel, HttpUrl


class ChallengePreview(BaseModel):
    id: int
    label: str
    active: bool


class ChallengesResponse(BaseModel):
    id: str
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    backend: str


