import sqlite3
from vocolab import exc


class IntegrityError(sqlite3.IntegrityError):
    pass


def parse_user_insertion(e: Exception):
    """ Wrapper to uniform exception while inserting new users """

    if issubclass(IntegrityError, e.__class__):
        error_message = e.__str__()
        if "UNIQUE" in error_message and "email" in error_message:
            raise exc.ValueNotValid('email already exists', data='email')
        elif "UNIQUE" in error_message and "username" in error_message:
            raise exc.ValueNotValid('username already exists', data='username')
    raise e


def parse_challenge_insertion(e: Exception):
    """ Wrapper to uniform exception while inserting new challenges """
    if issubclass(IntegrityError, e.__class__):
        error_message = e.__str__()
        if "UNIQUE" in error_message and "label" in error_message:
            raise exc.ValueNotValid('a challenge with the same label exists', data='label')

    raise e
