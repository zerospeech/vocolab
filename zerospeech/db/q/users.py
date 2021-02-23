import hashlib
import json
import os
import secrets
from datetime import datetime
from typing import Optional, List

from email_validator import validate_email, EmailSyntaxError
from pydantic import BaseModel, EmailStr

from zerospeech.db import users_db, schema, exc as db_exc
from zerospeech.settings import get_settings
from zerospeech import exc

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

    hashed_pswd, salt = hash_pwd(usr.pwd)
    verification_code = secrets.token_urlsafe(8)
    try:
        # insert user entry into the database
        query = schema.users_table.insert().values(
            username=usr.username,
            email=usr.email,
            active=True,
            verified=verification_code,
            hashed_pswd=hashed_pswd,
            salt=salt
        )

        await users_db.execute(query)

    except Exception as e:
        db_exc.parse_user_insertion(e)

    # create user profile data
    data = schema.UserData(
        username=usr.username,
        affiliation=usr.affiliation,
        first_name=usr.first_name,
        last_name=usr.last_name
    )
    update_user_data(usr.username, data)

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
    elif secrets.compare_digest(user.verified, 'True'):
        raise exc.ActionNotValidError("Email already verified")
    else:
        raise exc.ValueNotValidError("validation code was not correct")


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
                   by_email: Optional[str] = None, by_password_reset_session: Optional[str] = None) -> schema.User:
    """ Get a user from the database using uid, username or email as a search parameter.

    :rtype: schema.User
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
    elif by_password_reset_session:
        query = schema.password_reset_table.select().where(
            schema.password_reset_table.c.token == by_password_reset_session
        )

        session = await users_db.fetch_one(query)
        if session is None:
            raise ValueError("session was not found")
        session = schema.PasswordResetSession(**session)
        if session.expiration_date < datetime.now():
            raise ValueError("session expired")

        query = schema.users_table.select().where(
            schema.users_table.c.id == session.user_id
        )

    else:
        raise ValueError('a value must be provided : uid, username, email')

    user = await users_db.fetch_one(query)
    if user is None:
        raise ValueError(f'database does not contain a user for given credentials')

    return schema.User(**user)


async def get_user_list() -> List[schema.User]:
    """ Return a list of all users """
    query = schema.users_table.select()
    user_list = await users_db.fetch_all(query)
    if user_list is None:
        raise ValueError(f'database does not contain any user')
    return [schema.User(**usr) for usr in user_list]


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


async def delete_session(by_token: Optional[str] = None, by_uid: Optional[str] = None):
    """ Delete a specific user session """
    if by_token:
        query = schema.logged_users_table.delete().where(
            schema.logged_users_table.c.token == by_token
        )
    elif by_uid:
        query = schema.logged_users_table.delete().where(
            schema.logged_users_table.c.user_id == by_uid
        )
    else:
        raise exc.OptionMissingError(
            f"Function {delete_session.__name__} requires an uid or token but None was provided!"
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


async def create_password_reset_session(username: str, email: str) -> schema.PasswordResetSession:
    try:
        user = await get_user(by_email=email)
    except ValueError:
        raise exc.UserNotFoundError("the user is not valid")

    if user.username != username:
        raise exc.ValueNotValidError("username provided does not match email")

    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.local.password_reset_expiry_delay
    query = schema.password_reset_table.insert().values(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by,
    )
    await users_db.execute(query)

    return schema.PasswordResetSession(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by
    )


async def update_users_password(user: schema.User, password: str, password_validation: str):

    if password != password_validation:
        raise ValueError('passwords do not match')

    hashed_pswd, salt = hash_pwd(password)
    query = schema.users_table.update().where(
        schema.users_table.c.id == user.id
    ).values(hashed_pswd=hashed_pswd, salt=salt)

    query2 = schema.password_reset_table.delete().where(
        schema.password_reset_table.c.user_id == user.id
    )

    await users_db.execute(query)
    await users_db.execute(query2)


def get_user_data(username: str) -> schema.UserData:
    db_file = (_settings.USER_DATA_DIR / f"{username}.json")
    if not db_file.is_file():
        raise exc.UserNotFoundError('user requested has no data entry')
    with db_file.open() as fp:
        raw_data = json.load(fp)
        return schema.UserData(**raw_data)


def update_user_data(username: str, data: schema.UserData):
    with (_settings.USER_DATA_DIR / f"{username}.json").open('w') as fp:
        json.dump(data.dict(), fp)
