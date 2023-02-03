from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from pydantic import BaseModel
from pydantic import HttpUrl

from vocolab.data import models, tables
from vocolab.core import misc
from ..base import zrDB, db_exc


class EvaluatorItem(BaseModel):
    """ Data representation of an evaluator """
    id: int
    label: str
    executor: models.tasks.ExecutorsType
    host: Optional[str]
    script_path: str
    executor_arguments: str

    class Config:
        orm_mode = True


class Challenge(BaseModel):
    """ Data representation of a challenge """
    id: int
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    evaluator: Optional[int]

    class Config:
        orm_mode = True

    def is_active(self) -> bool:
        """ Checks if challenge is active """
        present = date.today()
        if self.end_date:
            return self.start_date <= present <= self.end_date and self.active
        else:
            return self.start_date <= present and self.active

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())

    @classmethod
    async def create(cls, item: models.cli.NewChallenge):
        try:
            query = tables.challenges_table.insert().values(
                **item.dict()
            )
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

    @classmethod
    async def get(cls, *, challenge_id: int, allow_inactive: bool = False) -> "Challenge":
        query = tables.challenges_table.select().where(
            tables.challenges_table.c.id == challenge_id
        )
        ch_data = await zrDB.fetch_one(query)
        if ch_data is None:
            raise ValueError(f'There is no challenge with the following id: {challenge_id}')
        ch = cls.parse_obj(ch_data)
        if allow_inactive:
            return ch
        else:
            if not ch.is_active():
                raise ValueError(f"The Challenge {ch.label}[{ch.id}] is not active")
            return ch

    async def update_property(self, *, variable_name: str, value: Any, allow_parsing: bool = False):
        """ Update a property """
        if not hasattr(self, variable_name):
            raise ValueError(f'Class Challenge does not have a member called ! {variable_name}')

        variable_type = type(getattr(self, variable_name))

        if allow_parsing:
            value = misc.str2type(value, variable_type)

        if value is not None and not isinstance(value, variable_type):
            raise ValueError(f"Challenge.{variable_name} should be of type {variable_type}")

        setattr(self, variable_name, value)

        # update database
        query = tables.challenges_table.update().where(
            tables.challenges_table.c.id == self.id
        ).values({f"{variable_name}": value})

        try:
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

        return value

    async def delete(self):
        """ Remove from database """
        query = tables.challenges_table.delete().where(
            tables.challenges_table.c.id == self.id
        )
        await zrDB.execute(query)




class ChallengeList(BaseModel):
    items: List[Challenge]

    def filter_active(self) -> "ChallengeList":
        self.items = [i for i in self.items if i.is_active()]
        return self

    @classmethod
    async def get(cls, include_all: bool = False) -> "ChallengeList":
        query = tables.challenges_table.select()
        challenges = await zrDB.fetch_all(query)
        if challenges is None:
            raise ValueError('No challenges were found')

        if include_all:
            return cls(items=challenges)
        return cls(items=challenges).filter_active()


class Leaderboard(BaseModel):
    """ Data representation of a Leaderboard """
    id: Optional[int]
    challenge_id: int  # Id to linked challenge
    label: str  # Name of leaderboard
    path_to: Path  # Path to build result
    entry_file: str  # filename in submission results
    archived: bool  # is_archived
    external_entries: Optional[Path]  # Location of external entries (baselines, toplines, archived)
    static_files: bool  # has static files
    sorting_key: Optional[str]  # path to the item to use as sorting key

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())

    class Config:
        orm_mode = True


class LeaderboardEntry:
    """ Data representation of a leaderboard entry """
    id: Optional[int]
    entry_path: Path
    model_id: str
    submission_id: str
    leaderboard_id: int
    submitted_at: datetime
