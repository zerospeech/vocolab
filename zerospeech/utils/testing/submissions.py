import uuid
from pathlib import Path

import numpy as np
import yaml

from zerospeech.settings import get_settings

_settings = get_settings()


def create_fake_submission(username: str, challenge_label: str) -> Path:
    """ Creates some fake files for testing submissions """
    submission_id = str(uuid.uuid4())
    location = (_settings.USER_DATA_DIR / username / 'submissions' / challenge_label / submission_id)
    location.mkdir(parents=True, exist_ok=True)
    for i in range(100):
        with (location / f'fx_{i}.txt').open('w') as fp:
            np.savetxt(fp, np.random.rand(8, 8))
    with (location / 'meta.yml').open('w') as fp:
        v = dict(
            author='Test Guy et al.',
            description='This is data for tests',
        )
        yaml.dump(v, fp)

    return location





