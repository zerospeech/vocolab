from datetime import date
from typing import Optional, List

from pydantic import BaseModel, AnyHttpUrl

from zerospeech.db import users_db, schema, exc as db_exc
from zerospeech.settings import get_settings

_settings = get_settings()


# TODO: implement submission/challenge queries
class NewChallenge(BaseModel):
    """ Dataclass for challenge creation """
    label: str
    active: bool
    url: AnyHttpUrl
    backend: str
    start_date: date
    end_date: Optional[date]


async def create_new_challenge(item: NewChallenge):
    try:
        query = schema.challenges_table.insert().values(
            label=item.label,
            active=item.active,
            url=item.url,
            backend=item.backend,
            start_date=item.start_date,
            end_date=item.end_date
        )
        await users_db.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)


async def list_challenges(
        include_all=None,
) -> List[schema.Challenge]:

    if include_all:
        query = schema.challenges_table.select()
    else:
        query = schema.challenges_table.select().where(
            schema.challenges_table.c.active is True
        )
    challenges = await users_db.fetch_all(query)
    if challenges is None:
        raise ValueError('No challenges were found')

    return [schema.Challenge(**c) for c in challenges]


def toggle_challenge(active: bool):
    pass


def delete_challenge():
    pass


def list_submissions(by_challenge, by_user, by_status, by_date):
    pass


def add_submission():
    pass


def get_submission():
    pass


def drop_submission():
    pass


def submission_status():
    pass


def update_submission_status():
    pass
