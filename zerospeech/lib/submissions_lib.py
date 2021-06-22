import asyncio
import json
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile

from zerospeech import exc
from zerospeech.db import models, schema
from zerospeech.db.q import challengesQ
from zerospeech.lib import _fs, leaderboards_lib, worker_lib
from zerospeech.settings import get_settings

_settings = get_settings()

# export function
make_submission_on_disk = _fs.submissions.make_submission_on_disk
md5sum = _fs.commons.md5sum
get_submission_dir = _fs.submissions.get_submission_dir
unzip = _fs.commons.unzip
SubmissionLogger = _fs.submissions.SubmissionLogger


def add_part(submission_id: str, filename: str, data: UploadFile):
    logger = _fs.submissions.SubmissionLogger(submission_id)
    folder = _fs.submissions.get_submission_dir(submission_id)

    # check existing submission
    if not folder.is_dir():
        raise exc.ResourceRequestedNotFound(f"submission ({submission_id}) does not exist!!")

    # check submission status set to upload
    if not (folder / 'upload.lock').is_file():
        raise exc.InvalidRequest(f"submission ({submission_id}) does not accept any more parts")

    # check if multipart_upload
    if (folder / 'tmp').is_dir() and (folder / 'tmp/upload.json').is_file():
        completed, expecting_list = _fs.submissions.multipart_add(submission_id, filename, data)
    else:
        completed, expecting_list = _fs.submissions.singlepart_add(submission_id, filename, data)

    # is_completed => remove lock
    if completed:
        (folder / 'upload.lock').unlink()
        logger.log(f"Submission upload was completed.")

    return completed, expecting_list


def complete_submission(submission_id: str, with_eval: bool = True):
    """ Does the end of upload tasks:
        - merge parts if the upload was multipart
        - unzip the input archive
        - mark upload as completed
        - run evaluation function
    : logs to submission logfile
    """
    folder = _fs.submissions.get_submission_dir(submission_id)

    if (folder / 'tmp').is_dir() and (folder / 'tmp/upload.json').is_file():
        with (folder / 'tmp' / 'upload.json').open() as fp:
            mf_data = models.file_split.SplitManifest(**json.load(fp))

        archive = _fs.file_spilt.merge_zip(mf_data, folder)
    else:
        archive = folder / 'input.zip'

    _fs.commons.unzip(archive, folder / 'input')
    # mark task as uploaded to the database
    asyncio.run(
        challengesQ.update_submission_status(by_id=submission_id, status=schema.SubmissionStatus.uploaded)
    )
    # start eval task
    if with_eval:
        asyncio.run(
            evaluate(submission_id)
        )


async def evaluate(submission_id: str, extra_args: Optional[List[str]] = None):
    """ ... """
    submission = await challengesQ.get_submission(by_id=submission_id)
    evaluator = await challengesQ.get_evaluator(by_id=submission.evaluator_id)
    extra_args = extra_args if extra_args is not None else []

    if evaluator is None:
        # todo What to do when no eval ?
        raise ValueError('No Evaluator Found')

    # Transfer submission to host if remote
    if evaluator.host != _settings.hostname:
        location = _fs.submissions.transfer_submission_to_remote(host=evaluator.host, submission_id=submission_id)
    else:
        location = get_submission_dir(submission_id)

    # send message to worker to launch evaluation
    await worker_lib.send_eval_message(
        submission_id=submission_id,
        executor=evaluator.executor,
        bin_path=str(Path(evaluator.script_path).parent),
        script_name=str(Path(evaluator.script_path).name),
        args=[*evaluator.base_arguments, *extra_args, str(location)]
    )


async def cancel_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname

    if is_remote:
        transfer_location = _settings.REMOTE_STORAGE.get(hostname)
        remote_submission_location = transfer_location / f"{submission_id}"
        logger.fetch_remote(hostname, remote_submission_location)

    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.canceled)


async def fail_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname

    # fetch results
    if is_remote:
        transfer_location = _settings.REMOTE_STORAGE.get(hostname)
        remote_submission_location = transfer_location / f"{submission_id}"
        logger.fetch_remote(hostname, remote_submission_location)

    # mark failed
    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.failed)


async def complete_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname

    # fetch results
    if is_remote:
        _fs.submissions.fetch_submission_from_remote(hostname, submission_id)

    # mark completed
    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.completed)

    submission = await challengesQ.get_submission(by_id=submission_id)

    # build relevant leaderboards
    await leaderboards_lib.build_all_challenge(submission.track_id)
    logger.log("api extracted all relevant information for leaderboard")
