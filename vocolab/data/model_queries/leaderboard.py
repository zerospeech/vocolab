from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Iterable

from pydantic import BaseModel, Json
from vocolab_ext.leaderboards import LeaderboardEntryBase

from vocolab import get_settings
from vocolab.core import misc, leaderboards_lib
from vocolab.data import tables
from .auth import User
from ..db import zrDB, db_exc

st = get_settings()


class Leaderboard(BaseModel):
    """ Data representation of a Leaderboard """
    label: str  # Name of leaderboard
    benchmark_id: str  # Label of the Benchmark
    archived: bool  # is_archived
    static_files: bool  # has static files
    sorting_key: Optional[str]  # path to the item to use as sorting key

    @classmethod
    def get_field_names(cls):
        return list(cls.__fields__.keys())

    class Config:
        orm_mode = True

    def get_dir(self) -> leaderboards_lib.LeaderboardDir:
        return leaderboards_lib.LeaderboardDir.load(
            label=self.label,
            sorting_key=self.sorting_key
        )

    @classmethod
    async def create(cls, ld_data: 'Leaderboard'):
        query = tables.leaderboards_table.insert().values(
            label=ld_data.label,
            benchmark_id=ld_data.benchmark_id,
            archived=ld_data.archived,
            static_files=ld_data.static_files,
            sorting_key=ld_data.sorting_key
        )
        try:
            result = await zrDB.execute(query)

            # make necessary folders in storage
            _ = leaderboards_lib.LeaderboardDir.create(
                label=ld_data.label,
                sorting_key=ld_data.sorting_key,
                static_files=ld_data.static_files
            )

            return result
        except Exception as e:
            db_exc.parse_user_insertion(e)

    async def update_property(self, *, variable_name: str, value: Any, allow_parsing: bool = False):
        """ Update a named property """
        if not hasattr(self, variable_name):
            raise ValueError(f'Class Leaderboard does not have a member called ! {variable_name}')

        variable_type = type(getattr(self, variable_name))

        if allow_parsing:
            value = misc.str2type(value, variable_type)

        if value is not None and not isinstance(value, variable_type):
            raise ValueError(f"Leaderboard.{variable_name} should be of type {variable_type}")

        if value is None:
            if not self.__fields__.get(variable_name).allow_none:
                raise ValueError(f'LeaderBoard.{variable_name} cannot be None/Null')
        else:
            if not isinstance(value, variable_type):
                raise ValueError(f"Leaderboard.{variable_name} should be of type {variable_type}")

        # set value
        setattr(self, variable_name, value)

        # Path is not supported by sqlite as a raw type
        if variable_type == Path:
            value = str(value)

        query = tables.leaderboards_table.update().where(
            tables.leaderboards_table.c.label == self.label
        ).values({f"{variable_name}": str(value)})
        try:
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

        return value

    @classmethod
    async def get(cls, leaderboard_id: str) -> Optional["Leaderboard"]:
        query = tables.leaderboards_table.select().where(
            tables.leaderboards_table.c.label == leaderboard_id
        )
        ld = await zrDB.fetch_one(query)
        if ld is None:
            return None
        return cls.parse_obj(ld)


class LeaderboardList(BaseModel):
    items: list[Leaderboard]

    def __iter__(self) -> Iterable[Leaderboard]:
        return iter(self.items)

    @classmethod
    async def get_all(cls) -> "LeaderboardList":
        query = tables.leaderboards_table.select()
        ld_list = await zrDB.fetch_all(query)
        if not ld_list:
            return cls(items=[])
        return cls(items=ld_list)

    @classmethod
    async def get_by_challenge(cls, benchmark_id: str) -> "LeaderboardList":
        query = tables.leaderboards_table.select().where(
            tables.leaderboards_table.c.benchmark_id == benchmark_id
        )
        ld_list = await zrDB.fetch_all(query)
        if not ld_list:
            return cls(items=[])
        return cls(items=ld_list)


class LeaderboardEntry(BaseModel):
    """ Data representation of a leaderboard entry """
    id: Optional[int]
    data: Json
    entry_path: Path
    submission_id: str
    leaderboard_id: str
    model_id: str
    user_id: int
    authors: str
    author_label: str
    description: str
    submitted_at: datetime

    async def base(self) -> LeaderboardEntryBase:
        user = await User.get(by_uid=self.user_id)
        return LeaderboardEntryBase(
            submission_id=self.submission_id,
            model_id=self.model_id,
            description=self.description,
            authors=self.authors,
            author_label=self.author_label,
            submission_date=self.submitted_at,
            submitted_by=user.username
        )

    async def update(self, base: LeaderboardEntryBase):
        self.submission_id = base.submission_id
        self.model_id = base.model_id
        self.description = base.description
        self.authors = base.authors
        self.author_label = base.author_label
        self.submitted_at = base.submission_date

        base_dict = asdict(base)
        del base["submitted_by"]
        query = tables.leaderboards_table.update().where(
            tables.leaderboard_entry_table.c.id == self.id
        ).values(
            **base_dict
        )
        await zrDB.execute(query)
        # todo: check how this would work ???
        (await self.leaderboard()).get_dir().update_entry(await self.base())

    async def leaderboard(self) -> Leaderboard:
        return await Leaderboard.get(self.leaderboard_id)

    @classmethod
    async def get(cls, by_id) -> Optional["LeaderboardEntry"]:
        query = tables.leaderboard_entry_table.select().where(
            tables.leaderboard_entry_table.c.id == by_id
        )
        ld = await zrDB.fetch_one(query)
        if ld is None:
            return None
        return cls.parse_obj(ld)


class LeaderboardEntryList(BaseModel):
    items: list[LeaderboardEntry]

    def __iter__(self) -> Iterable[LeaderboardEntry]:
        yield from self.items

    def as_leaderboard(self) -> dict:
        # todo: check data format
        return dict(
            last_modified=datetime.now().isoformat(),
            data=[
                entry.data
                for entry in self
            ]
        )

    @classmethod
    async def get_from_leaderboard(cls, leaderboard_label: str):
        """ Get all entries of leaderboard"""
        query = tables.leaderboard_entry_table.select().where(
            tables.leaderboard_entry_table.c.leaderboard_id == leaderboard_label
        )
        entries = await zrDB.fetch_all(query)
        return cls(items=entries)
