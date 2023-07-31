import hashlib
import json
import os
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Extra, EmailStr

from vocolab import get_settings, exc

_settings = get_settings()


class UserProfileData(BaseModel):
    username: str
    affiliation: str
    first_name: Optional[str]
    last_name: Optional[str]
    verified: bool
    email: EmailStr
    created: Optional[datetime]

    class Config:
        extra = Extra.allow

    @classmethod
    def load(cls, username: str):
        db_file = (_settings.user_data_dir / f"{username}.json")
        if not db_file.is_file():
            raise exc.UserNotFound('user requested has no data entry')

        with db_file.open() as fp:
            return cls.parse_obj(json.load(fp))

    def save(self):
        if not _settings.user_data_dir.is_dir():
            _settings.user_data_dir.mkdir(parents=True)

        with (_settings.user_data_dir / f"{self.username}.json").open('w') as fp:
            fp.write(self.json(indent=4))

    def delete(self):
        """ Delete profile data from disk"""
        file = (_settings.user_data_dir / f"{self.username}.json")
        file.unlink(missing_ok=True)


def hash_pwd(*, password: str, salt=None):
    """ Creates a hash of the given password.
        If salt is None generates a random salt.

    :arg password<str> the password to hash
    :arg salt<bytes> a value to salt the hashing
    :returns hashed_password, salt
    """

    if salt is None:
        salt = os.urandom(32)  # make random salt

    hash_pass = hashlib.pbkdf2_hmac(
        'sha256',  # The hash digest algorithm for HMAC
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    return hash_pass, salt
