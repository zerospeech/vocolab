import asyncio

from vocolab import out, get_settings
from vocolab.db.models import tasks
from vocolab.lib import submissions_lib

_settings = get_settings()


def update_task_fn(sum_: tasks.SubmissionUpdateMessage):
    async def eval_function(msg: tasks.SubmissionUpdateMessage):
        """ Evaluate a function type BrokerCMD """
        with submissions_lib.SubmissionLogger(msg.submission_id) as lg:
            out.log.debug(msg.dict())

            if msg.updateType == tasks.UpdateType.evaluation_complete:
                await submissions_lib.complete_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == tasks.UpdateType.evaluation_failed:
                await submissions_lib.fail_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            elif msg.updateType == tasks.UpdateType.evaluation_canceled:
                await submissions_lib.cancel_evaluation(
                    submission_id=msg.submission_id, hostname=msg.hostname,
                    logger=lg)
            else:
                raise ValueError("Unknown update task !!!")

    asyncio.run(eval_function(sum_))
