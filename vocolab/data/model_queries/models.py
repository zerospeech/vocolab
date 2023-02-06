import math
from datetime import datetime
from enum import Enum
from itertools import chain, product
from typing import Optional, List, Iterable

from pydantic import BaseModel, AnyHttpUrl

from vocolab import get_settings
from vocolab.data import db, tables, models

_settings = get_settings()


# TODO: add method for easy author_label editing


class ModelID(BaseModel):
    """ Data representation of a Model id & its metadata"""
    id: str
    user_id: int
    created_at: datetime
    description: str
    gpu_budget: str
    train_set: str
    authors: str
    institution: str
    team: str
    paper_url: AnyHttpUrl
    code_url: AnyHttpUrl

    @staticmethod
    def nth_word(n: int) -> str:
        """ Calculate the nth word of the english lower alphabet

            This function returns a string that counts using the lower english alphabet.
            0 -> ''
            1 -> a
            ...
            26 -> z
            27 -> aa
            28 -> ab
            ...
            53 -> ba
            ... etc

            Note: This methods becomes kind of slow for numbers larger than 10_000_000

        """
        nb_letters = 26  # use english alphabet [1, 26] lowercase letters
        letters = [chr(97 + i) for i in range(nb_letters)]
        # calculate word_length
        word_length = math.ceil(math.log((n + 1) * (nb_letters - 1) + 1) / math.log(nb_letters))
        # Build all possible combinations for the given word length
        it = chain.from_iterable(
            (product(letters, repeat=i) for i in range(word_length))
        )
        # find word in iterable
        word = next(w for i, w in enumerate(it) if i == n)
        return ''.join(word)

    @classmethod
    async def create(cls, first_author_name: str, data: models.api.NewModelIdRequest):
        """ Create a new ModelID entry in the database

            ids are created using the 3 first letters of first name of first author,
            the last 2 digits of the current year and are padded with extra letters to
            avoid duplicates.
         """
        new_model_id = f"{first_author_name[:3]}{str(datetime.now().year)[2:]}"

        counter = 1
        new_model_id_extended = f"{new_model_id}{cls.nth_word(counter)}"
        while cls.exists(new_model_id_extended):
            counter += 1
            new_model_id_extended = f"{new_model_id}{cls.nth_word(counter)}"

        # create db entry
        query = tables.models_table.insert().values(id=new_model_id_extended, **data.dict())
        await db.zrDB.execute(query)
        return new_model_id_extended

    @classmethod
    async def exists(cls, model_id: str) -> bool:
        item = await db.zrDB.fetch_one(
            tables.models_table.select().where(
                tables.models_table.c.id == model_id
            )
        )
        return item is not None

    @classmethod
    async def get(cls, model_id: str) -> Optional["ModelID"]:
        """ Fetch a model_id entry from the database """
        item_data = await db.zrDB.fetch_one(
            tables.models_table.select().where(
                tables.models_table.c.id == model_id
            )
        )
        if item_data is None:
            return None
        return cls.parse_obj(item_data)


class ModelIDList(BaseModel):
    items: List[ModelID]

    def __iter__(self) -> Iterable[ModelID]:
        return iter(self.items)

    @classmethod
    async def get(cls) -> "ModelIDList":
        items = db.zrDB.fetch_all(tables.models_table.select())
        return cls(items=items)


class SubmissionStatus(str, Enum):
    """ Definition of different states of submissions """
    # TODO: maybe add submission type (with scores...)
    uploading = 'uploading'
    uploaded = 'uploaded'
    on_queue = 'on_queue'
    validating = 'validating'  # todo verify usage
    invalid = 'invalid'
    evaluating = 'evaluating'
    completed = 'completed'
    canceled = 'canceled'
    failed = 'failed'
    no_eval = 'no_eval'
    no_auto_eval = 'no_auto_eval'
    excluded = 'excluded'

    @classmethod
    def get_values(cls):
        return [el.value for el in cls]  # noqa: enum is not typed correctly


class ChallengeSubmission(BaseModel):
    """ Data representation of a submission to a challenge """
    id: str
    user_id: int
    track_id: int
    submit_date: datetime
    status: SubmissionStatus
    auto_eval: bool
    evaluator_id: Optional[int]
    author_label: Optional[str] = None

    class Config:
        orm_mode = True

    @classmethod
    async def create(cls, username: str, new_submission: models.api.NewSubmissionRequest, evaluator_id: int) -> str:
        """ Creates a database entry for the new submission """
        submission_id = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{username}"
        values = new_submission.dict()
        values["id"] = submission_id
        values["submit_date"] = datetime.now()
        values["status"] = SubmissionStatus.uploading
        values["evaluator_id"] = evaluator_id
        # todo: auto-eval should maybe work differently ?
        values["auto_eval"] = _settings.task_queue_options.AUTO_EVAL

        await db.zrDB.execute(
            query=tables.submissions_table.insert(),
            values=values
        )
        return submission_id

    @classmethod
    async def get(cls, submission_id: str) -> Optional["ChallengeSubmission"]:
        item_data = await db.zrDB.fetch_one(
            tables.submissions_table.select().where(
                tables.submissions_table.c.id == submission_id
            )
        )
        if item_data is None:
            return None
        return cls.parse_obj(item_data)

    async def update_status(self, status: SubmissionStatus):
        self.status = status
        await db.zrDB.execute(
            tables.submissions_table.update().where(
                tables.submissions_table.c.id == self.id
            ).values(status=status.value)
        )

    async def update_evaluator(self, evaluator_id: int):
        self.evaluator_id = evaluator_id
        await db.zrDB.execute(
            tables.submissions_table.update().where(
                tables.submissions_table.c.id == self.id
            ).values(evaluator_id=evaluator_id)
        )

    async def delete(self):
        await db.zrDB.execute(
            tables.submissions_table.delete().where(
                tables.submissions_table.c.id == self.id
            )
        )


class ChallengeSubmissionList(BaseModel):
    items: List[ChallengeSubmission]

    def __iter__(self) -> Iterable[ChallengeSubmission]:
        return iter(self.items)

    @classmethod
    async def get_from_challenge(cls, challenge_id: int):
        items = await db.zrDB.fetch_all(
            tables.submissions_table.select().where(
                tables.submissions_table.c.track_id == challenge_id
            )
        )
        if items is None:
            items = []

        return cls(items=items)

    @classmethod
    async def get_from_model(cls, model_id: str):
        items = await db.zrDB.fetch_all(
            tables.submissions_table.select().where(
                tables.submissions_table.c.model_id == model_id
            )
        )
        if items is None:
            items = []

        return cls(items=items)

    @classmethod
    async def get_from_user(cls, user_id: int):
        items = await db.zrDB.fetch_all(
            tables.submissions_table.select().where(
                tables.submissions_table.c.user_id == user_id
            )
        )
        if items is None:
            items = []

        return cls(items=items)

    @classmethod
    async def get_by_status(cls, status: SubmissionStatus):
        items = await db.zrDB.fetch_all(
            tables.submissions_table.select().where(
                tables.submissions_table.c.status == status.value
            )
        )
        if items is None:
            items = []

        return cls(items=items)

    async def update_evaluators(self, evaluator_id: int):
        for e in self.items:
            e.evaluator_id = evaluator_id

        # todo check if query works successfully
        items_id = set([e.id for e in self.items])
        await db.zrDB.execute(
            tables.submissions_table.update().where(
                tables.submissions_table.c.id.in_(items_id)
            ).values(evaluator_id=evaluator_id)
        )
