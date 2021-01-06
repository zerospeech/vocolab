from datetime import datetime

import sqlalchemy
from pydantic import BaseModel, EmailStr

users_metadata = sqlalchemy.MetaData()


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    active: bool
    verified: str
    hashed_pswd: bytes
    salt: bytes

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
    sqlalchemy.Column("salt", sqlalchemy.BLOB)
)


class LoggedUser(BaseModel):
    token: str
    user_id: int
    expiration_date: datetime

    class Config:
        orm_mode = True


logged_users_table = sqlalchemy.Table(
    "logged_users",
    users_metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("expiration_date", sqlalchemy.DateTime)
)


class PasswordResetSession(BaseModel):
    token: str
    user_id: int
    expiration_date: datetime

    class Config:
        orm_mode = True


password_reset_table = sqlalchemy.Table(
    'password_reset_users',
    users_metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("expiration_date", sqlalchemy.DateTime),
)
