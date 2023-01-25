#!/usr/bin/env python
import hashlib
import json
import os
import sys
from pathlib import Path

submission_dir = Path(sys.argv[1])
print(f"Evaluating submission {submission_dir}")
scores = {}

score_dir = submission_dir / 'scores'
score_dir.mkdir(exist_ok=True, parents=True)

for i in range(15):
    data = os.urandom(1024)
    sc_raw = hashlib.md5(data).hexdigest()
    sc = [int(c, 16) for c in sc_raw]
    scores[str(i+1).zfill(3)] = sum(sc) / len(sc)

    with (score_dir / f"{str(i+1).zfill(3)}.score").open('wb') as fout:
        fout.write(data)

with (submission_dir / "scores.json").open('w') as fp:
    json.dump(scores, fp, indent=4)
