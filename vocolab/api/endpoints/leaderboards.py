""" Routing for /leaderboards section of the API
This section handles leaderboard data
"""
import tempfile
from pathlib import Path

from fastapi import (
    APIRouter, BackgroundTasks
)
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from vocolab_ext import leaderboards as leaderboard_ext

from vocolab.data import model_queries
from vocolab.settings import get_settings

router = APIRouter()
_settings = get_settings()


@router.get("/list")
async def get_list() -> list[str]:
    ld_list = await model_queries.LeaderboardList.get_all()
    return [
        ld.label for ld in ld_list
    ]


@router.get('{leaderboard}/info')
async def get_leaderboard_info(leaderboard: str):
    """ Return information of a specific challenge """
    return await model_queries.Leaderboard.get(leaderboard_id=leaderboard)


@router.get("{leaderboard}/json")
async def get_leaderboard_entries_as_json(leaderboard: str):
    """ Return a leaderboard into a json format """
    entry_list = await model_queries.LeaderboardEntryList.get_from_leaderboard(leaderboard)
    return entry_list.as_leaderboard()


@router.get("{leaderboard}/csv")
async def get_leaderboard_entries_as_csv(leaderboard: str):
    def clean(file: tempfile.NamedTemporaryFile):
        """ clean temp file """
        Path(file.name).unlink(missing_ok=True)

    # load objects
    entry_list = await model_queries.LeaderboardEntryList.get_from_leaderboard(leaderboard)
    ld_mngr = leaderboard_ext.LeaderboardManager.load_leaderboard_from_obj(leaderboard, entry_list.as_leaderboard())

    # Write csv into tmp file
    tmp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
    ld_mngr.export_as_csv(file=Path(tmp_file.name))

    # return file w/ clean-up bg-task
    return FileResponse(tmp_file.name, background=BackgroundTask(clean, file=tmp_file))


@router.get("{leaderboard}/entry/{entry_id}")
async def get_leaderboard_entry(leaderboard: str, entry_id: str):
    entry = await model_queries.LeaderboardEntry.get(entry_id)
    assert entry.leaderboard_id == leaderboard
    return entry.data
