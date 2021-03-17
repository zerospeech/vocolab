from datetime import datetime, date
from enum import Enum
from typing import Optional

import sqlalchemy
from pydantic import BaseModel, HttpUrl

challenge_metadata = sqlalchemy.MetaData()


class Challenge(BaseModel):
    id: int
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    backend: str

    class Config:
        orm_mode = True

    def is_active(self) -> bool:
        """ Checks if challenge is active """
        present = date.today()
        return self.end_date > present and self.active


challenges_table = sqlalchemy.Table(
    "challenges",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("start_date", sqlalchemy.Date),
    sqlalchemy.Column("end_date", sqlalchemy.Date),
    sqlalchemy.Column("active", sqlalchemy.Boolean),
    sqlalchemy.Column("url", sqlalchemy.String),
    sqlalchemy.Column("backend", sqlalchemy.String)
)


class SubmissionStatus(str, Enum):
    uploading = 'uploading'
    on_queue = 'on_queue'
    validating = 'validating'
    invalid = 'invalid'
    evaluating = 'evaluating'
    completed = 'completed'
    failed = 'failed'


class ChallengeSubmissions(BaseModel):
    id: int
    user_id: int
    track_id: int
    submit_date: datetime
    status: SubmissionStatus

    class Config:
        orm_mode = True


submissions_table = sqlalchemy.Table(
    "challenge_submissions",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, unique=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("track_id", sqlalchemy.Integer),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String)
)
