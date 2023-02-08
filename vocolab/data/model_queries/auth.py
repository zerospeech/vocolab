import json
import secrets
from datetime import datetime
from typing import Optional, List, Iterable

from email_validator import validate_email, EmailNotValidError
from jose import jwt, JWTError  # noqa: false flags from requirements https://youtrack.jetbrains.com/issue/PY-27985
from pydantic import BaseModel, EmailStr, Field, ValidationError

from vocolab.data import models, tables, exc as db_exc
from ..db import zrDB
from ...core import users_lib
from ...settings import get_settings

_settings = get_settings()


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
    def enabled(self) -> bool:
        """ Check if a user is enabled (active & verified)"""
        return self.active and self.is_verified()

    class Config:
        orm_mode = True

    def is_verified(self) -> bool:
        """ Check whether a user has been verified"""
        return self.verified == 'True'

    def password_matches(self, password: str) -> bool:
        """ Check if given password matches users """
        hashed_pwd, _ = users_lib.hash_pwd(password=password, salt=self.salt)
        return hashed_pwd == self.hashed_pswd

    async def change_password(self, new_password: str, password_validation: str):
        """ Modify a users password """
        if new_password != password_validation:
            raise ValueError('passwords do not match')

        hashed_pswd, salt = users_lib.hash_pwd(password=new_password)
        query = tables.users_table.update().where(
            tables.users_table.c.id == self.id
        ).values(hashed_pswd=hashed_pswd, salt=salt)
        await zrDB.execute(query)

    async def delete(self):
        query = tables.users_table.delete().where(
            tables.users_table.c.id == self.id
        )
        await zrDB.execute(query)

    async def verify(self, verification_code: str, force: bool = False) -> bool:
        """ Verify a user using a verification code, (can be forced) """
        if self.is_verified():
            return True

        query = tables.users_table.update().where(
            tables.users_table.c.id == self.id
        ).values(verified='True')

        if secrets.compare_digest(self.verified, verification_code) or force:
            await zrDB.execute(query)
            return True

        return False

    async def toggle_status(self, active: bool = True):
        """ Toggles a users status from active to inactive """
        query = tables.users_table.update().where(
            tables.users_table.c.id == self.id
        ).values(
            active=active
        )
        await zrDB.execute(query)

    def get_profile_data(self) -> users_lib.UserProfileData:
        """ Load users profile data """
        return users_lib.UserProfileData.load(self.username)

    @classmethod
    async def get(cls, *, by_uid: Optional[int] = None, by_username: Optional[str] = None,
                  by_email: Optional[str] = None) -> "User":
        """ Get a user from the database """
        if by_uid:
            query = tables.users_table.select().where(
                tables.users_table.c.id == by_uid
            )
        elif by_username:
            query = tables.users_table.select().where(
                tables.users_table.c.username == by_username
            )
        elif by_email:
            query = tables.users_table.select().where(
                tables.users_table.c.email == by_email
            )
        else:
            raise ValueError('a value must be provided : uid, username, email')

        user_data = await zrDB.fetch_one(query)
        if user_data is None:
            raise ValueError(f'database does not contain a user for given description')

        return cls(**user_data)

    @classmethod
    async def login(cls, login_id: str, password: str) -> Optional["User"]:
        try:
            validate_email(login_id)  # check if email is valid
            query = tables.users_table.select().where(
                tables.users_table.c.email == login_id
            )
        except EmailNotValidError:
            query = tables.users_table.select().where(
                tables.users_table.c.username == login_id
            )

        user_data = await zrDB.fetch_one(query)
        if user_data is None:
            return None

        current_user = cls(**user_data)
        # check password
        hashed_pswd, _ = users_lib.hash_pwd(password=password, salt=current_user.salt)
        if current_user.enabled and hashed_pswd == current_user.hashed_pswd:
            return current_user
        return None

    @classmethod
    async def create(cls, *, new_usr: models.api.UserCreateRequest):
        """ Create a new user entry in the users database """
        hashed_pswd, salt = users_lib.hash_pwd(password=new_usr.pwd)
        verification_code = secrets.token_urlsafe(8)
        try:
            # insert user entry into the database
            query = tables.users_table.insert().values(
                username=new_usr.username,
                email=new_usr.email,
                active=True,
                verified=verification_code,
                hashed_pswd=hashed_pswd,
                salt=salt,
                created_at=datetime.now()
            )
            await zrDB.execute(query)
        except Exception as e:
            db_exc.parse_user_insertion(e)

        # create user profile data
        profile_data = users_lib.UserProfileData(
            username=new_usr.username,
            email=new_usr.email,
            affiliation=new_usr.affiliation,
            first_name=new_usr.first_name,
            last_name=new_usr.last_name,
            verified=False
        )
        profile_data.save()
        return verification_code


class UserList(BaseModel):
    items: List[User]


    def __iter__(self) -> Iterable[User]:
        return iter(self.items)

    @classmethod
    async def get(cls, active_only: bool = False) -> "UserList":
        """ Get all existing users, flag allows to filter non-active users """
        query = tables.users_table.select()
        if active_only:
            query = tables.users_table.select().where(
                tables.users_table.c.active == True
            )
        user_list = await zrDB.fetch_all(query)
        if user_list is None:
            raise ValueError(f'database does not contain any user')
        return cls(items=user_list)

    @classmethod
    async def toggle_status(cls, active: bool = True):
        """ Toggles all users status from active to inactive """
        query = tables.users_table.update().values(
            active=active
        )
        return await zrDB.execute(query)

    @classmethod
    async def verify(cls):
        query = tables.users_table.update().values(
            verify="True"
        )
        await zrDB.execute(query)


class Token(BaseModel):
    """ API Session Token """
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + _settings.user_options.session_expiry_delay)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    allow_password_reset: bool = False  # used for password reset sessions
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
            payload = jwt.decode(token=encoded_token, key=_settings.secret,
                                 algorithms=[_settings.api_options.token_encryption])
            return Token(**payload)
        except (JWTError, ValidationError) as e:
            raise ValueError("Invalid token") from e
