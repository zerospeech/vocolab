import asyncio
import json

from fastapi import UploadFile

from zerospeech import exc
from zerospeech.db import models, schema
from zerospeech.db.q import challengesQ
from zerospeech.lib import _fs
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
    # todo start eval task
    if with_eval:
        pass


def evaluate(submission_id: str, logger):
    """ ... """
    return None
