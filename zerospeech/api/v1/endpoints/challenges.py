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
from zerospeech.db.q import challenges as ch_queries
from zerospeech.utils import submissions as submission_utils

router = APIRouter()
logger = LogSingleton.get()
_settings = get_settings()


@router.get('/', response_model=List[models.ChallengePreview])
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active challenges """
    challenge_lst = await ch_queries.list_challenges(include_all=include_inactive)
    return [models.ChallengePreview(id=ch.id, label=ch.label, active=ch.active) for ch in challenge_lst]


@router.get('/{challenge_id}', response_model=models.ChallengesResponse, responses={404: {"model": models.Message}})
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    return await ch_queries.get_challenge(challenge_id, allow_inactive=True)


# todo test submit creation
@router.post('/{challenge_id}/submission/create', responses={404: {"model": models.Message}})
async def create_submission(
        challenge_id: int, data: models.NewSubmissionRequest,
        current_user: schema.User = Depends(api_utils.get_current_active_user)
):
    """ Create a new submission """
    challenge = await ch_queries.get_challenge(challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    # create db entry
    submission_id = await ch_queries.add_submission(ch_queries.NewSubmission(
        user_id=current_user.id,
        track_id=challenge.id
    ))
    # create disk entry
    submission_utils.make_submission_on_disk(
        submission_id, current_user.username, challenge.label, meta=data
    )
    return submission_id


@router.put("/{challenge_id}/submission/upload", response_model=models.UploadSubmissionPartResponse)
async def upload_submission(
        challenge_id: int,
        submission_id: str,
        part_name: str,
        file_date: UploadFile = File(...),
        current_user: schema.User = Depends(api_utils.get_current_active_user)
):
    challenge = await ch_queries.get_challenge(challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    is_completed, remaining = submission_utils.add_part(submission_id, part_name, file_date)
    return models.UploadSubmissionPartResponse(completed=is_completed, remaining=[n.file_name for n in remaining])
