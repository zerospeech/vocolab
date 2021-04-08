import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from zerospeech import get_settings
from zerospeech.api import app
from zerospeech.db import zrDB, create_db

TEST_MANIFEST = []


@pytest.fixture(autouse=True)
def run_around_tests():
    # Test set-up
    yield
    # Post Test clean-up
    for item in TEST_MANIFEST:
        if isinstance(item, Path):
            shutil.rmtree(item)


@pytest.fixture(scope="session")
async def db():
    create_db()
    # connect to Database
    await zrDB.connect()


@pytest.fixture(scope="session")
def api_settings():
    return get_settings(settings_type="queue_worker")


@pytest.fixture(scope="session")
def queue_settings():
    return get_settings(settings_type="api")


@pytest.fixture(scope="session")
def cli_settings():
    return get_settings(settings_type="cli")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app) as ac:
        yield ac


@pytest.fixture(scope="session")
def large_binary_file():
    tmp = Path(tempfile.mkdtemp())
    with (tmp / 'test.bin').open('wb') as fd:
        for i in range(5000):
            fd.write(os.urandom(50000))
    yield (tmp / 'test.bin'), tmp
    # clean-up
    shutil.rmtree(tmp)
