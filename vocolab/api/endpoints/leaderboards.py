""" Routing for /leaderboards section of the API
This section handles leaderboard data
"""
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter
)
from vocolab import exc
from vocolab.data import models, model_queries
from vocolab.core import api_lib
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get('/', response_model=List[models.api.LeaderboardPublicView], responses={404: {"model": models.api.Message}})
async def get_leaderboards_list():
    """ Returns the list of leaderboards """
    lst = await leaderboardQ.list_leaderboards()

    # strip non public values from entries
    return [
        models.api.LeaderboardPublicView(
            id=ld.id,
            challenge_id=ld.challenge_id,
            label=ld.label,
            entry_file=ld.entry_file,
            archived=ld.archived,
            static_files=ld.static_files
        )
        for ld in lst
    ]


@router.get('/{leaderboard_id}/json',  responses={404: {"model": models.api.Message}})
async def get_leaderboard_data(leaderboard_id: int):
    """ Return leaderboard of a specific challenge """
    try:
        leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    except ValueError:
        raise exc.ResourceRequestedNotFound(f'No leaderboard with id {leaderboard_id}')

    if leaderboard.path_to.is_file():
        return api_lib.file2dict(leaderboard.path_to)
    else:
        return dict(
            updatedOn=datetime.now().isoformat(),
            data=[]
        )
