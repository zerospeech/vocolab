import asyncio
import json
import shlex
from fastapi import UploadFile
from pathlib import Path
from typing import List, Optional

from zerospeech import exc, out, worker
from zerospeech.db import models, schema
from zerospeech.db.q import challengesQ, leaderboardQ
from zerospeech.lib import _fs, leaderboards_lib
from zerospeech.settings import get_settings

_settings = get_settings()

# exported file functions
make_submission_on_disk = _fs.submissions.make_submission_on_disk
md5sum = _fs.commons.md5sum
get_submission_dir = _fs.submissions.get_submission_dir
unzip = _fs.commons.unzip
transfer_submission_to_remote = _fs.submissions.transfer_submission_to_remote
fetch_submission_from_remote = _fs.submissions.fetch_submission_from_remote
delete_submission_files = _fs.submissions.delete_submission_files
archive_submission_files = _fs.submissions.archive_submission_files
SubmissionLogger = _fs.submissions.SubmissionLogger


def add_part(submission_id: str, filename: str, data: UploadFile):
    submission_dir = _fs.submissions.get_submission_dir(submission_id, as_obj=True)
    logger = submission_dir.get_log_handler()

    # check existing submission
    if not submission_dir.root.is_dir():
        raise exc.ResourceRequestedNotFound(f"submission ({submission_id}) does not exist!!")

    # check submission status set to upload
    if not submission_dir.upload_lock.is_file():
        raise exc.InvalidRequest(f"submission ({submission_id}) does not accept any more parts")

    # check if multipart_upload
    if submission_dir.is_multipart():
        completed, expecting_list = _fs.submissions.multipart_add(submission_id, filename, data)
    else:
        completed, expecting_list = _fs.submissions.singlepart_add(submission_id, filename, data)

    # is_completed => remove lock
    if completed:
        submission_dir.upload_lock.unlink()
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
    submission_dir = get_submission_dir(submission_id, as_obj=True)

    # check if multipart => merge chunks
    if submission_dir.is_multipart():
        with submission_dir.multipart_index.open() as fp:
            mf_data = models.file_split.SplitManifest(**json.load(fp))

        archive = _fs.file_spilt.merge_zip(mf_data, folder)
    else:
        archive = submission_dir.singlepart

    # unzip data
    _fs.commons.unzip(archive, submission_dir.input)

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
    """ Set up a submission to be evaluated by a worker """
    submission_db = await challengesQ.get_submission(by_id=submission_id)
    logger = SubmissionLogger(submission_id)
    evaluator = await challengesQ.get_evaluator(by_id=submission_db.evaluator_id)
    extra_args = extra_args if extra_args is not None else []
    submission_fs = get_submission_dir(submission_id, as_obj=True)
    track = await challengesQ.get_challenge(challenge_id=submission_db.track_id)

    if evaluator is None:
        await challengesQ.update_submission_status(by_id=submission_id, status=schema.SubmissionStatus.no_eval)
        logger.log(f'challenge {submission_db.track_id} has not configured evaluators !')
        return None

    # set status to evaluating
    await challengesQ.update_submission_status(by_id=submission_id, status=schema.SubmissionStatus.evaluating)

    if submission_fs.eval_lock.is_file():
        out.log.warning(f"submission {submission_id} is already being evaluated")
        return None

    # Transfer submission to host if remote
    if evaluator.host != _settings.hostname:
        location = _fs.submissions.transfer_submission_to_remote(host=evaluator.host, submission_id=submission_id)
    else:
        location = get_submission_dir(submission_id)

    # send message to worker to launch evaluation
    out.cli.debug("sending message to queue")
    worker.evaluate.delay(
        models.tasks.SubmissionEvaluationMessage(
            label=f"{track.label}-eval",
            submission_id=submission_id,
            executor=evaluator.executor,
            bin_path=str(Path(evaluator.script_path).parent),
            script_name=str(Path(evaluator.script_path).name),
            executor_args=shlex.split(evaluator.executor_arguments),
            cmd_args=[*extra_args, str(location)]
        ).dict()
    )
    # add eval lock
    submission_fs.eval_lock.touch()


