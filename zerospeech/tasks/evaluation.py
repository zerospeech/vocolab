from pathlib import Path

from zerospeech.db import q
from zerospeech.db import schema
from zerospeech.task_manager import QueuesNames, SubmissionEvaluationMessage
from zerospeech.task_manager import publish_message
from zerospeech.utils import submissions


async def send_eval_task(msg, loop=None):
    return await publish_message(msg, QueuesNames.eval_queue, loop)


async def challenge_eval(submission_id: str, challenge: schema.Challenge = None):
    submission_obj = await q.challenges.get_submission(submission_id)

    if challenge is None:
        challenge = await q.challenges.get_challenge(challenge_id=submission_obj.track_id)

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
    subprocess_message = SubmissionEvaluationMessage(
        label=f"...",
        submission_id=submission_id,
        executor=evaluator.executor,
        bin_path=f"{script_path.parents[0]}",
        script_name=f"{script_path.name}",
        args=args
    )
    # todo check why added loop
    await send_eval_task(subprocess_message.json())
