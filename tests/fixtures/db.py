import pytest

from zerospeech.db import zrDB, create_db


@pytest.fixture(scope="session")
async def db():
    create_db()
    # connect to Database
    await zrDB.connect()



