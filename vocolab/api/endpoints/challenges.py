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
from vocolab.db.q import challengesQ
from vocolab.core import api_lib, submission_lib
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get('/list', response_model=List[models.api.ChallengePreview])
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active challenges """
    challenge_lst = await challengesQ.list_challenges(include_all=include_inactive)
    return [models.api.ChallengePreview(id=ch.id, label=ch.label, active=ch.active) for ch in challenge_lst]


@router.get('/{challenge_id}/info', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    return await challengesQ.get_challenge(challenge_id=challenge_id, allow_inactive=True)

@router.get('/{challenge_id}/submissions', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_sub_list(challenge_id: int):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    pass



@router.get('/{challenge_id}/leaderboards', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_all_leaderboards(challenge_id: int):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    pass



@router.get('/{challenge_id}/leaderboards/{leaderboard_id}', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_leaderboard(challenge_id: int, leaderboard_id):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    pass

