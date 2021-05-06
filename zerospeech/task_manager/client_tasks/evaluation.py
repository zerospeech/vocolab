from pathlib import Path

from zerospeech.db import q
from zerospeech.db import schema
from zerospeech.task_manager import QueuesNames, SubProcess
from zerospeech.task_manager import publish_message
from zerospeech.utils import submissions


async def send_eval_task(msg, loop=None):
    return await publish_message(msg, QueuesNames.eval_queue, loop)


async def challenge_eval(challenge: schema.Challenge, submission_id: str):
    if challenge.evaluator is None:
        raise ValueError(f"Challenge {challenge.label} has not specified an evaluation function !!")

    evaluator = await q.challenges.get_evaluator(challenge.evaluator)
    if evaluator is None:
        raise ValueError(f"Failed to fetch evaluator specified for {challenge.label}")

    # send submission to eval host
    if evaluator.host:
        folder = submissions.transfer_submission(evaluator.host, submission_id)
    else:
        folder = submissions.get_submission_dir(submission_id)

    # note: challenge evaluators are always of subprocess typing
    args = evaluator.base_arguments.split(';')
    args.append(f"{folder}")
    script_path = Path(evaluator.script_path)
    subprocess_message = SubProcess(
        label=f"{submission_id}",
        executor=evaluator.executor,
        exe_path=f"{script_path.parents[0]}",
        p_name=script_path.name,
        args=args
    )
    # todo check why added loop
    await send_eval_task(subprocess_message.json())
