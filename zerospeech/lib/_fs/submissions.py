import json
from datetime import datetime
from pathlib import Path
from hmac import compare_digest

from fastapi import UploadFile

from zerospeech import get_settings, exc
from zerospeech.db import models

from .commons import md5sum, rsync, ssh_exec

_settings = get_settings()


def get_submission_dir(submission_id: str) -> Path:
    """ Returns the directory containing the submission data based on the given id"""
    return _settings.SUBMISSION_DIR / submission_id


class SubmissionLogger:
    """ Class managing individual logging of submission life-cycle """

    @classmethod
    def log_filename(cls):
        return 'submission.log'

    def __init__(self, submission_id):
        self.id = submission_id
        self.submission_dir = get_submission_dir(submission_id)
        self.submission_log = self.submission_dir / self.log_filename()
        self.fp = None

    def __enter__(self):
        self.fp = self.submission_log.open('a')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp is not None:
            self.fp.close()
            self.fp = None

    @staticmethod
    def when():
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def header(self, who, what, multipart):
        with self.submission_log.open('w') as fp:
            fp.write(f"[{self.when()}]: Submission {self.id} was created\n")
            fp.write(f"--> user: {who}\n")
            fp.write(f"--> challenge: {what}\n")
            fp.write(f"--> as multipart: {multipart}")

    def append_eval(self, eval_output):
        with self.submission_log.open('a') as fp:
            fp.write(f"-------- start of evaluation output --------\n")
            fp.write(f"{eval_output.rstrip()}\n")
            fp.write(f"-------- end of evaluation output ----------\n")

    def log(self, msg, append=False):
        if not append:
            msg = f"[{self.when()}] {msg}"

        if self.fp:
            self.fp.write(f"{msg}\n")
        else:
            with self.submission_log.open('a') as fp:
                fp.write(f"{msg}\n")

    def get_text(self):
        with self.submission_log.open('r') as fp:
            return fp.readlines()

    def fetch_remote(self, host, remote_submission_location):
        return_code, result = ssh_exec(host, [f'cat', f'{remote_submission_location}/{self.log_filename()}'])
        if return_code == 0:
            self.log(result, append=True)
        else:
            self.log(f"Failed to fetch {host}:{remote_submission_location}/{self.log_filename()} !!")


def make_submission_on_disk(submission_id: str, username: str, track: str, meta: models.api.NewSubmissionRequest):
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
    """ Add a part to a multipart upload type submission.

    - Write the data into a file inside the submission folder.
    - Check if upload has finished (all parts in manifest have been uploaded)
    - If upload not completed return missing list
    - If upload completed finalise upload by merging & extracting submission.

    :param submission_id: The unique id of the submission
    :param filename: The name of the target uploaded file
    :param data: The binary data to write into the file
    :return: completed, list_remaining
        completed a boolean signifying if the upload is completed
        list_remaining: a list of the remaining files to complete the upload
    :raises
        - JSONError, ValidationError: If manifest is not properly formatted
        - ResourceRequestedNotFound: if file not present in the manifest
        - ValueNotValid if md5 hash of file does not match md5 recorded in the manifest
    """
    logger = SubmissionLogger(submission_id)
    logger.log(f"adding a new part to upload: tmp/{filename}")
    folder = get_submission_dir(submission_id)
    with (folder / 'tmp' / 'upload.json').open() as fp:
        mf_data = models.file_split.SplitManifest(**json.load(fp))

    # lookup hash
    file_meta = next(((val.file_hash, ind) for ind, val in enumerate(mf_data.index) if val.file_name == filename), None)
    # file not found in submission => raise exception
    if file_meta is None:
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise exc.ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    f_hash, file_index = file_meta

    # Add the part
    file_part = (folder / "tmp" / f"{filename}")
    with file_part.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    calc_hash = md5sum((folder / "tmp" / f"{filename}"))
    if not compare_digest(calc_hash, f_hash):
        # remove file and throw exception
        (folder / "tmp" / f"{filename}").unlink()
        data = f"failed hash comparison" \
               f"file: {folder / 'tmp' / f'{filename}'} with hash {calc_hash}" \
               f"on record found : {filename} with hash {f_hash}"
        logger.log(f"(ERROR) {data}, upload canceled!!")
        raise exc.ValueNotValid("Hash of part does not match given hash", data=data)

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
    """ Upload data into submission. (single file upload, no splitting)

    - Write the data into a file inside the submission folder.
    - Finalise upload by extracting submission.

    :param submission_id: The unique id of the submission
    :param filename: The name of the target uploaded file
    :param data: The binary data to write into the file
    :return: True, []
        Return type is created to match multipart_add function
        Singlepart is always completed since it only requires one file.
    :raises
        - JSONError, ValidationError: If manifest is not properly formatted
        - ResourceRequestedNotFound: if file not present in the manifest
        - ValueNotValid if md5 hash of file does not match md5 recorded in the manifest
    """
    folder = get_submission_dir(submission_id)
    logger = SubmissionLogger(submission_id)
    logger.log(f"adding a new part to upload: {filename}")

    # hash not found in submission => raise exception
    if not (folder / 'archive.hash').is_file():
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise exc.ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    with (folder / 'archive.hash').open() as fp:
        f_hash = fp.read().replace('\n', '')

    # Add the part
    file_part = (folder / f"input.zip")
    with file_part.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    if not md5sum((folder / "input.zip")) == f_hash:
        raise exc.ValueNotValid("Hash does not match expected!")

    logger.log(f" --> file was uploaded successfully", append=True)
    # completed => True
    return True, []


def transfer_submission_to_remote(host: str, submission_id: str):
    """ Transfer a submission to worker storage """
    # build variables
    is_remote = host != _settings.hostname
    transfer_location = _settings.REMOTE_STORAGE.get(host)
    local_folder = get_submission_dir(submission_id)

    if (not is_remote) and (transfer_location == _settings.SUBMISSION_DIR):
        return local_folder

    logger = SubmissionLogger(submission_id)
    remote_submission_location = transfer_location / f"{submission_id}"

    # create remote folder
    code, _ = ssh_exec(host, ['mkdir', '-p', f"{remote_submission_location}"])
    if code != 0:
        logger.log(f"failed to write on {host}")
        raise ValueError(f"No write permissions on {host}")

    # sync files
    res = rsync(src=local_folder, dest_host=host, dest=remote_submission_location)

    if res.returncode == 0:
        logger.log(f"copied files from {local_folder} to {host} for processing.")
        return remote_submission_location
    else:
        logger.log(f"failed to copy {local_folder} to {host} for processing.")
        logger.log(res.stderr.decode())
        raise ValueError(f"Failed to copy files to host {host}")


def fetch_submission_from_remote(host: str, submission_id: str):
    """ Download a submission from worker storage """
    # build variables
    is_remote = host != _settings.hostname
    transfer_location = _settings.REMOTE_STORAGE.get(host)
    local_folder = get_submission_dir(submission_id)

    if (not is_remote) and (transfer_location == _settings.SUBMISSION_DIR):
        return local_folder

    logger = SubmissionLogger(submission_id)
    remote_submission_location = transfer_location / f"{submission_id}"

    # fetch log files
    logger.fetch_remote(host, remote_submission_location)

    # sync files
    res = rsync(src_host=host, src=remote_submission_location, dest=local_folder)

    if res.returncode == 0:
        logger.log(f"fetched result files from {host} to {local_folder}")
        return local_folder
    else:
        logger.log(f"failed to fetch results from {host} to {local_folder}.")
        logger.log(res.stderr.decode())
        raise ValueError(f"Failed to copy files from host {host}")


