""" Input/Output Dataclass types for the /users section of the API """
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Extra, EmailStr


class UserData(BaseModel):
    username: str
    affiliation: str
    first_name: Optional[str]
    last_name: Optional[str]

    class Config:
        extra = Extra.allow


class UserProfileResponse(UserData):
    verified: bool
    email: EmailStr
    created: Optional[datetime]
