from pathlib import Path
import random
import string


def dummy_function(where: str, lines: int, length: int):
    loc = Path(where)

    if loc.is_dir():
        with (loc / 'output.txt').open('w') as fp:
            for i in range(lines):
                chars = "".join([random.choice(string.ascii_letters) for _ in range(length)])
                fp.write(f"{chars}\n")
    else:
        raise ValueError("bad location was provided")
