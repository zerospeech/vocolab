import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import UploadFile
from pydantic import BaseModel

from ...db import models
from ...settings import get_settings
from .logs import SubmissionLogger
from .upload import MultipartUploadHandler, SinglepartUploadHandler

_settings = get_settings()


class SubmissionInfo(BaseModel):
    model_id: str
    username: str
    track_id: int
    track_label: str
    submission_id: str
    created_at: datetime
    leaderboard_entries: Dict[str, Path]


class SubmissionDir(BaseModel):
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
    def content(self) -> Path:
        return self.root_dir / 'content'

    def has_input(self) -> bool:
        return self.content.is_dir()

    @property
    def scores(self) -> Path:
        """ the scores folders contains all the output files created by the evaluation process """
        return self.content / 'scores'

    def has_scores(self) -> bool:
        return self.scores.is_dir()

    @property
    def info_file(self) -> Path:
        """ info file contains meta data relative to the submission """
        return self.root_dir / 'info.json'

    def has_info(self) -> bool:
        """ Check whether info file is present"""
        return self.info_file.is_file()

    @property
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

    def get_log_handler(self) -> SubmissionLogger:
        """ build the SubmissionLogger class that allows to log submission relative events """
        return SubmissionLogger(root_dir=self.root_dir)


    def add_content(self, file_name: str, file_size: int, file_hash: str, data: UploadFile):
        """ todo: write method description """
        if self.is_multipart():
            # Multipart content
            handler = MultipartUploadHandler.load_from_index(self.multipart_index_file)
            handler.add_part(
                logger=self.get_log_handler(),
                file_name=file_name,
                file_size=file_size,
                file_hash=file_hash,
                data=data
            )
            handler.dump_to_index(self.multipart_index_file)

            if handler.completed():
                handler.merge_parts()
            else:
                # todo return missing? remaining ? something
                pass
        else:
            # singlepart content
            # TODO: continue this section here ......
            handler = SinglepartUploadHandler(root_dir=self.root_dir)
            handler.write_data(file_name=file_name, )





class ModelDir(BaseModel):
    root_dir: Path

    @property
    def label(self):
        return self.root_dir.name

    @classmethod
    def load(cls, model_id: str):
        root = _settings.submission_dir / model_id

        if not root.is_dir():
            raise FileNotFoundError(f'Model {model_id} does not exist')
        return cls(root_dir=root)

    def make_submission(self, submission_id: str, auto_eval: bool, request_meta: models.api.NewSubmissionRequest):
        root_dir = self.root_dir / submission_id
        if root_dir.is_dir():
            raise FileExistsError(f'Submission {submission_id} cannot be created as it already exists')
        # create the dir
        root_dir.mkdir()
        submission_dir = SubmissionDir(root_dir=root_dir)
        submission_dir.content.mkdir()

        sub_info = SubmissionInfo(
            username=request_meta.username,
            track_id=request_meta.track_id,
            track_label=request_meta.track_label,
            submission_id=submission_id,
            created_at=datetime.now(),
            leaderboard_entries=request_meta.leaderboards
        )

        # todo save info as file

        if request_meta.multipart:
            submission_dir.multipart_dir.mkdir(exist_ok=True)
            # todo build class for multipart index
        else:
            with submission_dir.singlepart_hash_file.open('w') as fp:
                fp.write(request_meta.hash)

        submission_dir.get_log_handler().header(
            who=request_meta.username,
            task=request_meta.track_label,
            multipart=request_meta.multipart,
            has_scores=request_meta.has_scores,
            auto_eval=auto_eval
        )

        # create upload lockfile
        submission_dir.upload_lock.touch()

    @property
    def submissions(self) -> List[SubmissionDir]:
        return [
            SubmissionDir.load(self.label, sub_id.name)
            for sub_id in self.root_dir.iterdir()
            if sub_id.is_dir()
        ]

    def get_submission(self, submission_id: str):
        return SubmissionDir.load(self.label, submission_id)
