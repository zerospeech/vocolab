""" Routing for /users section of the API
This section handles user data
"""
from datetime import date
from typing import List, Optional, Dict

from pydantic import BaseModel, HttpUrl
from fastapi import (
    FastAPI, Depends, Response
)


from zerospeech.db import schema, q as queries
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings
from zerospeech.api import api_utils, auth


users_app = FastAPI()
logger = LogSingleton.get()
_settings = get_settings()


@users_app.get("/")
def get_user(current_user: schema.User = Depends(auth.get_current_active_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "verified": current_user.verified
    }


@users_app.get("/profile")
def get_profile(current_user: schema.User = Depends(auth.get_current_active_user)):
    return queries.users.get_user_data(current_user.username)


@users_app.post("/profile")
def update_profile(user_data: schema.UserData, current_user: schema.User = Depends(auth.get_current_active_user)):
    queries.users.update_user_data(current_user.username, data=user_data)
    return Response(status_code=200)


@users_app.get('/submissions')
def submissions_list(current_user: schema.User = Depends(auth.get_current_active_user)):
    """ Return a list of all user submissions """
    raise NotImplemented()


@users_app.get('/submissions/{submissions_id}')
def get_submission(submissions_id: int, current_user: schema.User = Depends(auth.get_current_active_user)):
    """ Return information on a submission """
    raise NotImplemented()


@users_app.get('/submissions/{submissions_id}/status')
def get_submission_status(submissions_id: int, current_user: schema.User = Depends(auth.get_current_active_user)):
    """ Return status of a submission """
    raise NotImplemented()


# Set docs parameters
api_utils.set_documentation_params(users_app)
