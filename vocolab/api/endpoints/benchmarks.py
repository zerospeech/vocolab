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


@router.get('/list')
async def get_challenge_list(include_inactive: bool = False):
    """ Return a list of all active benchmarks """
    return await model_queries.BenchmarkList.get(include_all=include_inactive)


@router.get('/{benchmark_id}/info')
async def get_challenge_info(benchmark_id: str):
    """ Return information of a specific benchmark """
    return await model_queries.Benchmark.get(benchmark_id=benchmark_id, allow_inactive=True)


@router.get('/{benchmark_id}/submissions/list',
            responses={404: {"model": models.api.Message}})
async def get_sub_list(benchmark_id: str) -> model_queries.ChallengeSubmissionList:
    """ Return information of a specific benchmark """
    return await model_queries.ChallengeSubmissionList.get_from_challenge(benchmark_id)


@router.get("/{benchmark_id}/models/list")
async def get_models_list(benchmark_id: str):
    pass


@router.get('/{benchmark_id}/leaderboards/list', responses={404: {"model": models.api.Message}})
async def get_all_leaderboards(benchmark_id: str) -> model_queries.LeaderboardList:
    """ Return information of a specific challenge """
    return await model_queries.LeaderboardList.get_by_challenge(benchmark_id=benchmark_id)
