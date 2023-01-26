from datetime import datetime, date
from pathlib import Path
from typing import Optional

import sqlalchemy
from pydantic import BaseModel, HttpUrl

from vocolab.db.models.tasks import ExecutorsType
from datetime import datetime
from enum import Enum
from typing import Optional

import sqlalchemy
from pydantic import BaseModel, AnyHttpUrl

challenge_metadata = sqlalchemy.MetaData()


class ModelID(BaseModel):
    """ Data representation of a Model id & its metadata"""
    id: str
    user_id: int
    created_at: datetime
    description: str
    gpu_budget: str
    train_set: str
    authors: str
    institution: str
    team: str
    paper_url: AnyHttpUrl
    code_url: AnyHttpUrl

""" 
Table indexing of model ids
"""
models_table = sqlalchemy.Table(
    "models",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, unique=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("gpu_budget", sqlalchemy.String),
    sqlalchemy.Column("train_set", sqlalchemy.String),
    sqlalchemy.Column("authors", sqlalchemy.String),
    sqlalchemy.Column("institution", sqlalchemy.String),
    sqlalchemy.Column("team", sqlalchemy.String),
    sqlalchemy.Column("paper_url", sqlalchemy.String),
    sqlalchemy.Column("code_url", sqlalchemy.String),
)

class EvaluatorItem(BaseModel):
    """ Data representation of an evaluator """
    id: int
    label: str
    executor: ExecutorsType
    host: Optional[str]
    script_path: str
    executor_arguments: str

    class Config:
        orm_mode = True

"""
Table indexing the existing evaluators
"""
evaluators_table = sqlalchemy.Table(
    "evaluators",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("host", sqlalchemy.String),
    sqlalchemy.Column("executor", sqlalchemy.String),
    sqlalchemy.Column("script_path", sqlalchemy.String),
    sqlalchemy.Column("executor_arguments", sqlalchemy.String)
)


class Challenge(BaseModel):
    """ Data representation of a challenge """
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

"""
Table used to index the existing challenges & their metadata
"""
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


class LeaderBoard(BaseModel):
    """ Data representation of a Leaderboard """
    id: Optional[int]
    challenge_id: int  # Id to linked challenge
    label: str  # Name of leaderboard
    path_to: Path  # Path to build result
    entry_file: str  # filename in submission results
    archived: bool  # is_archived
    external_entries: Optional[Path]  # Location of external entries (baselines, toplines, archived)
    static_files: bool  # has static files
    sorting_key: Optional[str]  # path to the item to use as sorting key

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())

    class Config:
        orm_mode = True


"""
Table indexing the existing leaderboards and their metadata
"""
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
    sqlalchemy.Column('sorting_key', sqlalchemy.String),
)



class SubmissionStatus(str, Enum):
    """ Definition of different states of submissions """
    # TODO: maybe add submission type (with scores...)
    uploading = 'uploading'
    uploaded = 'uploaded'
    on_queue = 'on_queue'
    validating = 'validating'  # todo verify usage
    invalid = 'invalid'
    evaluating = 'evaluating'
    completed = 'completed'
    canceled = 'canceled'
    failed = 'failed'
    no_eval = 'no_eval'
    no_auto_eval = 'no_auto_eval'
    excluded = 'excluded'

    @classmethod
    def get_values(cls):
        return [el.value for el in cls]  # noqa enum has attr values



class ChallengeSubmission(BaseModel):
    """ Data representation of a submission to a challenge """
    id: str
    user_id: int
    track_id: int
    submit_date: datetime
    status: SubmissionStatus
    auto_eval: bool
    evaluator_id: Optional[int]
    author_label: Optional[str] = None

    class Config:
        orm_mode = True


""" 
Table entry indexing submissions to challenges
"""
submissions_table = sqlalchemy.Table(
    "challenge_submissions",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, unique=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer),
    sqlalchemy.Column("track_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("challenges.id")),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("auto_eval", sqlalchemy.Boolean),
    sqlalchemy.Column("evaluator_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("evaluators.id")),
    sqlalchemy.Column("author_label", sqlalchemy.String)
)


class LeaderboardEntry:
    """ Data representation of a leaderboard entry """
    id: Optional[int]
    entry_path: Path
    model_id: str
    submission_id: str
    leaderboard_id: int
    submitted_at: datetime


""" Table indexing all leaderboard entries and their location  (as stores json files)"""
leaderboard_entry_table = sqlalchemy.Table(
    "leaderboard_entries",
    challenge_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True, autoincrement=True),
    sqlalchemy.Column("entry_path", sqlalchemy.String),
    sqlalchemy.Column("model_id", sqlalchemy.String, sqlalchemy.ForeignKey("leaderboards.id")),
    sqlalchemy.Column("submission_id", sqlalchemy.String, sqlalchemy.ForeignKey("challenge_submissions.id")),
    sqlalchemy.Column("leaderboard_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("models.id")),
    sqlalchemy.Column("submitted_at", sqlalchemy.String)
)
