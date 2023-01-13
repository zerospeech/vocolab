import json

from vocolab import get_settings, exc
from vocolab.db import models

_settings = get_settings()


def get_user_data(username: str) -> models.api.UserData:
    db_file = (_settings.user_data_dir / f"{username}.json")
    if not db_file.is_file():
        raise exc.UserNotFound('user requested has no data entry')
    with db_file.open() as fp:
        raw_data = json.load(fp)
    return models.api.UserData(**raw_data)


def update_user_data(username: str, data: models.api.UserData):
    if not _settings.user_data_dir.is_dir():
        _settings.user_data_dir.mkdir(parents=True)

    with (_settings.user_data_dir / f"{username}.json").open('w') as fp:
        json.dump(data.dict(), fp)
