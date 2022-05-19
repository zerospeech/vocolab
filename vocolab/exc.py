""" A File containing Exceptions definitions """
from typing import Any, Optional

from starlette import status as http_status


class VocoLabException(Exception):
    """ Generic Base Exception definition for the Zerospeech API """
    __http_status__: int = http_status.HTTP_400_BAD_REQUEST

    def __init__(self, msg: Optional[str] = None, data: Optional[Any] = None, status: Optional[int] = None):

        if msg is None:
            msg = self.__doc__

        if status is not None:
            self.__http_status__ = status

        self.message = msg
        self.data = data
        super(VocoLabException, self).__init__(msg)

    @property
    def status(self):
        """ Returns the https status code of the exception """
        return self.__http_status__

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class OptionMissing(VocoLabException):
    """ Generic Exception used when a function was called with incorrect or missing arguments """
    pass


class UserError(VocoLabException):
    """ Generic Exception for actions on users """
    pass


class AccessError(UserError):
    """ Exception for when accessing forbidden resources """
    pass


class UserNotFound(UserError):
    """ Exception to be raised when user cannot be found"""
    pass


class ActionNotValid(VocoLabException):
    """ Error you are performing a useless or invalid action"""
    pass


class ValueNotValid(VocoLabException):
    """ Error one of the values used was not valid """
    pass


class InvalidRequest(VocoLabException):
    """ Error the request made was not valid """
    pass


class ResourceRequestedNotFound(VocoLabException):
    """ Error the request made was not valid """
    pass


class SecurityError(VocoLabException):
    """ Error for not allowed actions """
    pass


class ServerError(VocoLabException):
    """ Error with the starting of a server/service """
    pass
