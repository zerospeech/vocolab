""" Routing for /challenges section of the API
This section handles challenge data
"""
from typing import List

from fastapi import (
    APIRouter, Depends, UploadFile, File
)


from zerospeech.db import schema
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings
from zerospeech.api import api_utils
from zerospeech.api.v1 import models

router = APIRouter()
logger = LogSingleton.get()
_settings = get_settings()


@router.get('/', response_model=List[models.ChallengesResponse])
async def get_challenge_list():
    """ Return a list of all active challenges """
    raise NotImplemented()


@router.get('/{challenge_id}', response_model=models.ChallengesResponse)
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    raise NotImplemented()


@router.put('/{challenge_id}/submit')
async def submit_to_challenge(
        challenge_id: int, submission: models.SubmissionRequest,
        current_user: schema.User = Depends(api_utils.get_current_active_user), file: UploadFile = File(...)
):
    """ Create a new submission """
    raise NotImplemented()

