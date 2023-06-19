import shlex
from datetime import date
from typing import Optional, List, Any, Iterable

from pydantic import BaseModel, HttpUrl

from vocolab import get_settings
from vocolab.core import misc
from vocolab.data import models, tables
from ..db import zrDB, db_exc

st = get_settings()


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

    async def update_args(self, arg_list: List[str]):
        query = tables.evaluators_table.update().where(
            tables.evaluators_table.c.id == self.id
        ).values(executor_arguments=shlex.join(arg_list))
        await zrDB.execute(query)

    @classmethod
    async def add_or_update(cls, *, evl_item: models.cli.NewEvaluatorItem):
        query = tables.evaluators_table.select().where(
            tables.evaluators_table.c.label == evl_item.label
        ).where(
            tables.evaluators_table.c.host == evl_item.host
        )
        res = await zrDB.fetch_one(query)

        if res is None:
            await zrDB.execute(tables.evaluators_table.insert(), evl_item.dict())
        else:
            update_query = tables.evaluators_table.update().where(
                tables.evaluators_table.c.id == res.id
            ).values(
                executor=evl_item.executor, script_path=evl_item.script_path,
                executor_arguments=evl_item.executor_arguments
            )
            await zrDB.execute(update_query)

    @classmethod
    async def get(cls, by_id: int) -> Optional["EvaluatorItem"]:
        query = tables.evaluators_table.select().where(
            tables.evaluators_table.c.id == by_id
        )
        result = await zrDB.fetch_one(query)
        if not result:
            return None
        return cls.parse_obj(result)


class EvaluatorList(BaseModel):
    items: List[EvaluatorItem]

    def __iter__(self) -> Iterable[EvaluatorItem]:
        return iter(self.items)

    @classmethod
    async def get(cls) -> "EvaluatorList":
        query = tables.evaluators_table.select()
        results = await zrDB.fetch_all(query)
        if not results:
            return cls(items=[])
        return cls(items=results)


class Benchmark(BaseModel):
    """ Data representation of a challenge """
    label: str
    start_date: date
    end_date: Optional[date]
    active: bool
    url: HttpUrl
    evaluator: Optional[int]
    auto_eval: bool = st.task_queue_options.AUTO_EVAL

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
            query = tables.benchmarks_table.insert().values(
                **item.dict()
            )
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

    @classmethod
    async def get(cls, *, benchmark_id: str, allow_inactive: bool = False) -> "Benchmark":
        query = tables.benchmarks_table.select().where(
            tables.benchmarks_table.c.label == benchmark_id
        )
        ch_data = await zrDB.fetch_one(query)
        if ch_data is None:
            raise ValueError(f'There is no challenge with the following id: {benchmark_id}')
        ch = cls.parse_obj(ch_data)
        if allow_inactive:
            return ch
        else:
            if not ch.is_active():
                raise ValueError(f"The Challenge {ch.label} is not active")
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
        query = tables.benchmarks_table.update().where(
            tables.benchmarks_table.c.label == self.label
        ).values({f"{variable_name}": value})

        try:
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

        return value

    async def delete(self):
        """ Remove from database """
        query = tables.benchmarks_table.delete().where(
            tables.benchmarks_table.c.label == self.label
        )
        await zrDB.execute(query)


class BenchmarkList(BaseModel):
    items: List[Benchmark]

    def __iter__(self) -> Iterable[Benchmark]:
        yield from self.items

    def filter_active(self) -> "BenchmarkList":
        self.items = [i for i in self.items if i.is_active()]
        return self

    @classmethod
    async def get(cls, include_all: bool = False) -> "BenchmarkList":
        query = tables.benchmarks_table.select()
        challenges = await zrDB.fetch_all(query)
        if challenges is None:
            raise ValueError('No challenges were found')

        if include_all:
            return cls(items=challenges)
        return cls(items=challenges).filter_active()
