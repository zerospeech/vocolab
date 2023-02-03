from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from vocolab import get_settings

_settings = get_settings()


async def get_evaluators():
    """ Returns a list of the evaluators """
    query = schema.evaluators_table.select()
    results = await zrDB.fetch_all(query)
    if not results:
        return []
    return [schema.EvaluatorItem(**i) for i in results]


async def get_evaluator(*, by_id: int) -> Optional[schema.EvaluatorItem]:
    """ Returns a specific evaluator """

    query = schema.evaluators_table.select().where(
        schema.evaluators_table.c.id == by_id
    )
    result = await zrDB.fetch_one(query)
    if not result:
        return None
    return schema.EvaluatorItem(**result)


async def add_evaluator(*, lst_eval: List[models.cli.NewEvaluatorItem]):
    """ Insert a list of evaluators into the database """
    for i in lst_eval:
        query = schema.evaluators_table.select().where(
            schema.evaluators_table.c.label == i.label
        ).where(
            schema.evaluators_table.c.host == i.host
        )
        res = await zrDB.fetch_one(query)

        if res is None:
            await zrDB.execute(schema.evaluators_table.insert(), i.dict())
        else:
            update_query = schema.evaluators_table.update().where(
                schema.evaluators_table.c.id == res.id
            ).values(executor=i.executor, script_path=i.script_path, executor_arguments=i.executor_arguments)
            await zrDB.execute(update_query)


async def edit_evaluator_args(*, eval_id: int, arg_list: List[str]):
    """ update evaluator base arguments """
    query = schema.evaluators_table.update().where(
        schema.evaluators_table.c.id == eval_id
    ).values(executor_arguments=";".join(arg_list))
    await zrDB.execute(query)
