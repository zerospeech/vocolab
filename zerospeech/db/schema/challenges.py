from datetime import datetime
from pathlib import Path

import sqlalchemy
from pydantic import BaseModel, HttpUrl

users_metadata = sqlalchemy.MetaData()


class Challenge(BaseModel):
    id: int
    label: str
    start_date: datetime
    end_date: datetime
    active: bool
    url: HttpUrl
    backend: str

    class Config:
        orm_mode = True


challenges_table = sqlalchemy.Table(
    "challenges",
    users_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("start_date", sqlalchemy.DateTime),
    sqlalchemy.Column("end_date", sqlalchemy.DateTime),
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
    users_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("track_id", sqlalchemy.Integer),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("file", sqlalchemy.String),
    sqlalchemy.Column("backend", sqlalchemy.String)
)
