from datetime import date
from pathlib import Path
from typing import Optional, Tuple, List

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


class NewSubmissionRequest(BaseModel):
    filename: str
    location: Path
    hash: str
    multipart: bool
    index: List[Tuple[str, int, str]]


