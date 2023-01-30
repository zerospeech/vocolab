import shutil

import json
from datetime import datetime
from pathlib import Path
from hmac import compare_digest
from typing import Dict, List, Union

from fastapi import UploadFile

from vocolab import get_settings, exc
from vocolab.db import models

from .._fs.commons import md5sum, rsync, ssh_exec, zip_folder

_settings = get_settings()


class SubmissionLogger:
    """ Class managing individual logging of submission life-cycle """

    @classmethod
    def log_filename(cls):
        return 'submission.log'

    @classmethod
    def eval_log_file(cls):
        return 'evaluation.log'

    def __init__(self, submission_id):
        self.id = submission_id
        self.submission_dir = get_submission_dir(submission_id)
        self.submission_log = self.submission_dir / self.log_filename()
        self.eval_log = self.submission_dir / self.eval_log_file()
        self.slurm_logfile = self.submission_dir / "slurm.log"
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
            fp.write(f"--> as multipart: {multipart}\n")

    @property
    def slurm_log(self):
        if self.slurm_logfile.is_file():
            with self.slurm_logfile.open() as fp:
                return fp.readlines()
        return []

    def append_eval(self, eval_output):
        with self.eval_log.open('a') as fp:
            fp.write(f"-------- start of evaluation output --------\n")
            fp.write(f"---> {datetime.now().isoformat()}")
            fp.write(f"{eval_output.rstrip()}\n")
            for line in self.slurm_log:
                fp.write(f"{line.strip()}\n")
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
        if self.submission_log.is_file():
            with self.submission_log.open('r') as fp:
                return fp.readlines()
        return []

    def fetch_remote(self, host, remote_submission_location):
        return_code, result = ssh_exec(host, [f'cat', f'{remote_submission_location}/{self.eval_log_file()}'])
        if return_code == 0:
            self.log(result, append=True)
        else:
            self.log(f"Failed to fetch {host}:{remote_submission_location}/{self.log_filename()} !!")


class SubmissionDir:
    """ Submission directory template class

    Class containing subfolders & files that are in a submission directory,
    this class is used to abstract usage of submission directories.

    """

    def __init__(self, root_dir: Path):
        self.__submission_root = root_dir

    @property
    def root(self) -> Path:
        """ Root directory of submission """
        return self.__submission_root

    @property
    def input(self) -> Path:
        """ Input directory containing base submission files (in unzipped form)"""
        return self.root / 'input'

    def has_input(self) -> bool:
        return self.input.is_dir()

    @property
    def scores(self) -> Path:
        """ the scores folders contains all the output files created by the evaluation process """
        return self.root / 'scores'

    def has_scores(self) -> bool:
        return self.scores.is_dir()

    @property
    def info_file(self) -> Path:
        """ info file contains meta data relative to the submission """
        return self.root / 'info.json'

    def has_info(self) -> bool:
        return self.info_file.is_file()

    @property
    def info(self) -> Union[Dict, List]:
        with self.info_file.open() as fp:
            return json.load(fp)

    @info.setter
    def info(self, data: Dict):
        with self.info_file.open('w') as fp:
            json.dump(data, fp, indent=4)

    @property
    def multipart_dir(self) -> Path:
        """ multipart dir contains the chunks & index for multipart uploads """
        return self.root / 'tmp'

    @property
    def multipart_index(self) -> Path:
        """ multipart index file contains info pertaining to multipart upload
         - split & merge manifest (order to merge the files)
         - checksums to verify upload & merge

        """
        return self.multipart_dir / 'upload.json'

    def is_multipart(self) -> bool:
        return self.multipart_dir.is_dir() and self.multipart_index.is_file()

    @property
    def singlepart(self):
        """ singlepart upload is included into a zip file """
        return self.root / "input.zip"

    @property
    def singlepart_hash(self) -> Path:
        """ singlepart upload can be verified by the checksum inside this file """
        return self.root / 'archive.hash'

    def has_singlepart(self) -> bool:
        return self.singlepart.is_file()

    @property
    def upload_lock(self) -> Path:
        """ a lockfile locking the submission while upload has not completed """
        return self.root / 'upload.lock'

    @property
    def eval_lock(self) -> Path:
        """ a lockfile locking the submission while evaluation is ongoing """
        return self.root / 'eval.lock'

    @property
    def error_lock(self) -> Path:
        """ a lockfile locking the submission while evaluation is ongoing """
        return self.root / 'error.lock'

    @property
    def clean_lock(self) -> Path:
        """ a lockfile marking the submission for deletion """
        return self.root / 'clean.lock'

    @property
    def interrupted_lock(self) -> Path:
        """ a lockfile to signify that a process was running and was interrupted """
        return self.root / 'interrupted.lock'

    def clean_all_locks(self):
        """ Remove all lock files in submission"""
        self.upload_lock.unlink(missing_ok=True)
        self.eval_lock.unlink(missing_ok=True)
        self.error_lock.unlink(missing_ok=True)
        self.interrupted_lock.unlink(missing_ok=True)
        self.clean_lock.unlink(missing_ok=True)

    def get_log_handler(self) -> SubmissionLogger:
        """ build the SubmissionLogger class that allows to log submission relative events """
        return SubmissionLogger(self.root.name)


