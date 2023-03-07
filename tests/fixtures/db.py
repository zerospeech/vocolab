import pytest

from vocolab.data.db import zrDB, build_database_from_schema


@pytest.fixture(scope="session")
async def db():
    build_database_from_schema()
    # connect to Database
    await zrDB.connect()



