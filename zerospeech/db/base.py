import databases
import sqlalchemy

from zerospeech.db.schema import users_metadata
from zerospeech.db.schema import challenge_metadata
from zerospeech.settings import get_settings

_settings = get_settings()

_USERS_CONN = f"sqlite:///{_settings.DB_HOME}/{_settings.db_file}"

zrDB = databases.Database(_USERS_CONN)


def create_db():
    if not (_settings.DB_HOME / _settings.db_file).is_file():
        (_settings.DB_HOME / _settings.db_file).touch()

    engine = sqlalchemy.create_engine(
       _USERS_CONN, connect_args={"check_same_thread": False}
    )
    users_metadata.create_all(engine)
    challenge_metadata.create_all(engine)
