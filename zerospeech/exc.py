""" A File containing Exceptions definitions """
from typing import Any, Optional


class ZerospeechException(Exception):
    """ Generic Base Exception definition for the Zerospeech API """

    def __init__(self, msg: Optional[str] = None, data: Optional[Any] = None):

        if msg is None:
            msg = self.__doc__

        self.message = msg
        self.data = data
        super(ZerospeechException, self).__init__(msg)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class UserError(ZerospeechException):
    """ Generic Exception for actions on users """
    pass


class UserNotFoundError(UserError):
    """ Exception to be raised when user cannot be found"""
    pass


class ActionNotValidError(ZerospeechException):
    """ Error you are performing a useless or invalid action"""
    pass


class ValueNotValidError(ZerospeechException):
    """ Error one of the values used was not valid """
    pass
