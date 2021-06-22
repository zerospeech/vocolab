from datetime import datetime
from typing import Optional, List

from zerospeech import get_settings
from zerospeech.lib.worker_lib import pika_utils
from zerospeech.db.models.tasks import (
    SimpleLogMessage, SubmissionUpdateMessage,
    SubmissionEvaluationMessage, UpdateType, ExecutorsType
)

_settings = get_settings()


def make_label(fn_type):
    return f"{fn_type}-{datetime.now().isoformat()}"


async def send_echo_message(*, message: str, label: Optional[str] = None):
    if label is None:
        label = make_label('echo-testing')
    msg = SimpleLogMessage(
        label=label,
        message=message
    )
    channel = _settings.QUEUE_CHANNELS.get('echo')
    return await pika_utils.publish_message(msg=msg, queue_name=channel)


async def send_update_message(*, submission_id: str, hostname: str, update_type: UpdateType,
                              label: Optional[str] = None):
    if label is None:
        label = make_label(f'updating-{submission_id}')

    msg = SubmissionUpdateMessage(
        label=label,
        submission_id=submission_id,
        hostname=hostname,
        updateType=update_type
    )
    channel = _settings.QUEUE_CHANNELS.get('update')
    return await pika_utils.publish_message(msg=msg, queue_name=channel)


async def send_eval_message(*, submission_id: str, executor: ExecutorsType,
                            bin_path: str, script_name: str, args: List[str], label: Optional[str] = None):
    if label is None:
        label = make_label('echo-testing')

    msg = SubmissionEvaluationMessage(
        label=label,
        executor=executor,
        submission_id=submission_id,
        bin_path=bin_path,
        script_name=script_name,
        args=args
    )
    channel = _settings.QUEUE_CHANNELS.get('eval')
    return await pika_utils.publish_message(msg=msg, queue_name=channel)
