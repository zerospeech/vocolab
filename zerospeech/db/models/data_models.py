from datetime import date
from typing import Optional, List

from pydantic import BaseModel, AnyHttpUrl

from zerospeech.db.schema.challenges import Challenge


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
    evaluator: Optional[int]
    start_date: date
    end_date: Optional[date]


class NewSubmission(BaseModel):
    user_id: int
    track_id: int


class ChallengePreview(BaseModel):
    id: int
    label: str
    active: bool


class ChallengesResponse(Challenge):
    pass


class SubmissionRequestFileIndexItem(BaseModel):
    file_name: str
    file_size: int
    file_hash: Optional[str] = None


class NewSubmissionRequest(BaseModel):
    filename: str
    hash: str
    multipart: bool
    index: Optional[List[SubmissionRequestFileIndexItem]]


class UploadSubmissionPartResponse(BaseModel):
    completed: bool
    remaining: List[str]
