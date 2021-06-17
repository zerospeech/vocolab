"""
Database functions that manipulate the leaderboard table
"""
from typing import Any, List
from zerospeech.db import schema, zrDB, exc as db_exc
from zerospeech.lib import misc


async def get_leaderboard(*, leaderboard_id: int) -> schema.LeaderBoard:
    """ Fetches the leaderboard object with the corresponding id

    :raise ValueError if the item is not is the database
    :raise SQLAlchemy exceptions if database connection or condition fails
    """
    query = schema.leaderboards_table.select().where(
        schema.leaderboards_table.c.id == leaderboard_id
    )
    ld = await zrDB.fetch_one(query)
    if ld is None:
        raise ValueError(f'Leaderboard: {leaderboard_id} not found in database !!!')

    return schema.LeaderBoard(**ld)


async def list_leaderboards() -> List[schema.LeaderBoard]:
    """ Fetch a list of all the leaderboards present in the database

    :raise ValueError if the leaderboard database is empty
    :raise SQLAlchemy exceptions if database connection or condition fails
    """
    query = schema.leaderboards_table.select()
    leaderboards = await zrDB.fetch_all(query)
    if not leaderboards:
        raise ValueError('No leaderboards found')

    return [schema.LeaderBoard(**ld) for ld in leaderboards]


async def create_leaderboard(*, lead_data: schema.LeaderBoard):
    """ Create an new leaderboard entry in database from item object

    """
    query = schema.leaderboards_table.insert().values(
        label=lead_data.label,
        challenge_id=lead_data.challenge_id,
        path_to=f"{lead_data.path_to}",
        entry_file=lead_data.entry_file,
        archived=lead_data.archived,
        external_entries=f"{lead_data.external_entries}",
        static_files=lead_data.static_files
    )
    try:
        await zrDB.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)


async def update_leaderboard_value(*, leaderboard_id, variable_name: str, value: Any, allow_parsing: bool = False):
    """ Update a value in the leaderboard corresponding to the given id

    :raise ValueError if given variable does not exist or does not match corresponding type
    """
    field = schema.LeaderBoard.__fields__.get(variable_name, None)
    if field is None:
        raise ValueError(f'Class Leaderboard does not have a member called ! {variable_name}')

    if allow_parsing:
        value = misc.str2type(value, field.type_)

    if not isinstance(value, field.type_):
        raise ValueError(f"Leaderboard.{variable_name} should be of type {field.type_}")

    query = schema.leaderboards_table.update().where(
        schema.leaderboards_table.c.id == leaderboard_id
    ).values({f"{variable_name}": value})
    try:
        await zrDB.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)

    return value
