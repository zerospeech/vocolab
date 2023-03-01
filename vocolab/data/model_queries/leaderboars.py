from datetime import datetime
from pathlib import Path
from typing import List

from pydantic import BaseModel, Json

from vocolab.data import tables
from ..db import zrDB


class LeaderboardEntry(BaseModel):
    """ Data Representation of a Leaderboard Entry """
    id: int
    data: Json
    src: Path
    model_id: str
    submission_id: str
    leaderboard_id: int
    user_id: int
    submitted_at: datetime

    class Config:
        orm_mode = True



class LeaderboardEntryList(BaseModel):
    """ Data representation of a leaderboard entry list"""
    items: List[LeaderboardEntry]


class Leaderboard(BaseModel):
    """ Data representation of a Leaderboard """
    id: int
    challenge_id: int
    label: str
    archived: bool
    static_files: bool
    sorting_key: bool

    class Config:
        orm_mode = True

    @classmethod
    async def get_by_id(cls, _id: int) -> "Leaderboard":
        """ Load leaderboard from id """
        query = tables.leaderboards_table.select().where(
            tables.leaderboards_table.c.id == _id
        )

        ld_data = await zrDB.fetch_one(query)
        if ld_data is None:
            raise ValueError('Leaderboard not found')

        return cls.parse_obj(ld_data)

    async def get_entries(self) -> LeaderboardEntryList:
        """ Load leaderboard entries """
        query = tables.leaderboard_entry_table.select().where(
            tables.leaderboard_entry_table.c.leaderboard_id == self.id
        )
        ld_entries = await zrDB.fetch_all(query)
        if not ld_entries:
            return LeaderboardEntryList(items=[])
        return LeaderboardEntryList.parse_obj(dict(items=ld_entries))







