""" Routing for /users section of the API
This section handles user data
"""
import functools

import pydantic
from fastapi import (
    APIRouter, Depends, Response, HTTPException
)

from vocolab import out, exc
from vocolab.core import api_lib, users_lib, submission_lib
from vocolab.data import model_queries, models
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()

NonAllowedOperation = functools.partial(HTTPException, status_code=401, detail="Operation not allowed")


@router.get("/{username}/profile")
def get_profile(username: str,
                current_user: model_queries.User = Depends(
                    api_lib.get_current_active_user)) -> users_lib.UserProfileData:
    if current_user.username != username:
        raise NonAllowedOperation()

    try:
        user_data = current_user.get_profile_data()
        # re-update verification
        user_data.verified = current_user.is_verified()
        return user_data
    except pydantic.ValidationError:
        out.log.error("Failed to validate profile data")
        out.console.exception()


@router.post("/{username}/profile")
def update_profile(
        username: str,
        user_data: users_lib.UserProfileData,
        current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    if _settings.is_locked():
        raise exc.APILockedException()

    if current_user.username != username:
        raise NonAllowedOperation()

    if user_data.username != current_user.username:
        raise NonAllowedOperation()

    user_data.verified = current_user.is_verified()
    user_data.save()
    return Response(status_code=200)


@router.get("/{username}/models/list")
async def list_users_models(username: str, current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    """ Returning list of models of current user """
    if current_user.username != username:
        raise NonAllowedOperation()
    return await model_queries.ModelIDList.get_by_user(current_user.id)


@router.post("/{username}/models/create")
async def create_new_model(username: str, author_name: str, data: models.api.NewModelIdRequest,
                           current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    """ Create a new model id"""
    if _settings.is_locked():
        raise exc.APILockedException()

    if current_user.username != username:
        raise NonAllowedOperation()

    try:
        # create in DB
        model_id = await model_queries.ModelID.create(user_id=current_user.id, first_author_name=author_name, data=data)
        # create on disk
        submission_lib.ModelDir.make(model_id)
    except Exception as e:
        out.console.print(e)
        raise e

    return dict(
        model_id=model_id, user=current_user.username,
    )


@router.get("/{username}/submissions/list")
async def list_users_submissions(username: str,
                                 current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    """ List submissions created by the user """
    if current_user.username != username:
        raise NonAllowedOperation()

    return await model_queries.ChallengeSubmissionList.get_from_user(user_id=current_user.id)


@router.post("/{username}/submissions/create")
async def create_new_submission(username: str, data: models.api.NewSubmissionRequest,
                                current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    """ Create a new empty submission with the given information """
    if _settings.is_locked():
        raise exc.APILockedException()

    if current_user.username != username:
        raise NonAllowedOperation()

    new_submission = await model_queries.ChallengeSubmission.create(
        user_id=current_user.id,
        username=current_user.username,
        model_id=data.model_id,
        benchmark_id=data.benchmark_id,
        has_scores=data.has_scores,
        author_label=data.author_label
    )

    # create model_id & submission dir
    model_dir = submission_lib.ModelDir.load(data.model_id)
    model_dir.make_submission(
        submission_id=new_submission.id,
        benchmark_label=new_submission.benchmark_id,
        auto_eval=new_submission.auto_eval,
        username=current_user.username,
        leaderboard_file=data.leaderboard,
        filehash=data.hash,
        multipart=data.multipart,
        has_scores=data.has_scores,
        index=data.index
    )

    return dict(
        status=new_submission.status, benchmark=new_submission.benchmark_id,
        user=current_user.username, submission_id=new_submission.id, auto_eval=new_submission.auto_eval
    )
