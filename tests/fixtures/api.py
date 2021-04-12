import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from zerospeech.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app) as ac:
        yield ac
