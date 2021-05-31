from zerospeech import get_settings
from zerospeech.db.q import leaderboard as q_leaderboard
from zerospeech.db.schema import LeaderBoard

_settings = get_settings()


def get_leaderboard_location():
    return _settings.LEADERBOARD_LOCATION


def get_external_location():
    return _settings.LEADERBOARD_LOCATION / 'external_entries'


async def create(*, challenge_id, label, entry_file, external_entries):
    LeaderBoard(
        challenge_id=challenge_id,
        label=label,
        entry_file=entry_file,
        archived=False,
        external_entries=external_entries,
        path_to=(get_leaderboard_location() / f"{label}.json")
    )
