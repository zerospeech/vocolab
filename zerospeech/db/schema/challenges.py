from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Optional

import sqlalchemy
from pydantic import BaseModel, HttpUrl

from zerospeech.db.models.tasks import ExecutorsType

challenge_metadata = sqlalchemy.MetaData()


class Challenge(BaseModel):
    id: int
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    evaluator: Optional[int]

    class Config:
        orm_mode = True

    def is_active(self) -> bool:
        """ Checks if challenge is active """
        present = date.today()
        if self.end_date:
            return self.start_date <= present <= self.end_date and self.active
        else:
            return self.start_date <= present and self.active

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())


challenges_table = sqlalchemy.Table(
    "challenges",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("start_date", sqlalchemy.Date),
    sqlalchemy.Column("end_date", sqlalchemy.Date),
    sqlalchemy.Column("active", sqlalchemy.Boolean),
    sqlalchemy.Column("url", sqlalchemy.String),
    sqlalchemy.Column("evaluator", sqlalchemy.Integer, sqlalchemy.ForeignKey("evaluators.id"))
)


class SubmissionStatus(str, Enum):
    uploading = 'uploading'
    uploaded = 'uploaded'
    on_queue = 'on_queue'
    validating = 'validating'
    invalid = 'invalid'
    evaluating = 'evaluating'
    completed = 'completed'
    canceled = 'canceled'
    failed = 'failed'


class ChallengeSubmission(BaseModel):
    id: str
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
    sqlalchemy.Column("track_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("challenges.id")),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String)
)


class EvaluatorItem(BaseModel):
    id: int
    label: str
    executor: ExecutorsType
    host: Optional[str]
    script_path: str
    base_arguments: str

    class Config:
        orm_mode = True


evaluators_table = sqlalchemy.Table(
    "evaluators",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("host", sqlalchemy.String),
    sqlalchemy.Column("executor", sqlalchemy.String),
    sqlalchemy.Column("script_path", sqlalchemy.String),
    sqlalchemy.Column("base_arguments", sqlalchemy.String)
)


class LeaderBoard(BaseModel):
    id: Optional[int]
    challenge_id: int  # Id to linked challenge
    label: str  # Name of leaderboard
    path_to: Path  # Path to build result
    entry_file: str  # filename in submission results
    archived: bool  # is_archived
    external_entries: Path  # Location of external entries (baselines, toplines, archived)
    static_files: bool  # has static files

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())

    class Config:
        orm_mode = True


leaderboards_table = sqlalchemy.Table(
    "leaderboards",
    challenge_metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column('challenge_id', sqlalchemy.Integer, sqlalchemy.ForeignKey("challenges.id")),
    sqlalchemy.Column('label', sqlalchemy.String, unique=True),
    sqlalchemy.Column('path_to', sqlalchemy.String),
    sqlalchemy.Column('entry_file', sqlalchemy.String),
    sqlalchemy.Column('archived', sqlalchemy.Boolean),
    sqlalchemy.Column('external_entries', sqlalchemy.String),
    sqlalchemy.Column('static_files', sqlalchemy.Boolean),
)

