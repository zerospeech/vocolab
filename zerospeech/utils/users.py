import json

from zerospeech import get_settings, exc
from zerospeech.db import schema

_settings = get_settings()


def get_user_data(username: str) -> schema.UserData:
    db_file = (_settings.USER_DATA_DIR / f"{username}.json")
    if not db_file.is_file():
        raise exc.UserNotFound('user requested has no data entry')
    with db_file.open() as fp:
        raw_data = json.load(fp)
        return schema.UserData(**raw_data)


def update_user_data(username: str, data: schema.UserData):
    if not _settings.USER_DATA_DIR.is_dir():
        _settings.USER_DATA_DIR.mkdir(parents=True)

    with (_settings.USER_DATA_DIR / f"{username}.json").open('w') as fp:
        json.dump(data.dict(), fp)
