from datetime import datetime, date
from pathlib import Path
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


class ChallengeSubmissions(BaseModel):
    id: int
    user_id: int
    track_id: int
    submit_date: datetime
    status: str
    file: Path

    class Config:
        orm_mode = True


users_table = sqlalchemy.Table(
    "challenge_submissions",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("track_id", sqlalchemy.Integer),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("file", sqlalchemy.String),
    sqlalchemy.Column("backend", sqlalchemy.String)
)
