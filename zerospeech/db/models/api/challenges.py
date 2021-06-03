""" Dataclasses representing API/challenge input output data types """
from typing import Optional, List

from pydantic import BaseModel

from zerospeech.db.schema.challenges import Challenge


class ChallengePreview(BaseModel):
    """ Used as response type for root challenge list request"""
    id: int
    label: str
    active: bool


class ChallengesResponse(Challenge):
    """ Used as response type for preview of a challenge """
    pass


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
    filename: str
    hash: str
    multipart: bool
    index: Optional[List[SubmissionRequestFileIndexItem]]


class NewSubmission(BaseModel):
    """ Item used in the database to create a new submission entry """
    user_id: int
    track_id: int


class UploadSubmissionPartResponse(BaseModel):
    """ Response type of the upload submission part method in /challenges """
    completed: bool
    remaining: List[str]
