""" Dataclasses representing API/challenge input output data types """
from datetime import date
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from pydantic import BaseModel, HttpUrl


class ChallengePreview(BaseModel):
    """ Used as response type for root challenge list request"""
    id: int
    label: str
    active: bool


class ChallengesResponse(BaseModel):
    """ Used as response type for preview of a challenge """
    id: int
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    evaluator: Optional[int]


class SubmissionRequestFileIndexItem(BaseModel):
    """ Item used to represent a file in the file index
        used in the NewSubmissionRequest object.

        File index is used to verify correct number of files/parts have been uploaded
    """
    file_name: str
    file_size: int
    file_hash: Optional[str] = None


class NewSubmissionRequest(BaseModel):
    """ Dataclass used for input in the creation of a new submission to a challenge """
    username: str
    track_label: str
    track_id: int
    model_id: str
    filename: str
    hash: str
    multipart: bool
    has_scores: bool
    leaderboards: Dict[str, Path]
    index: Optional[List[SubmissionRequestFileIndexItem]]


class NewSubmission(BaseModel):
    """ Item used in the database to create a new submission entry """
    user_id: int
    track_id: int


class SubmissionPreview(BaseModel):
    submission_id: str
    track_label: str
    track_id: int
    status: str


class SubmissionView(BaseModel):
    submission_id: str
    user_id: int
    username: str
    track_label: str
    track_id: int
    status: str
    date: date
    evaluator_label: str
    evaluator_cmd: str
    leaderboards: List[Tuple[str, int]]


class UploadSubmissionPartResponse(BaseModel):
    """ Response type of the upload submission part method in /challenges """
    completed: bool
    remaining: List[str]
