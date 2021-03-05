""" Routing for /users section of the API
This section handles user data
"""

from fastapi import (
    APIRouter, Depends, Response
)

from zerospeech.api import api_utils
from zerospeech.db import schema, q as queries
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings

router = APIRouter()
logger = LogSingleton.get()
_settings = get_settings()


@router.get("/")
def get_user(current_user: schema.User = Depends(api_utils.get_current_active_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "verified": current_user.verified
    }


@router.get("/profile")
def get_profile(current_user: schema.User = Depends(api_utils.get_current_active_user)):
    return queries.users.get_user_data(current_user.username)


@router.post("/profile")
def update_profile(user_data: schema.UserData, current_user: schema.User = Depends(api_utils.get_current_active_user)):
    queries.users.update_user_data(current_user.username, data=user_data)
    return Response(status_code=200)


@router.get('/submissions')
def submissions_list(current_user: schema.User = Depends(api_utils.get_current_active_user)):
    """ Return a list of all user submissions """
    raise NotImplemented()


@router.get('/submissions/{submissions_id}')
def get_submission(submissions_id: int, current_user: schema.User = Depends(api_utils.get_current_active_user)):
    """ Return information on a submission """
    raise NotImplemented()


@router.get('/submissions/{submissions_id}/status')
def get_submission_status(submissions_id: int, current_user: schema.User = Depends(api_utils.get_current_active_user)):
    """ Return status of a submission """
    raise NotImplemented()

