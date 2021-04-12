import shutil
from pathlib import Path

import pytest

pytest_plugins = [
   "tests.fixtures.api",
   "tests.fixtures.db",
   "tests.fixtures.utils",
]

TEST_MANIFEST = []


@pytest.fixture(autouse=True)
def run_around_tests():
    # Test set-up
    yield
    # Post Test clean-up
    for item in TEST_MANIFEST:
        if isinstance(item, Path):
            shutil.rmtree(item)


