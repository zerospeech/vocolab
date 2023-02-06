""" Routing for /challenges section of the API
This section handles challenge data
"""
from typing import List

from fastapi import (
    APIRouter
)

from vocolab.data import models, model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get('/list', response_model=List[models.api.ChallengePreview])
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active challenges """
    challenge_lst = await model_queries.ChallengeList.get(include_all=include_inactive)
    return [models.api.ChallengePreview(id=ch.id, label=ch.label, active=ch.active) for ch in challenge_lst.items]


@router.get('/{challenge_id}/info', response_model=models.api.ChallengesResponse,
            responses={404: {"model": models.api.Message}})
async def get_challenge_info(challenge_id: int):
    """ Return information of a specific challenge """
    # todo add leaderboards to challenge info
    return await model_queries.Challenge.get(challenge_id=challenge_id, allow_inactive=True)


@router.get('/{challenge_id}/submissions/list',
            responses={404: {"model": models.api.Message}})
async def get_sub_list(challenge_id: int) -> model_queries.ChallengeSubmissionList:
    """ Return information of a specific challenge """
    return await model_queries.ChallengeSubmissionList.get_from_challenge(challenge_id)


@router.get("/{challenge_id}/models/list")
async def get_models_list(challenge_id: int):
    pass


@router.get('/{challenge_id}/leaderboards/list', responses={404: {"model": models.api.Message}})
async def get_all_leaderboards(challenge_id: int) -> model_queries.LeaderboardList:
    """ Return information of a specific challenge """
    return await model_queries.LeaderboardList.get_by_challenge(challenge_id=challenge_id)
