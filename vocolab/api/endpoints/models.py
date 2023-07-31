""" Routing for /challenges section of the API
This section handles challenge data
"""

from fastapi import (
    APIRouter
)

from vocolab.data import model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get('/list')
async def get_model_list():
    """ Request the full model list """
    # todo check if extra formatting is needed
    return await model_queries.ModelIDList.get()


@router.get('/{model_id}/info')
async def get_model_info(model_id: str):
    return await model_queries.ModelID.get(model_id)


@router.get('/{model_id}/submissions/list')
async def get_model_submissions(model_id: str):
    """ Get all submissions corresponding to a model_id """
    model = await model_queries.ModelID.get(model_id)
    # todo load submissions


@router.get('/{model_id}/challenges/list')
async def get_model_submission_info(model_id: str):
    # todo: check
    pass
