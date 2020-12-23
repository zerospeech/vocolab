import hashlib
import os
import secrets
from datetime import datetime
from typing import Optional

from email_validator import validate_email, EmailSyntaxError
from pydantic import BaseModel, EmailStr

from zerospeech.db import users_db, schema
from zerospeech.settings import get_settings

_settings = get_settings()


class UserCreate(BaseModel):
    """ Dataclass for user creation """
    username: str
    email: EmailStr
    pwd: str
    first_name: str
    last_name: str
    affiliation: str


def hash_pwd(password: str, salt=None):
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


async def create_user(usr: UserCreate):
    """ Create a new user entry in the users database. """
    # todo raise & handle error if duplicate username/email
    hashed_pswd, salt = hash_pwd(usr.pwd)
    verification_code = secrets.token_urlsafe(8)
    query = schema.users_table.insert().values(
        username=usr.username,
        email=usr.email,
        active=True,
        verified=verification_code,
        hashed_pswd=hashed_pswd,
        salt=salt
    )
    await users_db.execute(query)
    return verification_code


async def verify_user(username: str, verification_code: str):
    user = await get_user(by_username=username)
    if secrets.compare_digest(user.verified, verification_code):
        query = schema.users_table.update().where(
            schema.users_table.c.id == user.id
        ).values(
            verified='True'
        )
        await users_db.execute(query)
        return True
    return False


def check_users_password(password: str, user: schema.User):
    """ Verify that a given password matches the users """
    hashed_pwd, _ = hash_pwd(password, salt=user.salt)
    return hashed_pwd == user.hashed_pswd


async def validate_token(token: str):
    """ Verify that a session token exists & is valid.
    :returns the logged_user entry
    :raises ValueError if entry not valid
    """
    query = schema.logged_users_table.select().where(
        schema.logged_users_table.c.token == token
    )

    logged_usr = await users_db.fetch_one(query)
    if logged_usr is None:
        raise ValueError('Token appears to not be valid')

    logged_usr = schema.LoggedUser(**logged_usr)

    # verify dates
    if datetime.now() > logged_usr.expiration_date:
        raise ValueError('Token appears to have expired')

    return logged_usr


async def get_user(by_uid: Optional[int] = None, by_username: Optional[str] = None,
                   by_email: Optional[str] = None) -> schema.User:
    """ Get a user from the database using uid, username or email as a search parameter.

    :returns the user object
    :raises ValueError if the user does not exist or no search value was provided
    """

    if by_uid:
        query = schema.users_table.select().where(
            schema.users_table.c.id == by_uid
        )
    elif by_username:
        query = schema.users_table.select().where(
            schema.users_table.c.username == by_username
        )
    elif by_email:
        query = schema.users_table.select().where(
            schema.users_table.c.email == by_email
        )
    else:
        raise ValueError('a value must be provided : uid, username, email')

    user = await users_db.fetch_one(query)
    if user is None:
        raise ValueError(f'database does not contain a user for given credentials')

    return schema.User(**user)


async def login_user(login: str, pwd: str):
    """ Create a new session for a user
    :arg login<str> argument used to identify user (can be username or email)
    :arg pwd<str> the password of the user
    :returns the user object
    :raises ValueError if the login or password are not matched to a user.
    """

    # check username/email
    try:
        email = validate_email(email=login)
        query = schema.users_table.select().where(
            schema.users_table.c.email == email.email
        )
    except EmailSyntaxError:
        query = schema.users_table.select().where(
            schema.users_table.c.username == login
        )

    usr = await users_db.fetch_one(query)
    if usr is None:
        raise ValueError('Login or password incorrect')

    usr = schema.User(**usr)

    # check password
    if not check_users_password(pwd, usr):
        raise ValueError('Login or password incorrect')

    # Log user in
    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.local.session_expiry_delay
    query = schema.logged_users_table.insert().values(
        token=user_token,
        user_id=usr.id,
        expiration_date=token_best_by
    )
    await users_db.execute(query)

    return usr, user_token


async def delete_session(token: str):
    """ Delete a specific user session """
    query = schema.logged_users_table.delete().where(
        schema.logged_users_table.c.token == token
    )
    # returns number of deleted entries
    return await users_db.execute(query)


async def clear_expired_sessions():
    """ Deletes all expired sessions from the logged_users table """
    query = schema.logged_users_table.delete().where(
        schema.logged_users_table.c.expiration_date <= datetime.now()
    )
    # returns number of deleted entries
    return await users_db.execute(query)


async def create_password_reset_session(user: Optional[schema.User] = None,
                                        email: Optional[str] = None) -> schema.PasswordResetSession:
    if user:
        safe = True

    elif email:
        user = get_user(by_email=email)
        safe = False

    else:
        raise ValueError('No identifier provided')

    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.local.password_reset_expiry_delay
    query = schema.password_reset_table.insert().values(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by,
        safe_reset=safe
    )
    await users_db.execute(query)

    return schema.PasswordResetSession(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by,
        safe_reset=safe
    )


def get_user_profile(username: str):
    # TODO see how to implement this
    pass
