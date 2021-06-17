import asyncio
from contextlib import contextmanager
from datetime import datetime, date, time
from dateutil import parser

__FALSE_VALUES__ = ['false', '0', 'f', 'n', 'no', 'nope', 'none', 'nan', 'not']


def str2type(value: str, m_type):
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
