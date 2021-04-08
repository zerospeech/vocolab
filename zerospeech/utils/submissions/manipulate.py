import json
from pathlib import Path
import shutil

from zerospeech.settings import get_settings
from zerospeech.utils import misc

_settings = get_settings()


def make_submission_on_disk(submission_id: str, username: str, track: str, nb_parts: int):
    folder = (_settings.USER_DATA_DIR / 'submissions' / submission_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'logs').mkdir(exist_ok=True)
    (folder / 'scores').mkdir(exist_ok=True)
    (folder / 'input').mkdir(exist_ok=True)
    (folder / 'raw').mkdir(exist_ok=True)
    info = {
        'user': username,
        'track': track,
        'nb_parts': nb_parts
    }
    with (folder / 'info.json').open('w') as fp:
        json.dump(info, fp)
    (folder / 'upload.lock').touch()


"""
TODO: create a transfer job data function (that checks if job storage is remote)
TODO: create a fake submission creation
TODO: create an unzip & merge zips function
"""


def transfer_submission(submission_id: str, submission_location: Path):
    """ Transfer a submission to worker storage """
    if _settings.SHARED_WORKER_STORAGE:
        shutil.copytree(submission_location, (_settings.JOB_STORAGE / submission_id))
    else:
        misc.scp(submission_location, Path(f"{_settings.REMOTE_WORKER_HOST}:{_settings.JOB_STORAGE}"))
