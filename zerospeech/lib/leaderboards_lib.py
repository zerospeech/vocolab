import json
from datetime import datetime
from typing import Dict

from zerospeech import out, get_settings
from zerospeech.db import schema
from zerospeech.db.q import leaderboardQ, challengesQ
from zerospeech.lib import _fs

_settings = get_settings()


def get_static_location(label: str):
    return _settings.LEADERBOARD_LOCATION / 'static' / label


async def create(*, challenge_id, label, entry_file, external_entries, static_files, path_to):
    """ Create a new leaderboard """
    ld = schema.LeaderBoard(
        challenge_id=challenge_id,
        label=label,
        entry_file=entry_file,
        archived=False,
        external_entries=external_entries,
        path_to=(_fs.leaderboards.get_leaderboard_location() / path_to),
        static_files=static_files
    )
    await leaderboardQ.create_leaderboard(lead_data=ld)
    # todo create on disk


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
        leaderboard_entries.append(_fs.commons.load_dict_file(item))

    if not leaderboard.archived:
        static_location = get_static_location(leaderboard.label)
        if leaderboard.static_files:
            (static_location / 'static').mkdir(exist_ok=True, parents=True)

        submission_list = await challengesQ.list_submission(by_track=leaderboard.challenge_id)
        for sub in submission_list:
            # skip not completed submissions
            if sub.status != schema.SubmissionStatus.completed:
                continue
            # append submission to leaderboard
            sub_location = _fs.submissions.get_submission_dir(sub.id)
            leaderboard_entries.append(_fs.leaderboards.load_entry_from_sub(sub.id, leaderboard.entry_file))
            # grab all static files
            if leaderboard.static_files and (sub_location / 'static').is_dir():
                _fs.commons.copy_all_contents(sub_location / 'static', static_location,
                                              prefix=f"{sub.user_id}_{sub.track_id}")

    # Export to file
    with (_settings.LEADERBOARD_LOCATION / leaderboard.path_to).open('w') as fp:
        json.dump(dict(
            updatedOn=datetime.now().isoformat(),
            data=leaderboard_entries
        ), fp)

    return _settings.LEADERBOARD_LOCATION / leaderboard.path_to


async def get_leaderboard(*, leaderboard_id) -> Dict:
    """ Load leaderboard object file """
    leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    return _fs.commons.load_dict_file(_settings.LEADERBOARD_LOCATION / leaderboard.path_to)
