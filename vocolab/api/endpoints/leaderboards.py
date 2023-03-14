""" Routing for /leaderboards section of the API
This section handles leaderboard data
"""

from fastapi import (
    APIRouter
)

from vocolab.data import models, model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get("/list")
async def get_list():
    pass


@router.get('{leaderboard_id}/info')
async def get_leaderboard_info(leaderboard_id: str):
    """ Return information of a specific challenge """
    return await model_queries.Leaderboard.get(leaderboard_id=leaderboard_id)


@router.get("{leaderboard_id}/json")
async def get_leaderboard_entries_as_json(leaderboard_id: int):
    pass
    # try:
    #     leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    # except ValueError:
    #     raise exc.ResourceRequestedNotFound(f'No leaderboard with id {leaderboard_id}')
    #
    # if leaderboard.path_to.is_file():
    #     return api_lib.file2dict(leaderboard.path_to)
    # else:
    #     return dict(
    #         updatedOn=datetime.now().isoformat(),
    #         data=[]
    #     )


@router.get("{leaderboard_id}/csv")
async def get_leaderboard_entries_as_csv(leaderboard_id: int):
    pass


@router.get("{leaderboard_id}/entry/{entry_id}")
async def get_leaderboard_entry(leaderboard_id: int, entry_id: str):
    pass
