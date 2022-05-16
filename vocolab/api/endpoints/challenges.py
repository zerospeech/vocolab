""" Routing for /challenges section of the API
This section handles challenge data
"""
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter, Depends, UploadFile, File, BackgroundTasks
)

from vocolab import out, exc
from vocolab.db import schema, models
from vocolab.db.q import challengesQ, leaderboardQ
from vocolab.lib import api_lib, submissions_lib
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get('/', response_model=List[models.api.ChallengePreview])
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active challenges """
    challenge_lst = await challengesQ.list_challenges(include_all=include_inactive)
    return [models.api.ChallengePreview(id=ch.id, label=ch.label, active=ch.active) for ch in challenge_lst]


@router.get('/{challenge_id}', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    return await challengesQ.get_challenge(challenge_id=challenge_id, allow_inactive=True)


# todo test submit creation
@router.post('/{challenge_id}/submission/create', responses={404: {"model": models.api.Message}})
async def create_submission(
        challenge_id: int, data: models.api.NewSubmissionRequest,
        current_user: schema.User = Depends(api_lib.get_current_active_user)
):
    """ Create a new submission """
    challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    # create db entry
    submission_id = await challengesQ.add_submission(new_submission=models.api.NewSubmission(
        user_id=current_user.id,
        track_id=challenge.id,
    ), evaluator_id=challenge.evaluator)
    # create disk entry
    submissions_lib.make_submission_on_disk(
        submission_id, current_user.username, challenge.label, meta=data
    )
    return submission_id


@router.put("/{challenge_id}/submission/upload", response_model=models.api.UploadSubmissionPartResponse)
async def upload_submission(
        challenge_id: int,
        submission_id: str,
        part_name: str,
        background_tasks: BackgroundTasks,
        file_data: UploadFile = File(...),
        current_user: schema.User = Depends(api_lib.get_current_active_user),
):
    out.console.info(f"user: {current_user.username}")
    challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')
    try:
        is_completed, remaining = submissions_lib.add_part(submission_id, part_name, file_data)

        if is_completed:
            # run the completion of the submission on the background
            background_tasks.add_task(submissions_lib.complete_submission, submission_id, with_eval=True)

        return models.api.UploadSubmissionPartResponse(
            completed=is_completed, remaining=[n.file_name for n in remaining]
        )
    except exc.ZerospeechException as e:
        out.log.exception()
        raise e