def get_submission_dir(submission_id: str, as_obj: bool = False) -> Union[Path, SubmissionDir]:
    """ Returns the directory containing the submission data based on the given id"""
    if as_obj:
        return SubmissionDir(_settings.submission_dir / submission_id)
    return _settings.submission_dir / submission_id


def make_submission_on_disk(submission_id: str, username: str, track: str, meta: models.api.NewSubmissionRequest):
    """ Creates a template folder with all the necessary folders / info to create a new submission

        - scores/ : folder used for evaluation output
        - input/ : folder used for unzipped submission files
        - tmp/ : temporary folder for multipart uploads (contains chunks & index)
        - upload.lock : lockfile used to declare the submission has not finished uploading
    """
    submission_dir: SubmissionDir = get_submission_dir(submission_id, as_obj=True)
    submission_dir.root.mkdir(parents=True, exist_ok=True)
    submission_dir.scores.mkdir(exist_ok=True)
    submission_dir.input.mkdir(exist_ok=True)
    submission_dir.info = {
        'user': username,
        'track': track,
        "submission_id": submission_id,
        "submitted-at": f"{datetime.now().isoformat()}"
    }

    if meta.multipart:
        submission_dir.multipart_dir.mkdir(exist_ok=True)
        # add tmp to data
        upload_data = meta.dict()
        upload_data["tmp_location"] = str(submission_dir.multipart_dir)
        # write info to disk
        with submission_dir.multipart_index.open('w') as fp:
            json.dump(upload_data, fp)
    else:
        with submission_dir.singlepart_hash.open('w') as fp:
            fp.write(meta.hash)

    sub_log = SubmissionLogger(submission_id)
    sub_log.header(username, track, meta.multipart)

    # create upload lockfile
    submission_dir.upload_lock.touch()


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
    submission_dir = get_submission_dir(submission_id, as_obj=True)
    with submission_dir.multipart_index.open() as fp:
        mf_data = models.file_split.SplitManifest(**json.load(fp))

    # lookup hash
    file_meta = next(((val.file_hash, ind) for ind, val in enumerate(mf_data.index) if val.file_name == filename), None)
    # file not found in submission => raise exception
    if file_meta is None:
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise exc.ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    f_hash, file_index = file_meta

    # Add the part
    file_part = submission_dir.multipart_dir / f"{filename}"
    with file_part.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    calc_hash = md5sum(submission_dir.multipart_dir / f"{filename}")
    if not compare_digest(calc_hash, f_hash):
        # remove file and throw exception
        (submission_dir.multipart_dir / f"{filename}").unlink()
        data = f"failed hash comparison" \
               f"file: {submission_dir.multipart_dir / f'{filename}'} with hash {calc_hash}" \
               f"on record found : {filename} with hash {f_hash}"
        logger.log(f"(ERROR) {data}, upload canceled!!")
        raise exc.ValueNotValid("Hash of part does not match given hash", data=data)

    # up count of received parts
    mf_data.received.append(mf_data.index[file_index])

    # write new metadata
    with submission_dir.multipart_index.open('w') as fp:
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
    submission_dir = get_submission_dir(submission_id, as_obj=True)
    logger = SubmissionLogger(submission_id)
    logger.log(f"adding a new part to upload: {filename}")

    # hash not found in submission => raise exception
    if not submission_dir.singlepart_hash.is_file():
        logger.log(f"(ERROR) file {filename} was not found in manifest, upload canceled!!")
        raise exc.ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    with submission_dir.singlepart_hash.open() as fp:
        f_hash = fp.read().replace('\n', '')

    # Add the part
    with submission_dir.singlepart.open('wb') as fp:
        for d in data.file:
            fp.write(d)

    # Verify checksum
    if not md5sum(submission_dir.singlepart) == f_hash:
        raise exc.ValueNotValid("Hash does not match expected!")

    logger.log(f" --> file was uploaded successfully", append=True)
    # completed => True
    return True, []


def transfer_submission_to_remote(host: str, submission_id: str):
    """ Transfer a submission to worker storage """
    # build variables
    is_remote = host != _settings.app_options.hostname
    transfer_location = _settings.task_queue_options.REMOTE_STORAGE.get(host)
    local_folder = get_submission_dir(submission_id)

    if (not is_remote) and (transfer_location == _settings.submission_dir):
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
    is_remote = host != _settings.app_options.hostname
    transfer_location = _settings.task_queue_options.REMOTE_STORAGE.get(host)
    local_folder = get_submission_dir(submission_id)

    if (not is_remote) and (transfer_location == _settings.submission_dir):
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


def archive_submission_files(submission_id: str) -> Path:
    """ Archive submission files as a zipped archive """
    archive_location = _settings.submission_archive_dir
    submission_location = get_submission_dir(submission_id)

    # create archive of submission in archive dir
    zip_folder((archive_location / f'{submission_id}.zip'), submission_location)

    # delete files in submission
    shutil.rmtree(submission_location)

    return archive_location / f'{submission_id}.zip'


def delete_submission_files(submission_id: str):
    """ Delete submission files """
    submission_location = get_submission_dir(submission_id)
    shutil.rmtree(submission_location)
