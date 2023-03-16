import functools
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from pydantic import BaseModel

from vocolab import get_settings, exc
from .logs import SubmissionLogger
from .upload import MultipartUploadHandler, SinglepartUploadHandler, ManifestIndexItem
from ..commons import unzip, ssh_exec, rsync, zip_folder, scp
from ...data.models.api import SubmissionRequestFileIndexItem

_settings = get_settings()


class SubmissionInfo(BaseModel):
    model_id: str
    username: str
    benchmark_label: str
    submission_id: str
    created_at: datetime
    leaderboard_entry: Optional[str]


class SubmissionDir(BaseModel, arbitrary_types_allowed=True):
    """ Handler interfacing a submission directory stored on disk """
    root_dir: Path

    @classmethod
    def load(cls, model_id: str, submission_id: str):
        """ Load item from model-id & submission-id"""
        root = _settings.submission_dir / model_id / submission_id
        if not root.is_dir():
            raise FileNotFoundError(f'Submission {model_id}/{submission_id} does not exist')
        return cls(root_dir=root)

    @property
    def submission_id(self) -> str:
        """ Returns the submission id """
        return self.root_dir.name

    @property
    def content_location(self) -> Path:
        return self.root_dir / 'content'

    def has_content(self) -> bool:
        """ Check if submission has content """
        return self.content_location.is_dir() and any(Path(self.content_location).iterdir())

    @property
    def scores(self) -> Path:
        """ the scores folders contains all the output files created by the evaluation process """
        return self.content_location / 'scores'

    def has_scores(self) -> bool:
        return self.scores.is_dir()

    @property
    def info_file(self) -> Path:
        """ info file contains meta data relative to the submission """
        return self.root_dir / 'info.json'

    def has_info(self) -> bool:
        """ Check whether info file is present"""
        return self.info_file.is_file()

    @functools.lru_cache()
    def info(self) -> SubmissionInfo:
        """ Load submission information """
        with self.info_file.open() as fp:
            return SubmissionInfo.parse_obj(json.load(fp))

    @property
    def multipart_dir(self) -> Path:
        """ multipart dir contains the chunks & index for multipart uploads """
        return self.root_dir / '.parts'

    @property
    def multipart_index_file(self) -> Path:
        """ multipart index file contains info pertaining to multipart upload
         - split & merge manifest (order to merge the files)
         - checksums to verify upload & merge
        """
        return self.multipart_dir / 'upload.json'

    def is_multipart(self) -> bool:
        """ Check whether file was uploaded as multipart """
        return self.multipart_dir.is_dir() and self.multipart_index_file.is_file()

    @property
    def upload_lock(self) -> Path:
        """ a lockfile locking the submission while upload has not completed """
        return self.root_dir / 'upload.lock'

    @property
    def content_archive_hash_file(self) -> Path:
        return self.root_dir / 'archive.hash'

    @property
    def eval_lock(self) -> Path:
        """ a lockfile locking the submission while evaluation is ongoing """
        return self.root_dir / 'eval.lock'

    @property
    def error_lock(self) -> Path:
        """ a lockfile locking the submission while evaluation is ongoing """
        return self.root_dir / 'error.lock'

    @property
    def clean_lock(self) -> Path:
        """ a lockfile marking the submission for deletion """
        return self.root_dir / 'clean.lock'

    @property
    def interrupted_lock(self) -> Path:
        """ a lockfile to signify that a process was running and was interrupted """
        return self.root_dir / 'interrupted.lock'

    def clean_all_locks(self):
        """ Remove all lock files in submission"""
        self.upload_lock.unlink(missing_ok=True)
        self.eval_lock.unlink(missing_ok=True)
        self.error_lock.unlink(missing_ok=True)
        self.interrupted_lock.unlink(missing_ok=True)
        self.clean_lock.unlink(missing_ok=True)

    @property
    def log_handler(self) -> SubmissionLogger:
        """ build the SubmissionLogger class that allows to log submission relative events """
        return SubmissionLogger(root_dir=self.root_dir)

    def get_leaderboard_items(self):
        if not self.has_info():
            raise ValueError('Submission has no info index')
        return self.info.leaderboard_entries

    def add_content(self, file_name: str, data: UploadFile):
        """ Add content to the submission
        *) multipart:
            - add part to the tmp folder
            - check if completed
                - if completed merge parts
        *) singlepart:
            - add uploaded data to the submission

        Multipart is completed when all the parts have been successfully uploaded
        Singlepart is completed when the target archive has been successfully uploaded

        If upload is completed --> unzip content into the content folder.
        """
        if self.is_multipart():
            """ Multipart upload """
            handler = MultipartUploadHandler.load_from_index(self.multipart_index_file)
            handler.add_part(
                logger=self.log_handler,
                file_name=file_name,
                data=data
            )
            handler.dump_to_index(self.multipart_index_file)
        else:
            """ Single part upload """
            handler = SinglepartUploadHandler(root_dir=self.root_dir)
            handler.write_data(
                logger=self.log_handler,
                file_name=file_name,
                data=data
            )

        if handler.completed():
            return True, []
        return False, handler.remaining_items

    def complete_upload(self):
        """ Actions to perform after upload has completed on a submission (extract files, update metadata, etc)"""
        logger = self.log_handler
        if self.is_multipart():
            handler = MultipartUploadHandler.load_from_index(self.multipart_index_file)
            if not handler.completed():
                raise exc.FailedOperation(f'Cannot Complete incomplete submission {self.submission_id} !!!')

            # merge parts to target archive
            logger.log(f"upload of parts for {self.submission_id} completed, merging parts...")
            handler.merge_parts()
            logger.log("parts merged successfully")
        else:
            handler = SinglepartUploadHandler(root_dir=self.root_dir)
            if not handler.completed():
                raise exc.FailedOperation(f'Cannot Complete incomplete submission {self.submission_id} !!!')

            logger.log(f"upload for {self.submission_id} completed")

        # unzip archive to content location
        logger.log(f"unzipping archive {handler.target_file} into {self.content_location}")
        unzip(handler.target_file, self.content_location)


    def send_content(self, hostname: str) -> Path:
        """ Send content to a remote host for evaluation (return target location) """
        is_remote = hostname != _settings.app_options.hostname
        transfer_root_dir = _settings.task_queue_options.REMOTE_STORAGE.get(hostname)
        model_id = self.info.model_id
        remote_submission_dir = transfer_root_dir / model_id / self.submission_id
        logger = self.log_handler

        # if host is local & submission dir is current, do nothing
        if (not is_remote) and (transfer_root_dir == _settings.submission_dir):
            return self.root_dir

        code, _ = ssh_exec(hostname, ['mkdir', '-p', f'{remote_submission_dir}'])
        if code != 0:
            logger.log(f"failed to write on {hostname}")
            raise ValueError(f"No write permissions on {hostname}")

        # sync files
        res = rsync(src=self.root_dir, dest_host=hostname, dest=remote_submission_dir)
        if res.returncode == 0:
            logger.log(f"copied files from {self.root_dir} to {hostname} for processing.")
            return remote_submission_dir
        else:
            logger.log(f"failed to copy {self.root_dir} to {hostname} for processing.")
            logger.log(res.stderr.decode())
            raise ValueError(f"Failed to copy files to host {hostname}")

    def fetch_content(self, hostname: str):
        """ Fetch updated content from remote (after evaluation) """
        is_remote = hostname != _settings.app_options.hostname
        transfer_root_dir = _settings.task_queue_options.REMOTE_STORAGE.get(hostname)
        model_id = self.info.model_id
        remote_submission_dir = transfer_root_dir / model_id / self.submission_id
        logger = self.log_handler

        # if host is local & submission dir is current, do nothing
        if (not is_remote) and (transfer_root_dir == _settings.submission_dir):
            return self.root_dir

        # fetch log files
        logger.fetch_remote(hostname, remote_submission_dir)

        # sync files
        res = rsync(src_host=hostname, src=remote_submission_dir, dest=self.root_dir)

        if res.returncode == 0:
            logger.log(f"fetched result files from {hostname} to {self.root_dir}")
            return self.root_dir
        else:
            logger.log(f"failed to fetch results from {hostname} to {self.root_dir}.")
            logger.log(res.stderr.decode())
            raise ValueError(f"Failed to copy files from host {hostname}")

    def __archive_zip(self):
        """ Archive submission as zip """
        if _settings.remote_archive:
            host = _settings.ARCHIVE_HOST
            with _settings.get_temp_dir() as tmp:
                archive_file = tmp / f'{self.info.model_id}_{self.info.submission_id}'
                zip_folder(archive_file=archive_file, location=self.root_dir)
                res = scp(src=archive_file, host=host, dest=_settings.submission_archive_dir)
                if res.returncode != 0:
                    raise ValueError(f"Failed to transfer to {host}")
        else:
            """ Archive files to local archive as a zip file"""
            zip_folder(
                archive_file=self.root_dir / f'{self.info.model_id}_{self.info.submission_id}',
                location=self.root_dir
            )

    def __archive_raw(self):
        if _settings.remote_archive:
            host = _settings.ARCHIVE_HOST
            code, _ = ssh_exec(host, ['mkdir', '-p', f"{self.root_dir}"])
            if code != 0:
                raise ValueError(f"No write permissions on {host}")

            res = rsync(src=self.root_dir, dest_host=host, dest=self.root_dir)
            if res.returncode != 0:
                raise ValueError(f"Failed to copy files to host {host}")

        else:
            _res = rsync(src=self.root_dir, dest=self.root_dir)
            if _res.returncode != 0:
                raise ValueError("Failed to copy files to archive")

    def archive(self, zip_files: bool = False):
        """Transfer submission to archive """
        if zip_files:
            self.__archive_zip()
        else:
            self.__archive_raw()

    def remove_all(self):
        """ Remove all files related to this submission """
        shutil.rmtree(self.root_dir)


