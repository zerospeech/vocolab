""" Dataclasses representing API/auth input output data types """
from pydantic import BaseModel, EmailStr, validator


class UserCreateRequest(BaseModel):
    """ Dataclass for user creation """
    username: str
    email: EmailStr
    pwd: str
    first_name: str
    last_name: str
    affiliation: str

    @validator('username', 'pwd', 'first_name', 'last_name', 'affiliation')
    def non_empty_string(cls, v):
        assert v, "UserCreate does not accept empty fields"
        return v


class LoggedItem(BaseModel):
    """ Return type of the /login function """
    username: str
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
