import json

from zerospeech.settings import get_settings

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
