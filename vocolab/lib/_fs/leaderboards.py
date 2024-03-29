from vocolab import get_settings

from .commons import load_dict_file
from .submissions import get_submission_dir

_settings = get_settings()


def get_leaderboard_location():
    return _settings.leaderboard_dir


def get_leaderboard_archive_location():
    return _settings.DATA_FOLDER / 'archive'


def load_entry_from_sub(submission_id: str, leaderboard_entry: str):
    """ Load a leaderboard entry from a submission dir """
    location = get_submission_dir(submission_id)
    if (location / leaderboard_entry).is_file():
        return load_dict_file(location / leaderboard_entry)
    return {}
