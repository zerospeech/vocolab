import databases
import sqlalchemy

from vocolab import get_settings
from vocolab.data import exc as db_exc
from .tables import tables_metadata


_settings = get_settings()

# Database Connection
zrDB = databases.Database(_settings.database_connection_url)

def build_database_from_schema():
    if not (_settings.DATA_FOLDER / _settings.database_options.db_file).is_file():
        (_settings.DATA_FOLDER / _settings.database_options.db_file).touch()

    engine = sqlalchemy.create_engine(
       _settings.database_connection_url, connect_args={"check_same_thread": False}
    )
    tables_metadata.create_all(engine)
