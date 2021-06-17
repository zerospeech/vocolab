import argparse
import asyncio
from datetime import datetime

from zerospeech import get_settings
from zerospeech.db.models.tasks import (
    SimpleLogMessage,
    SubmissionEvaluationMessage,
    SubmissionUpdateMessage
)
from zerospeech.lib.worker_lib.pika_utils import publish_message
from zerospeech.lib.worker_lib.worker_types import WORKER_TYPE

_settings = get_settings()


def test_simple_log(message):
    channel = _settings.QUEUE_CHANNELS.get('echo')
    msg = SimpleLogMessage(
        label="testing",
        message=f"{message}"
    )
    asyncio.run(publish_message(msg, channel))


def test_eval_message(submission_id, hostname):
    channel = _settings.QUEUE_CHANNELS.get('eval')
    remote_bin = _settings.REMOTE_BIN.get(hostname, None)
    if remote_bin is None:
        raise ValueError(f'Host {hostname} has no registered bin folder !!')

    remote_submissions = _settings.REMOTE_STORAGE.get(hostname, None)
    if remote_submissions is None:
        raise ValueError(f'Host {hostname} has no remote storage folder registered !!')

    msg = SubmissionEvaluationMessage(
        label="testing-eval",
        submission_id=submission_id,
        bin_path=f"{remote_bin}",
        script_name="test.sh",
        args=[f"{remote_submissions / submission_id}"]
    )
    asyncio.run(publish_message(msg, channel))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("worker",
                        choices=list(WORKER_TYPE.keys()), default="echo",
                        help="Worker Type")
    parser.add_argument('--message', default=f"The time is {datetime.now().isoformat()}")
    parser.add_argument('--submission-id', default=f"123")
    parser.add_argument('--hostname', default=f"{_settings.hostname}")
    args = parser.parse_args()

    # publish message
    if args.worker == 'eval':
        test_eval_message(args.submission_id, args.hostname)
    elif args.worker == 'update':
        raise NotImplementedError('No test for update messaging')
    elif args.worker == 'echo':
        test_simple_log(args.message)
    else:
        raise ValueError(f'Worker {args.worker} is not a valid worker !!!')
