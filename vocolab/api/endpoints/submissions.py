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
    pass


@router.get("/{submission_id}/info")
async def get_sub_info(submission_id: str):
    pass


@router.get("/{submission_id}/scores")
async def get_submission_scores(submission_id: str):
    pass


@router.get("/{submission_id}/content/mode")
async def submission_mode(submission_id: str):
    """
    Should return the submission mode
    open: allows adding content
    closed: content has completed being add
    """
    pass


@router.get("/{submission_id}/content/reset")
async def reset_submission(submission_id: str):
    """
    remove content of submission & allow new content to be added
    """
    pass


@router.post('{submission_id}/content/init')
async def upload_manifest(submission_id: str,
                          current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    # todo: initialise manifest before upload
    # create submission dir
    # add manifest and promise of files
    pass


@router.put("/{submission_id}/content/add", response_model=models.api.UploadSubmissionPartResponse)
async def upload_submission(
        submission_id: str,
        part_name: str,
        background_tasks: BackgroundTasks,
        file_data: UploadFile = File(...),
        current_user: model_queries.User = Depends(api_lib.get_current_active_user),
):
    out.console.info(f"user: {current_user.username}")
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
        is_completed, remaining = sub_dir.add_content(file_name=part_name, data=file_data)

        if is_completed:
            # todo: fix completed actions
            # run the completion of the submission on the background
            background_tasks.add_task(submission_lib.complete_submission, submission_id, with_eval=True)

        return models.api.UploadSubmissionPartResponse(
            completed=is_completed, remaining=[n.file_name for n in remaining]
        )
    except exc.VocoLabException as e:
        out.log.exception()
        raise e


@router.delete("/{submission_id}/remove")
async def remove_submission(submission_id: str,
                            current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    pass
