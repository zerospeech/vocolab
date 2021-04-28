from typing import Optional, Tuple, List
from pydantic import BaseModel

from zerospeech.db.schema.challenges import Challenge


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
