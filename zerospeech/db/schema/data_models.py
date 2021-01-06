from typing import Optional

from pydantic import BaseModel


class UserData(BaseModel):
    username: str
    affiliation: str
    first_name: Optional[str]
    last_name: Optional[str]

