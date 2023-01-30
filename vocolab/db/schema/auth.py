import json
from datetime import datetime
from typing import Optional

import sqlalchemy
from jose import jwt, JWTError  # noqa: false flags from requirements https://youtrack.jetbrains.com/issue/PY-27985
from pydantic import BaseModel, EmailStr, Field, ValidationError

from ...settings import get_settings

_settings = get_settings()
users_metadata = sqlalchemy.MetaData()


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    active: bool
    verified: str
    hashed_pswd: bytes
    salt: bytes
    created_at: Optional[datetime]

    @property
    def enabled(self):
        return self.active and self.verified == 'True'

    class Config:
        orm_mode = True


users_table = sqlalchemy.Table(
    "users_credentials",
    users_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("active", sqlalchemy.Boolean),
    sqlalchemy.Column("verified", sqlalchemy.String),
    sqlalchemy.Column("hashed_pswd", sqlalchemy.BLOB),
    sqlalchemy.Column("salt", sqlalchemy.BLOB),
    sqlalchemy.Column("created_at", sqlalchemy.DATETIME)
)

class Token(BaseModel):
    """ API Session Token """
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + _settings.user_options.session_expiry_delay)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    allow_password_reset: bool = False # used for password reset sessions
    user_email: EmailStr

    def is_expired(self) -> bool:
        """ Check if Token has expired """
        return self.expires_at < datetime.now()

    def encode(self) -> str:
        """ Encode into a token string """
        # passing by json allows to convert datetimes to strings using pydantic serializer
        as_dict = json.loads(self.json())
        return jwt.encode(claims=as_dict, key=_settings.secret, algorithm=_settings.api_options.token_encryption)

    @classmethod
    def decode(cls, encoded_token: str):
        """ Decode token from encoded string """
        try:
            payload = jwt.decode(token=encoded_token, key=_settings.secret, algorithms=[_settings.api_options.token_encryption])
            return Token(**payload)
        except (JWTError, ValidationError) as e:
            raise ValueError("Invalid token") from e
