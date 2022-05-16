from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
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

