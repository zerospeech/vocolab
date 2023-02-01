""" Routing for /challenges section of the API
This section handles challenge data
"""

from fastapi import (
    APIRouter, Depends, UploadFile, File, BackgroundTasks
)

from vocolab import out, exc
from vocolab.core import api_lib, submission_lib
from vocolab.data import models, model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.post('/create')
async def create_new_model(
        first_author_name: str,
        current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    """ Route to create a new model entry """
    # todo: add data in request body & check if it works correctly
    return await model_queries.ModelID.create(first_author_name, ...)


@router.get('/list')
async def get_model_list():
    """ Request the full model list """
    # todo check if extra formatting is needed
    return await model_queries.ModelIDList.get()


@router.get('/{model_id}/info')
async def get_model_info(model_id: str):
    return await model_queries.ModelID.get(model_id)


@router.get('/{model_id}/submissions/list')
async def get_model_submissions(model_id: str):
    """ Get all submissions corresponding to a model_id """
    model = await model_queries.ModelID.get(model_id)
    return await model.get_submissions()


@router.get('/{model_id}/submissions/{submission_id}/info')
async def get_model_submission_info():
    # todo: check
    pass


@router.get('/{model_id}/submissions/{submission_id}/leaderboard-entries')
async def get_model_submission_leaderboard_entries():
    # todo: check
    pass


# todo: update submission process
@router.post('/{model_id}/submissions/create/', responses={404: {"model": models.api.Message}})
async def create_submission(
        model_id: str, challenge_id: int,
        data: models.api.NewSubmissionRequest,
        current_user: schema.User = Depends(api_lib.get_current_active_user)
):
    """ Create a new submission """
    # todo fetch model_id

    challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
    if challenge is None:
        return ValueError(f'challenge {challenge_id} not found or inactive')

    # create db entry
    # todo check submission table data
    submission_id = await challengesQ.add_submission(new_submission=models.api.NewSubmission(
        user_id=current_user.id,
        track_id=challenge.id,
    ), evaluator_id=challenge.evaluator)

    # create disk entry
    model_dir = submission_lib.ModelDir.load(data.model_id)
    model_dir.make_submission(
        submission_id=submission_id,
        challenge_id=challenge_id,
        challenge_label=challenge.label,
        auto_eval=...,
        request_meta=data
    )

    return submission_id


# todo update
@router.put("/{model_id}/submission/{submission_id}/upload", response_model=models.api.UploadSubmissionPartResponse)
async def upload_submission(
        model_id: str,
        submission_id: str,
        challenge_id: int,
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
        is_completed, remaining = submission_lib.add_part(submission_id, part_name, file_data)

        if is_completed:
            # run the completion of the submission on the background
            background_tasks.add_task(submission_lib.complete_submission, submission_id, with_eval=True)

        return models.api.UploadSubmissionPartResponse(
            completed=is_completed, remaining=[n.file_name for n in remaining]
        )
    except exc.VocoLabException as e:
        out.log.exception()
        raise e