async def cancel_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname
    submission_fs = get_submission_dir(submission_id, as_obj=True)

    if is_remote:
        transfer_location = _settings.REMOTE_STORAGE.get(hostname)
        remote_submission_location = transfer_location / f"{submission_id}"
        logger.fetch_remote(hostname, remote_submission_location)

    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.canceled)
    submission_fs.eval_lock.unlink()


async def fail_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname
    submission_fs = get_submission_dir(submission_id, as_obj=True)

    # fetch results
    if is_remote:
        transfer_location = _settings.REMOTE_STORAGE.get(hostname)
        remote_submission_location = transfer_location / f"{submission_id}"
        logger.fetch_remote(hostname, remote_submission_location)

    # mark failed
    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.failed)
    submission_fs.eval_lock.unlink()


async def complete_evaluation(submission_id: str, hostname: str, logger: SubmissionLogger):
    is_remote = hostname != _settings.hostname
    out.log.debug(f"fetching items from remote: {is_remote}")
    submission_fs = get_submission_dir(submission_id, as_obj=True)

    # fetch results
    if is_remote:
        _fs.submissions.fetch_submission_from_remote(hostname, submission_id)
        out.log.debug(f"items successfully synced with remote {hostname}")

    # mark completed
    await challengesQ.update_submission_status(by_id=submission_id,
                                               status=schema.SubmissionStatus.completed)
    submission_fs.eval_lock.unlink()
    submission = await challengesQ.get_submission(by_id=submission_id)

    # re-build relevant leaderboards
    await leaderboards_lib.build_all_challenge(submission.track_id)
    logger.log("api extracted all relevant information for leaderboard")


async def delete_submission(*, by_id: Optional[str] = None, by_user: Optional[int] = None,
                            by_track: Optional[int] = None, by_status: Optional[int] = None) -> List[str]:
    """ delete an existing submission """
    async def delete_sub(sub_id: str):
        # drop from database
        await challengesQ.drop_submission(by_id=sub_id)

    if by_id is not None:
        await delete_sub(sub_id=by_id)
        # return list of id's deleted
        return [by_id]
    elif by_user is not None:
        sub_list = await challengesQ.list_submission(by_user=by_user)
        for sub in sub_list:
            await delete_sub(sub.id)

        # return list of id's deleted
        return [sub.id for sub in sub_list]
    elif by_track is not None:
        sub_list = await challengesQ.list_submission(by_track=by_track)
        for sub in sub_list:
            await delete_sub(sub.id)

        # return list of id's deleted
        return [sub.id for sub in sub_list]
    else:
        raise ValueError('No delete action was given')


async def archive_leaderboard_entries(submission_id: str):
    """ Archive if possible all leaderboard entries in a submission """
    submission = await challengesQ.get_submission(by_id=submission_id)
    leaderboards = await leaderboardQ.get_leaderboards(by_challenge_id=submission.track_id)

    for lead in leaderboards:
        if lead.external_entries is None:
            continue

        lead_entry = _fs.leaderboards.load_entry_from_sub(submission_id, lead.entry_file)
        if submission.author_label:
            lead_entry['author_label'] = submission.author_label

        with (lead.external_entries / f'{submission_id.replace("-", "")}.json').open("w") as fp:
            json.dump(lead_entry, fp)


async def multi_archive_leaderboard_entries(*, by_user: Optional[int] = None,
                                            by_track: Optional[int] = None,
                                            by_status: Optional[str] = None):
    """ Archive multiple submission entries by different selectors """

    if by_user:
        submissions = await challengesQ.list_submission(by_user=by_user)
    elif by_track:
        submissions = await challengesQ.list_submission(by_track=by_track)
    elif by_status:
        submissions = await challengesQ.list_submission(by_status=by_status)
    else:
        raise ValueError('Selector not specified')

    for sub in submissions:
        await archive_leaderboard_entries(sub.id)
