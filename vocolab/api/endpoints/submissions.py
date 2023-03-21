""" Routing for /challenges section of the API
This section handles challenge data
"""

from fastapi import (
    APIRouter, Depends, UploadFile, File, BackgroundTasks,
    HTTPException
)

from vocolab import out, exc
from vocolab.core import api_lib, submission_lib
from vocolab.data import models, model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get("/list")
async def get_sub_list():
    # todo implement this
    pass


@router.get("/{submission_id}/info")
async def get_sub_info(submission_id: str):
    """ Returns entry of submission """
    return await model_queries.ChallengeSubmission.get(submission_id)


@router.get("/{submission_id}/scores")
async def get_submission_scores(submission_id: str):
    # todo implement this
    pass


@router.get("/{submission_id}/content/status")
async def submission_mode(submission_id: str):
    """ Returns the status of a submission """
    sub = await model_queries.ChallengeSubmission.get(submission_id)
    return dict(
        submission_id=sub.id,
        status=sub.status
    )


@router.post("/{submission_id}/content/add")
async def upload_submission(
        submission_id: str,
        part_name: str,
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        current_user: model_queries.User = Depends(api_lib.get_current_active_user),
):
    if _settings.is_locked():
        raise exc.APILockedException()

    out.console.info(f"user: {current_user.username} is uploading {file.filename}")
    submission = await model_queries.ChallengeSubmission.get(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="submission not found")

    if submission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Operation not allowed")

    try:
        sub_dir = submission_lib.SubmissionDir.load(model_id=submission.model_id, submission_id=submission.id)
    except FileNotFoundError:
        raise HTTPException(status_code=417, detail="Expected submission directory to exist")

    try:
        is_completed, remaining = sub_dir.add_content(file_name=part_name, data=file)

        if is_completed:
            # run the completion of the submission on the background
            async def bg_task():
                sub_dir.complete_upload()
                await submission.update_status(model_queries.SubmissionStatus.uploaded)

            background_tasks.add_task(bg_task)

        return models.api.UploadSubmissionPartResponse(
            completed=is_completed, remaining=[n.file_name for n in remaining]
        )
    except exc.VocoLabException as e:
        out.log.exception()
        raise e


@router.delete("/{submission_id}/remove")
async def remove_submission(submission_id: str,
                            current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    if _settings.is_locked():
        raise exc.APILockedException()

    out.log.info(f"user {current_user.username} requested that the submission {submission_id} gets deleted !")
    # todo implement delete operation
    pass
