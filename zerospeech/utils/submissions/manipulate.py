import json
from pathlib import Path
import shutil
from tempfile import SpooledTemporaryFile
from typing import TYPE_CHECKING

from zerospeech.settings import get_settings
from zerospeech.utils import misc
from zerospeech.exc import ResourceRequestedNotFound, InvalidRequest, ValueNotValid

if TYPE_CHECKING:
    from zerospeech.api.v1.models import NewSubmissionRequest

_settings = get_settings()


def make_submission_on_disk(submission_id: str, username: str, track: str, meta: "NewSubmissionRequest"):
    """ Creates a template folder with all the necessary folders / info to create a new submission

        - logs/ : folder to write evaluation logs
        - scores/ : folder used for evaluation output
        - input/ : folder used for unzipped submission files
        - tmp/ : temporary folder for multipart uploads (contains chunks & index)
        - upload.lock : lockfile used to declare the submission has not finished uploading
    """
    folder = (_settings.USER_DATA_DIR / 'submissions' / submission_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'logs').mkdir(exist_ok=True)
    (folder / 'scores').mkdir(exist_ok=True)
    (folder / 'input').mkdir(exist_ok=True)
    info = {
        'user': username,
        'track': track,
    }
    with (folder / 'info.json').open('w') as fp:
        json.dump(info, fp)

    if meta.multipart:
        (folder / 'tmp').mkdir(exist_ok=True)
        with (folder / 'tmp' / 'upload.json').open('w') as fp:
            json.dump(meta.dict(), fp)
    else:
        with (folder / 'archive.hash').open('w') as fp:
            fp.write(meta.hash)

    (folder / 'upload.lock').touch()


def multipart_add(submission_id: str, filename: str, data: SpooledTemporaryFile):
    folder = (_settings.USER_DATA_DIR / 'submissions' / submission_id)
    with (folder / 'tmp' / 'upload.json').open() as fp:
        mf_data = misc.SplitManifest(**json.load(fp))

    # add the part
    with (folder / "tmp" / f"{filename}").open('wb') as fp:
        for d in data:
            fp.write(d)

    # check hash
    f_hash = next((v for v in mf_data.index if v[0] == filename), None)
    if f_hash is None:
        raise ResourceRequestedNotFound(f"Part {filename} is not part of submission {submission_id}!!")

    if not misc.md5sum((folder / "tmp" / f"{filename}")) == f_hash:
        raise ValueNotValid("Hash of part does not match given hash")

    # up count of received parts
    mf_data.completed += 1

    # write new data
    with (folder / 'tmp' / 'upload.json').open() as fp:
        json.dump(mf_data.dict(), fp)

    # return status
    return mf_data.completed >= len(mf_data.index), mf_data


def add_part(submission_id: str, filename: str, data: SpooledTemporaryFile):
    folder = (_settings.USER_DATA_DIR / 'submissions' / submission_id)
    if not folder.is_dir():
        raise ResourceRequestedNotFound(f"submission ({submission_id}) does not exist!!")

    if not (folder / 'upload.lock').is_file():
        raise InvalidRequest(f"submission ({submission_id}) does not accept any more parts")

    if (folder / 'tmp').is_file() and (folder / 'tmp/upload.json'):
        return multipart_add(submission_id, filename, data)
    else:
        pass






def transfer_submission(submission_id: str, submission_location: Path):
    """ Transfer a submission to worker storage """
    if _settings.SHARED_WORKER_STORAGE:
        shutil.copytree(submission_location, (_settings.JOB_STORAGE / submission_id))
    else:
        misc.scp(submission_location, Path(f"{_settings.REMOTE_WORKER_HOST}:{_settings.JOB_STORAGE}"))