class ModelDir(BaseModel):
    root_dir: Path

    @property
    def label(self):
        return self.root_dir.name

    @classmethod
    def make(cls, model_id: str):
        root = _settings.submission_dir / model_id
        root.mkdir(exist_ok=True, parents=True)

    @classmethod
    def load(cls, model_id: str):
        root = _settings.submission_dir / model_id

        if not root.is_dir():
            raise FileNotFoundError('Model Folder not found')

        return cls(root_dir=root)

    def make_submission(
            self, submission_id: str, benchmark_label: str, auto_eval: bool,
            username: str, filehash: str, has_scores: bool, multipart: bool,
            index: Optional[List[SubmissionRequestFileIndexItem]],
            leaderboard_file: Optional[str] = None
    ) -> SubmissionDir:
        root_dir = self.root_dir / submission_id
        if root_dir.is_dir():
            raise FileExistsError(f'Submission {submission_id} cannot be created as it already exists')
        # create the dir
        root_dir.mkdir()
        submission_dir = SubmissionDir(root_dir=root_dir)
        submission_dir.content_location.mkdir()

        # Submission generic info
        sub_info = SubmissionInfo(
            model_id=self.label,
            username=username,
            benchmark_label=benchmark_label,
            submission_id=submission_id,
            created_at=datetime.now(),
            leaderboard_entry=leaderboard_file
        )
        # save info to file
        with submission_dir.info_file.open('w') as fp:
            fp.write(sub_info.json(indent=4))

        if multipart:
            if len(index) <= 0:
                raise ValueError('Parts list is empty')
            submission_dir.multipart_dir.mkdir(exist_ok=True)
            upload_handler = MultipartUploadHandler(
                store_location=submission_dir.multipart_dir,
                target_location=submission_dir.root_dir,
                merge_hash=filehash,
                index=[ManifestIndexItem.from_api(i) for i in index]
            )
            with submission_dir.multipart_index_file.open('w') as fp:
                fp.write(
                    upload_handler.json(include={'index'}, indent=4)
                )
        else:
            with submission_dir.content_archive_hash_file.open('w') as fp:
                fp.write(filehash)

        submission_dir.log_handler.header(
            who=username,
            task=benchmark_label,
            multipart=multipart,
            has_scores=has_scores,
            auto_eval=auto_eval
        )
        return submission_dir

    @property
    def submissions(self) -> List[SubmissionDir]:
        return [
            SubmissionDir.load(self.label, sub_id.name)
            for sub_id in self.root_dir.iterdir()
            if sub_id.is_dir()
        ]

    def get_submission(self, submission_id: str):
        return SubmissionDir.load(self.label, submission_id)
