from datetime import datetime
from typing import List, Any, Optional
from uuid import uuid4

from zerospeech.db import models, zrDB, schema, exc as db_exc
from zerospeech import get_settings, out
from zerospeech.lib import misc

_settings = get_settings()


async def create_new_challenge(item: models.cli.NewChallenge):
    """ Creates a new challenge entry in the database """
    try:
        query = schema.challenges_table.insert().values(
            label=item.label,
            active=item.active,
            url=item.url,
            evaluator=item.evaluator,
            start_date=item.start_date,
            end_date=item.end_date
        )
        await zrDB.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)


async def list_challenges(*, include_all: bool = False) -> List[schema.Challenge]:
    """ Returns a list of all the challenges

    :flag include_all allows to filter out inactive challenges
    """
    query = schema.challenges_table.select()
    challenges = await zrDB.fetch_all(query)
    if challenges is None:
        raise ValueError('No challenges were found')

    challenges = [schema.Challenge(**c) for c in challenges]
    if include_all:
        return challenges
    else:
        return [c for c in challenges if c.is_active()]


async def get_challenge(*,
                        challenge_id: int, allow_inactive=False,
                        ) -> schema.Challenge:
    """ Fetches the Challenge object from the database

    :note:  in strict mode (allow_inactive = False) the function raises a ValueError
    if the challenge has expired or is inactive.
    """
    query = schema.challenges_table.select().where(
        schema.challenges_table.c.id == challenge_id
    )
    ch = await zrDB.fetch_one(query)
    if ch is None:
        raise ValueError(f'There is no challenge with the following id: {challenge_id}')
    ch = schema.Challenge(**ch)
    if allow_inactive:
        return ch
    else:
        if not ch.is_active():
            raise ValueError(f"The Challenge {ch.label}[{ch.id}] is not active")
        return ch


async def update_challenge_property(*, challenge_id: int, variable_name: str, value: Any,
                                    allow_parsing: bool = False):
    """ Update the property of a challenge """
    field = schema.Challenge.__fields__.get(variable_name, None)
    if field is None:
        raise ValueError(f'Class Challenge does not have a member called ! {variable_name}')

    if allow_parsing:
        value = misc.str2type(value, field.type_)

    if not isinstance(value, field.type_):
        raise ValueError(f"Challenge.{variable_name} should be of type {field.type_}")

    query = schema.challenges_table.update().where(
        schema.challenges_table.c.id == challenge_id
    ).values({f"{variable_name}": value})

    try:
        await zrDB.execute(query)
    except Exception as e:
        db_exc.parse_user_insertion(e)

    return value


async def delete_challenge(*, ch_id: int):
    """ Delete the database entry of a challenge """
    query = schema.challenges_table.delete().where(
        schema.challenges_table.c.id == ch_id
    )
    return await zrDB.execute(query)


async def add_submission(*, new_submission: models.api.NewSubmission, evaluator_id: int):
    """ Creates a database entry to a new submission """
    submission_id = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
    query = schema.submissions_table.insert()
    values = new_submission.dict()
    values["id"] = submission_id
    values["submit_date"] = datetime.now()
    values["status"] = schema.SubmissionStatus.uploading
    values["evaluator_id"] = evaluator_id
    await zrDB.execute(query=query, values=values)
    return submission_id


async def list_submission(*, by_track: int = None, by_user: int = None, by_status=None):
    """ Fetches a list of submission from the database """
    query = schema.submissions_table.select()

    if by_track:
        query = query.where(
            schema.submissions_table.c.track_id == by_track
        )

    if by_user:
        query = query.where(
            schema.submissions_table.c.user_id == by_user
        )

    if by_status:
        query = query.where(
            schema.submissions_table.c.status == by_status
        )

    sub_list = await zrDB.fetch_all(query)

    # map & return
    return [schema.ChallengeSubmission(**sub) for sub in sub_list]


async def get_submission(*, by_id: str) -> schema.ChallengeSubmission:
    """ Fetches a submission from the database """
    query = schema.submissions_table.select().where(
        schema.submissions_table.c.id == by_id
    )
    sub = await zrDB.fetch_one(query)
    if sub is None:
        raise ValueError(f'There is no challenge with the following id: {by_id}')
    # map & return
    return schema.ChallengeSubmission(**sub)


async def update_submission_status(*, by_id: str, status: schema.SubmissionStatus):
    """ Update the status of a submission """
    query = schema.submissions_table.update().where(
        schema.submissions_table.c.id == by_id
    ).values(status=status)
    return await zrDB.execute(query)


async def drop_submission(*, by_id: str):
    """ Delete db entry of a submission """
    query = schema.submissions_table.delete().where(
        schema.submissions_table.c.id == by_id
    )
    await zrDB.execute(query)


async def submission_status(*, by_id: str) -> schema.SubmissionStatus:
    """ Returns the status of a submission """
    query = schema.submissions_table.select().where(
        schema.submissions_table.c.id == by_id
    )
    sub = await zrDB.fetch_one(query)
    if sub is None:
        raise ValueError(f'There is no challenge with the following id: {by_id}')
    # map & return
    return schema.ChallengeSubmission(**sub).status


async def get_evaluators():
    """ Returns a list of the evaluators """
    query = schema.evaluators_table.select()
    results = await zrDB.fetch_all(query)
    if not results:
        return []
    return [schema.EvaluatorItem(**i) for i in results]


async def get_evaluator(*, by_id: Optional[int] = None, by_submission_id: Optional[str]):
    """ Returns a specific evaluator """
    if by_id:
        query = schema.evaluators_table.select().where(
            schema.evaluators_table.c.id == by_id
        )
    elif by_submission_id:
        """
            TODO
        """
        query = schema.evaluators_table.select().where(

        )
    else:
        raise ValueError('No filter given')

    result = await zrDB.fetch_one(query)
    if not result:
        return None
    return schema.EvaluatorItem(**result)


async def add_evaluator(*, lst_eval: List[models.cli.NewEvaluatorItem]):
    """ Insert a list of evaluators into the database """
    query = schema.evaluators_table.insert()
    # out.Console.ic([i.dict() for i in lst_eval])
    await zrDB.execute_many(query, [i.dict() for i in lst_eval])


async def edit_evaluator_args(*, eval_id: int, arg_list: List[str]):
    """ update evaluator base arguments """
    query = schema.evaluators_table.update().where(
        schema.evaluators_table.c.id == eval_id
    ).values(base_arguments=";".join(arg_list))
    await zrDB.execute(query)
