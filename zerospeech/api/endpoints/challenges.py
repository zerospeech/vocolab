""" Routing for /challenges section of the API
This section handles challenge data
"""
from typing import List

from fastapi import (
    APIRouter, Depends, UploadFile, File, BackgroundTasks
)

from zerospeech import out
from zerospeech.api import api_utils
from zerospeech.db import schema, models
from zerospeech.db.q import challengesQ
from zerospeech.settings import get_settings
from zerospeech.utils import submissions

router = APIRouter()
_settings = get_settings()


@router.get('/', response_model=List[models.ChallengePreview])
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active challenges """
    challenge_lst = await challengesQ.list_challenges(include_all=include_inactive)
    return [models.ChallengePreview(id=ch.id, label=ch.label, active=ch.active) for ch in challenge_lst]


@router.get('/{challenge_id}', response_model=models.ChallengesResponse, responses={404: {"model": models.Message}})
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    return await challengesQ.get_challenge(challenge_id=challenge_id, allow_inactive=True)


@router.get('/{challenge_id}/leaderboard',  responses={404: {"model": models.Message}})
async def get_challenge_leaderboard(challenge_id: int):
    """ Return leaderboard of a specific challenge """
    # todo check into GraphQL maybe ?
    raise NotImplemented('Leaderboard not implemented')


# todo test submit creation
@router.post('/{challenge_id}/submission/create', responses={404: {"model": models.Message}})
async def create_submission(
        challenge_id: int, data: models.NewSubmissionRequest,
        current_user: schema.User = Depends(api_utils.get_current_active_user)
):
    """ Create a new submission """
    challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    # create db entry
    submission_id = await challengesQ.add_submission(new_submission=models.NewSubmission(
        user_id=current_user.id,
        track_id=challenge.id
    ))
    # create disk entry
    submissions.manipulate.make_submission_on_disk(
        submission_id, current_user.username, challenge.label, meta=data
    )
    return submission_id


@router.put("/{challenge_id}/submission/upload", response_model=models.UploadSubmissionPartResponse)
async def upload_submission(
        challenge_id: int,
        submission_id: str,
        part_name: str,
        background_tasks: BackgroundTasks,
        file_data: UploadFile = File(...),
        current_user: schema.User = Depends(api_utils.get_current_active_user),
):
    out.Console.info(f"user: {current_user.username}")
    challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    is_completed, remaining = submissions.manipulate.add_part(submission_id, part_name, file_data)

    if is_completed:
        # run the completion of the submission on the background
        background_tasks.add_task(submissions.manipulate.complete_submission, submission_id)

    return models.UploadSubmissionPartResponse(completed=is_completed, remaining=[n.file_name for n in remaining])
