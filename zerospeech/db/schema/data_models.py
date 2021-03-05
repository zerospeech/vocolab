from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


# todo maybe move this ?
class UserData(BaseModel):
    username: str
    affiliation: str
    first_name: Optional[str]
    last_name: Optional[str]
