import asyncio
import json
from pathlib import Path
import shutil
from typing import TYPE_CHECKING
from hmac import compare_digest

from fastapi import UploadFile

from zerospeech.settings import get_settings
from zerospeech.utils import misc
from zerospeech.exc import ResourceRequestedNotFound, InvalidRequest, ValueNotValid
from zerospeech.db.q import challenges as q_challenge
from zerospeech.utils.submissions.log import SubmissionLogger

if TYPE_CHECKING:
    from zerospeech.api.models import NewSubmissionRequest

_settings = get_settings()


def get_submission_dir(submission_id: str) -> Path:
    """ Returns the directory containing the submission data based on the given id"""
    return _settings.SUBMISSION_DIR / submission_id


def make_submission_on_disk(submission_id: str, username: str, track: str, meta: "NewSubmissionRequest"):
    """ Creates a template folder with all the necessary folders / info to create a new submission

        - logs/ : folder to write evaluation logs
        - scores/ : folder used for evaluation output
        - input/ : folder used for unzipped submission files
        - tmp/ : temporary folder for multipart uploads (contains chunks & index)
        - upload.lock : lockfile used to declare the submission has not finished uploading
    """
    folder = get_submission_dir(submission_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'scores').mkdir(exist_ok=True)
    (folder / 'input').mkdir(exist_ok=True)
    info = {
        'user': username,
        'track': track,
        "submission_id": submission_id
    }
    with (folder / 'info.json').open('w') as fp:
        json.dump(info, fp)

    if meta.multipart:
        (folder / 'tmp').mkdir(exist_ok=True)
        # add tmp to data
        upload_data = meta.dict()
        upload_data["tmp_location"] = str(folder / 'tmp')
        # write info to disk
        with (folder / 'tmp' / 'upload.json').open('w') as fp:
            json.dump(upload_data, fp)
    else:
        with (folder / 'archive.hash').open('w') as fp:
            fp.write(meta.hash)

    sub_log = SubmissionLogger(submission_id)
    sub_log.header(username, track, meta.multipart)

    (folder / 'upload.lock').touch()


def multipart_add(submission_id: str, filename: str, data: UploadFile):
    logger = SubmissionLogger(submission_id)
    logger.log(f"adding a new part to upload: tmp/{filename}")
    folder = get_submission_dir(submission_id)
    with (folder / 'tmp' / 'upload.json').open() as fp:
        mf_data = misc.SplitManifest(**json.load(fp))

    # lookup hash
    file_meta = next(((val.file_hash, ind) for ind, val in enumerate(mf_data.index) if val.file_name == filename), None)
    # file not found in submission => raise exception
    if file_meta is None:
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    f_hash, file_index = file_meta

    # Add the part
    file_part = (folder / "tmp" / f"{filename}")
    with file_part.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    calc_hash = misc.md5sum((folder / "tmp" / f"{filename}"))
    if not compare_digest(calc_hash, f_hash):
        # remove file and throw exception
        (folder / "tmp" / f"{filename}").unlink()
        data = f"failed hash comparison" \
               f"file: {folder / 'tmp' / f'{filename}'} with hash {calc_hash}" \
               f"on record found : {filename} with hash {f_hash}"
        logger.log(f"(ERROR) {data}, upload canceled!!")
        raise ValueNotValid("Hash of part does not match given hash", data=data)

    # up count of received parts
    mf_data.received.append(mf_data.index[file_index])

    # write new metadata
    with (folder / 'tmp' / 'upload.json').open('w') as fp:
        fp.write(mf_data.json())

    remaining = list(set(mf_data.index) - set(mf_data.received))
    logger.log(f" --> part was added successfully", append=True)

    # return --> is_completed
    return len(mf_data.received) == len(mf_data.index), remaining


def singlepart_add(submission_id: str, filename: str, data: UploadFile):
    folder = get_submission_dir(submission_id)
    logger = SubmissionLogger(submission_id)
    logger.log(f"adding a new part to upload: {filename}")

    # hash not found in submission => raise exception
    if not (folder / 'archive.hash').is_file():
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    with (folder / 'archive.hash').open() as fp:
        f_hash = fp.read().replace('\n', '')

    # Add the part
    file_part = (folder / f"input.zip")
    with file_part.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    if not misc.md5sum((folder / "input.zip")) == f_hash:
        raise ValueNotValid("Hash does not match expected!")

    logger.log(f" --> file was uploaded successfully", append=True)
    # completed => True
    return True, []


def add_part(submission_id: str, filename: str, data: UploadFile):
    logger = SubmissionLogger(submission_id)
    folder = get_submission_dir(submission_id)

    # check existing submission
    if not folder.is_dir():
        raise ResourceRequestedNotFound(f"submission ({submission_id}) does not exist!!")

    # check submission status set to upload
    if not (folder / 'upload.lock').is_file():
        raise InvalidRequest(f"submission ({submission_id}) does not accept any more parts")

    # check if multipart_upload
    if (folder / 'tmp').is_dir() and (folder / 'tmp/upload.json').is_file():
        completed, expecting_list = multipart_add(submission_id, filename, data)
    else:
        completed, expecting_list = singlepart_add(submission_id, filename, data)

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
    folder = get_submission_dir(submission_id)

    if (folder / 'tmp').is_dir() and (folder / 'tmp/upload.json').is_file():
        with (folder / 'tmp' / 'upload.json').open() as fp:
            mf_data = misc.SplitManifest(**json.load(fp))

        archive = misc.merge_zip(mf_data, folder)
    else:
        archive = folder / 'input.zip'

    misc.unzip(archive, folder / 'input')
    # mark task as uploaded to the database
    asyncio.run(
        q_challenge.update_submission_status(submission_id, q_challenge.schema.SubmissionStatus.uploaded)
    )
    # todo start eval task
    if with_eval:
        pass


def transfer_submission(host: str, submission_id: str):
    """ Transfer a submission to worker storage """
    logger = SubmissionLogger(submission_id)
    folder = get_submission_dir(submission_id)
    remote_location = _settings.REMOTE_STORAGE.get(host) / submission_id / 'input'
    # create remote folder
    code, _ = misc.ssh_exec(host, ['mkdir', '-p', f"{remote_location}"])
    if code != 0:
        logger.log(f"failed to write on {host}")
        raise ValueError(f"Failed to copy files to host {host}")

    res = misc.scp((folder / 'input'), host, remote_location, recursive=True)
    if res.returncode == 0:
        logger.log(f"copied files from {folder/ 'input'} to {host} for processing.")
        return remote_location
    else:
        logger.log(f"failed to copy {folder / 'input'} to {host} for processing.")
        logger.log(res.stderr.decode())
        raise ValueError(f"Failed to copy files to host {host}")

