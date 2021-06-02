import json
from datetime import datetime

from zerospeech import get_settings, out
from zerospeech.db import schema
from zerospeech.db.q import leaderboardQ, challengesQ
from zerospeech.db.schema import LeaderBoard
from zerospeech.utils import misc
from zerospeech.utils import submissions

_settings = get_settings()


def get_leaderboard_location():
    return _settings.LEADERBOARD_LOCATION


def get_external_location():
    return _settings.LEADERBOARD_LOCATION / 'external_entries'


async def create(*, challenge_id, label, entry_file, external_entries, static_files, path_to):
    ld = LeaderBoard(
        challenge_id=challenge_id,
        label=label,
        entry_file=entry_file,
        archived=False,
        external_entries=external_entries,
        path_to=(get_leaderboard_location() / path_to),
        static_files=static_files
    )
    await leaderboardQ.create_leaderboard(lead_data=ld)


def load_entry_from_sub(submission_id: str, leaderboard_entry: str):
    """ Load a leaderboard entry from a submission dir """
    location = submissions.log.get_submission_dir(submission_id)
    if (location / leaderboard_entry).is_file():
        return misc.load_dict_file(location / leaderboard_entry)
    return None


async def build_leaderboard(*, leaderboard_id: int):
    leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    leaderboard_entries = []

    # load external entries
    external_entries = [
        *leaderboard.external_entries.rglob('*.json'),
        *leaderboard.external_entries.rglob('*.yaml'),
        *leaderboard.external_entries.rglob('*.yml')
    ]
    for item in external_entries:
        out.Console.debug(item)
        leaderboard_entries.append(misc.load_dict_file(item))

    if not leaderboard.archived:
        submission_list = await challengesQ.list_submission(by_track=leaderboard.challenge_id)
        for sub in submission_list:
            if sub.status != schema.SubmissionStatus.completed:
                # skip not completed submissions
                continue
            leaderboard_entries.append(load_entry_from_sub(sub.id, leaderboard.entry_file))

    # Export to file
    with (_settings.LEADERBOARD_LOCATION / leaderboard.path_to).open('w') as fp:
        json.dump(dict(
            updatedOn=datetime.now().isoformat(),
            data=leaderboard_entries
        ), fp)

    return _settings.LEADERBOARD_LOCATION / leaderboard.path_to


async def get_leaderboard(*, leaderboard_id):
    """ Load leaderboard object file """
    leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    with (_settings.LEADERBOARD_LOCATION / leaderboard.path_to).open() as fp:
        return json.load(fp)
