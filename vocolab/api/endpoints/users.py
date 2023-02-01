""" Routing for /users section of the API
This section handles user data
"""

import pydantic
from fastapi import (
    APIRouter, Depends, Response
)

from vocolab import out
from vocolab.core import api_lib, users_lib
from vocolab.data import model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get("/profile")
def get_profile(
        current_user: model_queries.User = Depends(api_lib.get_current_active_user)) -> users_lib.UserProfileData:
    try:
        user_data = current_user.get_profile_data()
        # re-update verification
        user_data.verified = current_user.is_verified()
        return user_data
    except pydantic.ValidationError:
        out.log.error("Failed to validate profile data")
        out.console.exception()


@router.post("/profile")
def update_profile(
        user_data: users_lib.UserProfileData,
        current_user: model_queries.User = Depends(api_lib.get_current_active_user)):
    if user_data.username != current_user.username:
        raise ValueError('Bad username specified')

    user_data.verified = current_user.is_verified()

    user_data.update()
    return Response(status_code=200)


# @router.get('{username}/submissions')
# async def submissions_list(username: str):
#     """ Return a list of all user submissions """
#     user = model_queries.User.get(by_username=username)
#     # todo fix later
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
