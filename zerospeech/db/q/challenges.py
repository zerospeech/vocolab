from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from zerospeech.db import zrDB, schema, exc as db_exc
from zerospeech.db.schema import NewChallenge, NewSubmission
from zerospeech.settings import get_settings

_settings = get_settings()


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
        await zrDB.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)


async def list_challenges(
        include_all=None,
) -> List[schema.Challenge]:
    query = schema.challenges_table.select()
    challenges = await zrDB.fetch_all(query)
    if challenges is None:
        raise ValueError('No challenges were found')

    challenges = [schema.Challenge(**c) for c in challenges]
    if include_all:
        return challenges
    else:
        return [c for c in challenges if c.is_active()]


async def get_challenge(
        challenge_id: int, allow_inactive=False,
) -> Optional[schema.Challenge]:
    query = schema.challenges_table.select().where(
        schema.challenges_table.c.id == challenge_id
    )
    ch = await zrDB.fetch_one(query)
    ch = schema.Challenge(**ch)
    if allow_inactive:
        return ch
    else:
        return ch if ch.is_active() else None


async def set_challenge_property(ch_id: int, property_name: str, value: str, m_type):
    query = schema.challenges_table.update().where(
        schema.challenges_table.c.id == ch_id
    ).values({f"{property_name}": value})

    await zrDB.execute(query)


async def delete_challenge(ch_id: int):
    query = schema.challenges_table.delete().where(
        schema.challenges_table.c.id == ch_id
    )
    await zrDB.execute(query)


async def add_submission(new_submission: NewSubmission):
    submission_id = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
    query = schema.submissions_table.insert()
    values = new_submission.dict()
    values["id"] = submission_id
    values["submit_date"] = datetime.now()
    values["status"] = schema.SubmissionStatus.uploading
    await zrDB.execute(query=query, values=values)
    return submission_id


def list_submissions(by_challenge=None, by_user=None, by_status=None, by_date=None):
    pass


def get_submission():
    pass


def drop_submission():
    pass


def submission_status():
    pass


def update_submission_status():
    pass
