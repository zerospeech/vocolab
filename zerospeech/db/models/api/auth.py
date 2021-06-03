""" Dataclasses representing API/auth input output data types """
from pydantic import BaseModel, EmailStr


class LoggedItem(BaseModel):
    """ Return type of the /login function """
    access_token: str
    token_type: str


class CurrentUser(BaseModel):
    """ Basic userinfo Model """
    username: str
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """ Input Schema for /password/reset request """
    username: str
    email: EmailStr


