import asyncio
import base64
import json
import shutil
import subprocess
from collections import Callable
from contextlib import contextmanager
from datetime import datetime, date, time
from pathlib import Path
from typing import List, Tuple, Dict

from dateutil import parser

__FALSE_VALUES__ = ['false', '0', 'f', 'n', 'no', 'nope', 'none', 'nan', 'not']


def strip_from_dict(data: Dict, values: List[str]):
    for v in values:
        del data[v]


def key_to_value(obj: Dict, *,  key: str):
    keys = key.split('.')
    curr = obj
    for k in keys:
        curr = curr.get(k, None)
        if curr is None:
            raise KeyError(f"{key} @ {k}: not found in {obj}")

    return curr


def str2type(value: str, m_type):
    """ Convertor of values from string to python types

    Supports:
        - str2bool
        - str2date
        - str2time
        - str2datetime
        - str2Path
        - str2{int, float, **}
        - none, null, nan -> None

        **: Any builtin python type that has a constructor that accepts strings

    :param value: input value as string
    :param m_type: desired python <type '>
    :return: value cast in desired type
    """
    if value.lower() in ['null', 'none', 'nan']:
        return None

    if m_type == bool:
        if value.lower() in __FALSE_VALUES__:
            return False
        return True
    elif m_type == date:
        return parser.parse(value).date()
    elif m_type == time:
        return parser.parse(value).time()
    elif m_type == datetime:
        return parser.parse(value)
    else:
        return m_type(value)


@contextmanager
def get_event_loop():
    """ Create & close event loops """
    loop = asyncio.get_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def run_with_loop(fn: Callable, *args, **kwargs):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # if cleanup: 'RuntimeError: There is no current event loop.'
        loop = None

    if loop and loop.is_running():
        # loop.create_task()
        loop.run_until_complete(fn(*args, **kwargs))
    else:
        asyncio.run(fn(*args, **kwargs))


def execute(cmd: str, args: List[str]) -> Tuple[int, str]:
    """ Execute an external process using subprocess

    :returns returncode, output (output is a merge of stout & stderr)
    """

    if not shutil.which(cmd):
        raise ValueError(f'CMD: {cmd} was not found in path')

    results = subprocess.Popen(
        [cmd, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    output = ""

    while results.poll() is None:
        line = results.stdout.readline()
        if line != "":
            output += line

        line = results.stderr.readline()
        if line != "":
            output += line

    return results.returncode, output


class CustomTypesJsonEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        elif isinstance(o, bytes):
            return str(base64.b64encode(o))
        elif isinstance(o, datetime):
            return str(o.isoformat())
        elif isinstance(o, date):
            return str(o.isoformat())
        elif isinstance(o, time):
            return str(o.isoformat())
        elif isinstance(o, set):
            return list(o)
        elif hasattr(o, "__dict__"):
            return vars(o)
        else:
            return super().default(o)
