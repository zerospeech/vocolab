""" Routing for /users section of the API
This section handles user data
"""
import functools

import pydantic
from fastapi import (
    APIRouter, Depends, Response, HTTPException
)

from vocolab import out
from vocolab.core import api_lib, users_lib
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
    print("WRF")
    if current_user.username != username:
        raise NonAllowedOperation()

    # create & return the new model_id
    try:
        model_id = await model_queries.ModelID.create(user_id=current_user.id, first_author_name=author_name, data=data)
    except Exception as e:
        out.console.print(e)
        raise e

    return model_id


@router.get("/{username}/submissions/list")
async def list_users_submissions(username: str,
                                 current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    if current_user.username != username:
        raise NonAllowedOperation()

    items = await model_queries.ChallengeSubmissionList.get_from_user(user_id=current_user.id)
    return items


@router.post("/{username}/submissions/create")
async def create_new_submission(username: str, data: models.api.NewSubmissionRequest,
                                current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    if current_user.username != username:
        raise NonAllowedOperation()

    new_submission = await model_queries.ChallengeSubmission.create(
        user_id=current_user.id,
        username=current_user.username,
        model_id=data.model_id,
        benchmark_id=data.benchmark_id
    )

    # todo: create file structure
    # todo extract leaderboards

    return new_submission.id


# todo: update submission process
# @router.post('/{model_id}/submissions/create/', responses={404: {"model": models.api.Message}})
# async def create_submission(
#         model_id: str, challenge_id: int,
#         data: models.api.NewSubmissionRequest,
#         current_user: schema.User = Depends(api_lib.get_current_active_user)
# ):
#     """ Create a new submission """
#
#     challenge = await challengesQ.get_challenge(challenge_id=challenge_id)
#     if challenge is None:
#         return ValueError('challenge {challenge_id} not found or inactive')
#
#     # create db entry
#     submission_id = await challengesQ.add_submission(new_submission=models.api.NewSubmission(
#         user_id=current_user.id,
#         track_id=challenge.id,
#     ), evaluator_id=challenge.evaluator)
#
#     # create disk entry
#     model_dir = submission_lib.ModelDir.load(data.model_id)
#     model_dir.make_submission(
#         submission_id=submission_id,
#         challenge_id=challenge_id,
#         challenge_label=challenge.label,
#         auto_eval=...,
#         request_meta=data
#     )
#
#     return submission_id
#
#
# @router.get('{username}/submissions')
# async def submissions_list(username: str):
#     """ Return a list of all user submissions """
#     user = model_queries.User.get(by_username=username)
#     submissions = await challengesQ.get_user_submissions(user_id=current_user.id)
#     submissions = [
#         models.api.SubmissionPreview(
#             submission_id=s.id,
#             track_id=s.track_id,
#             track_label=(await challengesQ.get_challenge(challenge_id=s.track_id)).label,
#             status=s.status
#         )
#         for s in submissions
#     ]
#
#     data = {}
#     for sub in submissions:
#         if sub.track_label in data.keys():
#             data[sub.track_label].append(sub)
#         else:
#             data[sub.track_label] = [sub]
#
#     return data
#
#
#
# @router.get('{username}//submissions/tracks/{track_id}')
# async def submissions_list_by_track(
#         track_id: int, current_user: schema.User = Depends(api_lib.get_current_active_user)):
#     """ Return a list of all user submissions """
#     track = await challengesQ.get_challenge(challenge_id=track_id)
#     submissions = await challengesQ.get_user_submissions(user_id=current_user.id)
#
#     return [
#         models.api.SubmissionPreview(
#             submission_id=s.id,
#             track_id=s.track_id,
#             track_label=track.label,
#             status=s.status
#         )
#         for s in submissions if s.track_id == track.id
#     ]
#
#
# @router.get('/submissions/{submissions_id}')
# async def get_submission(submissions_id: str, current_user: schema.User = Depends(api_lib.get_current_active_user)):
#     """ Return information on a submission """
#     submission = await challengesQ.get_submission(by_id=submissions_id)
#     if submission.user_id != current_user.id:
#         raise exc.AccessError("current user is not allowed to preview this submission !",
#                               status=exc.http_status.HTTP_403_FORBIDDEN)
#
#     track = await challengesQ.get_challenge(challenge_id=submission.track_id)
#     leaderboards = await leaderboardQ.get_leaderboards(by_challenge_id=submission.track_id)
#
#     if submission.evaluator_id is not None:
#         evaluator = await challengesQ.get_evaluator(by_id=submission.evaluator_id)
#         evaluator_cmd = f"{evaluator.executor} {evaluator.script_path} {evaluator.executor_arguments.replace(';', ' ')}"
#         evaluator_label = evaluator.label
#     else:
#         evaluator_cmd = ""
#         evaluator_label = ""
#
#     return models.api.SubmissionView(
#         submission_id=submission.id,
#         user_id=current_user.id,
#         username=current_user.username,
#         track_label=track.label,
#         track_id=track.id,
#         status=submission.status,
#         date=submission.submit_date,
#         evaluator_cmd=evaluator_cmd,
#         evaluator_label=evaluator_label,
#         leaderboards=[(ld.label, ld.id) for ld in leaderboards]
#     )
#
#
# @router.get('/submissions/{submissions_id}/status')
# async def get_submission_status(
#         submissions_id: str, current_user: schema.User = Depends(api_lib.get_current_active_user)):
#     """ Return status of a submission """
#     submission = await challengesQ.get_submission(by_id=submissions_id)
#     if submission.user_id != current_user.id:
#         raise exc.AccessError("current user is not allowed to preview this submission !",
#                               status=exc.http_status.HTTP_403_FORBIDDEN)
#
#     return submission.status
#
#
# @router.get('/submissions/{submissions_id}/log')
# async def get_submission_status(
#         submissions_id: str, current_user: schema.User = Depends(api_lib.get_current_active_user)):
#     """ Return status of a submission """
#     submission = await challengesQ.get_submission(by_id=submissions_id)
#     if submission.user_id != current_user.id:
#         raise exc.AccessError("current user is not allowed to preview this submission !",
#                               status=exc.http_status.HTTP_403_FORBIDDEN)
#
#     log = submission_lib.SubmissionLogger(submissions_id)
#     return log.get_text()
#
#
# @router.get('/submissions/{submissions_id}/scores')
# async def get_user_results(submissions_id: str, current_user: schema.User = Depends(api_lib.get_current_active_user)):
#     """ Return status of a submission """
#     submission = await challengesQ.get_submission(by_id=submissions_id)
#     if submission.user_id != current_user.id:
#         raise exc.AccessError("current user is not allowed to preview this submission !",
#                               status=exc.http_status.HTTP_403_FORBIDDEN)
#     sub_location = submission_lib.get_submission_dir(submission_id=submission.id)
#
#     leaderboards = await leaderboardQ.get_leaderboards(by_challenge_id=submission.track_id)
#     result = {}
#     for ld in leaderboards:
#         ld_file = sub_location / ld.entry_file
#         if ld_file.is_file():
#             result[ld.label] = api_lib.file2dict(ld_file)
#
#     return result
