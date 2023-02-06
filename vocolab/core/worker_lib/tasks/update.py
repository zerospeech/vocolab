import asyncio

from vocolab import out, get_settings
from vocolab.data import models
from vocolab.core import submission_lib

_settings = get_settings()


def update_task_fn(sum_: models.tasks.SubmissionUpdateMessage):
    async def eval_function(msg: models.tasks.SubmissionUpdateMessage):
        """ Evaluate a function type BrokerCMD """
        with submission_lib.SubmissionLogger(msg.submission_id) as lg:
            out.log.debug(msg.dict())

            if msg.updateType == models.tasks.UpdateType.evaluation_complete:
                await submission_lib.complete_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == models.tasks.UpdateType.evaluation_failed:
                await submission_lib.fail_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == models.tasks.UpdateType.evaluation_canceled:
                await submission_lib.cancel_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            else:
                raise ValueError("Unknown update task !!!")

    asyncio.run(eval_function(sum_))
