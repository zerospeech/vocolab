import asyncio
from contextlib import contextmanager
from datetime import datetime


def str2type(value: str, m_type):
    # todo : finish this
    if m_type == 'int':
        return int(value)
    elif m_type == 'float':
        return float(value)
    elif m_type == 'date':
        return datetime()


@contextmanager
def get_event_loop():
    """ Create & close event loops """
    loop = asyncio.get_event_loop()
    try:
        yield loop
    finally:
        loop.close()
