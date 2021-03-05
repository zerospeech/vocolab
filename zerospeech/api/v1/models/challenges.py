from datetime import date
from typing import Optional, Dict

from pydantic import BaseModel, HttpUrl


class ChallengesResponse(BaseModel):
    id: str
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    backend: str


class SubmissionRequest(BaseModel):
    author_label: str
    affiliation: str
    associates: str
    open_source: bool
    submission_params: Dict

