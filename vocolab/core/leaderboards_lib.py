import json
from datetime import datetime
from typing import Dict

from vocolab import out, get_settings
from vocolab.data import models, model_queries
from vocolab.core import commons, misc

_settings = get_settings()


def get_static_location(label: str):
    # todo: check why this is in static files ?
    return _settings.static_files_directory / 'leaderboards' / label


def rebuild_leaderboard_index(leaderboard_entries, *, key):
    """ sort entries by using a specific key and re-write the index with the new ordering """

    leaderboard_entries = sorted(leaderboard_entries, key=lambda x: misc.key_to_value(x, key=key))

    for i, entry in enumerate(leaderboard_entries, 1):
        entry['index'] = i

    return leaderboard_entries


async def build_leaderboard(*, leaderboard_id: int):
    pass
    # todo recheck
    # leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    # leaderboard_entries = []
    # static_location = get_static_location(leaderboard.label)
    #
    # # create static dir
    # if leaderboard.static_files:
    #     static_location.mkdir(exist_ok=True, parents=True)
    #
    # # load external entries
    # external_entries = [
    #     *leaderboard.external_entries.rglob('*.json'),
    #     *leaderboard.external_entries.rglob('*.yaml'),
    #     *leaderboard.external_entries.rglob('*.yml')
    # ]
    # for item in external_entries:
    #     leaderboard_entries.append(commons.load_dict_file(item))
    #
    # # copy external static files
    # if leaderboard.static_files and (leaderboard.external_entries / 'static').is_dir():
    #     commons.copy_all_contents(leaderboard.external_entries / 'static', static_location)
    #
    # if not leaderboard.archived:
    #     submission_list = await challengesQ.list_submission(by_track=leaderboard.challenge_id)
    #     for sub in submission_list:
    #         # skip not completed submissions
    #         if sub.status != schema.SubmissionStatus.completed:
    #             continue
    #
    #         # append submission to leaderboard
    #         sub_location = _fs.submissions.get_submission_dir(sub.id)
    #         leaderboard_entry = _fs.leaderboards.load_entry_from_sub(sub.id, leaderboard.entry_file)
    #
    #         # if author_label is set use database value over local
    #         if sub.author_label and len(leaderboard_entry) > 0:
    #             leaderboard_entry['author_label'] = sub.author_label
    #
    #         # append to leaderboard
    #         leaderboard_entries.append(leaderboard_entry)
    #
    #         # grab all static files
    #         # todo: check is static file section is obsolete ?
    #         if leaderboard.static_files and (sub_location / 'static').is_dir():
    #             _fs.commons.copy_all_contents(sub_location / 'static', static_location)
    #
    # if leaderboard.sorting_key:
    #     try:
    #         leaderboard_entries = rebuild_leaderboard_index(leaderboard_entries, key=leaderboard.sorting_key)
    #     except KeyError:
    #         out.log.error(f"Failed to build index for leaderboard={leaderboard.label} "
    #                       f"with sorting_key: {leaderboard.sorting_key}")
    # # Export to file
    # with (_settings.leaderboard_dir / leaderboard.path_to).open('w') as fp:
    #     json.dump(dict(
    #         updatedOn=datetime.now().isoformat(),
    #         data=leaderboard_entries
    #     ), fp)
    #
    # return _settings.leaderboard_dir / leaderboard.path_to


async def get_leaderboard(*, leaderboard_id) -> Dict:
    """ Load leaderboard object file """
    pass
    # todo recheck
    # leaderboard = await leaderboardQ.get_leaderboard(leaderboard_id=leaderboard_id)
    # return _fs.commons.load_dict_file(_settings.leaderboard_dir / leaderboard.path_to)


async def create(*, challenge_id, label, entry_file, external_entries, static_files, path_to, archived):
    """ Create a new leaderboard """
    # todo recheck
    # if external_entries is not None:
    #     external_entries = (_fs.leaderboards.get_leaderboard_archive_location() / external_entries)
    #
    # ld = schema.LeaderBoard(
    #     challenge_id=challenge_id,
    #     label=label,
    #     entry_file=entry_file,
    #     archived=archived,
    #     external_entries=external_entries,
    #     path_to=(_fs.leaderboards.get_leaderboard_location() / path_to),
    #     static_files=static_files
    # )
    # lead_id = await leaderboardQ.create_leaderboard(lead_data=ld)
    # # issue: do we want auto-build on creation ?
    # await build_leaderboard(leaderboard_id=lead_id)
    # return lead_id


async def build_all_challenge(challenge_id: int):
    pass
    # todo recheck
    # leaderboard_list = await leaderboardQ.get_leaderboards(by_challenge_id=challenge_id)
    #
    # for ld in leaderboard_list:
    #     await build_leaderboard(leaderboard_id=ld.id)
