import os
import shutil
import tempfile
from pathlib import Path

import pytest

from zerospeech import get_settings


@pytest.fixture(scope="session")
def large_binary_file():
    tmp = Path(tempfile.mkdtemp())
    with (tmp / 'test.bin').open('wb') as fd:
        for i in range(5000):
            fd.write(os.urandom(50000))
    yield (tmp / 'test.bin'), tmp
    # clean-up
    shutil.rmtree(tmp)


@pytest.fixture(scope="session")
def api_settings():
    return get_settings(settings_type="queue_worker")


@pytest.fixture(scope="session")
def queue_settings():
    return get_settings(settings_type="api")


@pytest.fixture(scope="session")
def cli_settings():
    return get_settings(settings_type="cli")



