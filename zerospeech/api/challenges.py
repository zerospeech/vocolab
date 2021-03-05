""" Routing for /challenges section of the API
This section handles challenge data
"""
from datetime import date
from typing import List, Optional, Dict

from pydantic import BaseModel, HttpUrl
from fastapi import (
    FastAPI, Depends, UploadFile, File
)


from zerospeech.db import schema
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings
from zerospeech.api import api_utils, auth


challenge_app = FastAPI()
logger = LogSingleton.get()
_settings = get_settings()


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


@challenge_app.get('/', response_model=List[ChallengesResponse])
async def get_challenge_list():
    """ Return a list of all active challenges """
    raise NotImplemented()


@challenge_app.get('/{challenge_id}', response_model=ChallengesResponse)
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    raise NotImplemented()


@challenge_app.put('/{challenge_id}/submit')
async def submit_to_challenge(
        challenge_id: int, submission: SubmissionRequest,
        current_user: schema.User = Depends(auth.get_current_active_user), file: UploadFile = File(...)
):
    """ Create a new submission """
    raise NotImplemented()


# Set docs parameters
api_utils.set_documentation_params(challenge_app)
