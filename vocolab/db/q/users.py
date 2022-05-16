
import secrets
from datetime import datetime
from typing import Optional, List

from email_validator import validate_email, EmailSyntaxError

from vocolab import exc
from vocolab.db import zrDB, models, schema, exc as db_exc
from vocolab.settings import get_settings
from vocolab.lib import users_lib

_settings = get_settings()


async def create_user(*, usr: models.misc.UserCreate):
    """ Create a new user entry in the users' database."""

    hashed_pswd, salt = users_lib.hash_pwd(password=usr.pwd)
    verification_code = secrets.token_urlsafe(8)
    try:
        # insert user entry into the database
        query = schema.users_table.insert().values(
            username=usr.username,
            email=usr.email,
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
    data = models.api.UserData(
        username=usr.username,
        affiliation=usr.affiliation,
        first_name=usr.first_name,
        last_name=usr.last_name
    )
    users_lib.update_user_data(usr.username, data)

    return verification_code


async def verify_user(*, username: str, verification_code: str):
    """ User verification using a specific code.
        If the code is correct verification succeeds
        If not the function raises a ValueNotValid Exception
        If user is already verified we raise an ActionNotValid Exception
    """
    user = await get_user(by_username=username)
    if secrets.compare_digest(user.verified, verification_code):
        query = schema.users_table.update().where(
            schema.users_table.c.id == user.id
        ).values(
            verified='True'
        )
        await zrDB.execute(query)
        return True
    elif secrets.compare_digest(user.verified, 'True'):
        raise exc.ActionNotValid("Email already verified")
    else:
        raise exc.ValueNotValid("validation code was not correct")


async def admin_verification(*, user_id: int):
    """ Verify a user, raises an ValueError if user does not exist.
        To only be used for administration.
        Users need to validate their accounts.

        - bypasses code verification
        - no exception is raised if user already active
    """
    query = schema.users_table.update().where(
        schema.users_table.c.id == user_id
    ).values(
        verified='True'
    )
    res = await zrDB.execute(query)

    if res == 0:
        raise ValueError(f'user {user_id} was not found')


def check_users_password(*, password: str, user: schema.User):
    """ Verify that a given password matches the users """
    hashed_pwd, _ = users_lib.hash_pwd(password=password, salt=user.salt)
    return hashed_pwd == user.hashed_pswd


async def validate_token(*, token: str):
    """ Verify that a session token exists & is valid.
    :returns the logged_user entry
    :raises ValueError if entry not valid
    """
    query = schema.logged_users_table.select().where(
        schema.logged_users_table.c.token == token
    )

    logged_usr = await zrDB.fetch_one(query)
    if logged_usr is None:
        raise ValueError('Token appears to not be valid')

    logged_usr = schema.LoggedUser(**logged_usr)

    # verify dates
    if datetime.now() > logged_usr.expiration_date:
        raise ValueError('Token appears to have expired')

    return logged_usr


async def get_user(*, by_uid: Optional[int] = None, by_username: Optional[str] = None,
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

        session = await zrDB.fetch_one(query)
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

    user = await zrDB.fetch_one(query)
    if user is None:
        raise ValueError(f'database does not contain a user for given credentials')

    return schema.User(**user)


async def get_user_list() -> List[schema.User]:
    """ Return a list of all users """
    query = schema.users_table.select()
    user_list = await zrDB.fetch_all(query)
    if user_list is None:
        raise ValueError(f'database does not contain any user')
    return [schema.User(**usr) for usr in user_list]


async def delete_user(*, uid: int):
    """ Deletes all  password reset sessions from the password_reset_users table """
    query = schema.users_table.delete().where(
        schema.users_table.c.id == uid
    )
    # returns number of deleted entries
    return await zrDB.execute(query)


async def get_logged_user_list() -> List[schema.User]:
    """ Return a list of all users """
    query = schema.logged_users_table.join(schema.users_table).select().where(
        schema.logged_users_table.c.user_id == schema.users_table.c.id
    )
    logged_list = await zrDB.fetch_all(query)
    return [schema.User(**usr) for usr in logged_list]


async def login_user(*, login: str, pwd: str):
    """ Create a new session for a user
    :param login<str> argument used to identify user (can be username or email)
    :param pwd<str> the password of the user
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

    usr = await zrDB.fetch_one(query)
    if usr is None:
        raise ValueError('Login or password incorrect')

    usr = schema.User(**usr)

    # check password
    if not check_users_password(password=pwd, user=usr):
        raise ValueError('Login or password incorrect')

    # Log user in
    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.session_expiry_delay
    query = schema.logged_users_table.insert().values(
        token=user_token,
        user_id=usr.id,
        expiration_date=token_best_by
    )
    await zrDB.execute(query)

    return usr, user_token


async def admin_login(*, by_uid: int = Optional[int]):
    if by_uid:
        query = schema.users_table.select().where(
            schema.users_table.c.id == by_uid
        )
    else:
        raise ValueError("Login Parameters do not match !!!")

    usr = await zrDB.fetch_one(query)
    if usr is None:
        raise ValueError('Login or password incorrect')

    usr = schema.User(**usr)
    # Log user in
    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.session_expiry_delay
    query = schema.logged_users_table.insert().values(
        token=user_token,
        user_id=usr.id,
        expiration_date=token_best_by
    )
    await zrDB.execute(query)
    return usr, user_token


async def delete_session(*, by_token: Optional[str] = None, by_uid: Optional[int] = None,
                         clear_all: bool = False):
    """ Delete a specific user session """
    if by_token:
        query = schema.logged_users_table.delete().where(
            schema.logged_users_table.c.token == by_token
        )
    elif by_uid:
        query = schema.logged_users_table.delete().where(
            schema.logged_users_table.c.user_id == by_uid
        )
    elif clear_all:
        query = schema.logged_users_table.delete()
    else:
        raise exc.OptionMissing(
            f"Function {delete_session.__name__} requires an uid or token but None was provided!"
        )
    # returns number of deleted entries
    return await zrDB.execute(query)


async def clear_expired_sessions():
    """ Deletes all expired sessions from the logged_users table """
    query = schema.logged_users_table.delete().where(
        schema.logged_users_table.c.expiration_date <= datetime.now()
    )
    # returns number of deleted entries
    return await zrDB.execute(query)


async def create_password_reset_session(*, username: str, email: str) -> schema.PasswordResetSession:
    try:
        user = await get_user(by_email=email)
    except ValueError:
        raise exc.UserNotFound("the user is not valid")

    if user.username != username:
        raise exc.ValueNotValid("username provided does not match email")

    user_token = secrets.token_urlsafe(64)
    token_best_by = datetime.now() + _settings.password_reset_expiry_delay
    query = schema.password_reset_table.insert().values(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by,
    )
    await zrDB.execute(query)

    return schema.PasswordResetSession(
        token=user_token,
        user_id=user.id,
        expiration_date=token_best_by
    )


async def update_users_password(*, user: schema.User, password: str, password_validation: str):
    """ Change a users password """

    if password != password_validation:
        raise ValueError('passwords do not match')

    hashed_pswd, salt = users_lib.hash_pwd(password=password)
    query = schema.users_table.update().where(
        schema.users_table.c.id == user.id
    ).values(hashed_pswd=hashed_pswd, salt=salt)

    query2 = schema.password_reset_table.delete().where(
        schema.password_reset_table.c.user_id == user.id
    )

    await zrDB.execute(query)
    await zrDB.execute(query2)


async def toggle_user_status(*, user_id: int, active: bool = True):
    """ Toggles a users status for active to inactive """
    query = schema.users_table.update().where(
        schema.users_table.c.id == user_id
    ).values(
        active=active
    )
    res = await zrDB.execute(query)

    if res == 0:
        raise ValueError(f'user {user_id} was not found')


async def toggle_all_users_status(*, active: bool = True):
    """ Toggles a users status for active to inactive """
    query = schema.users_table.update().values(
        active=active
    )
    return await zrDB.execute(query)


async def get_password_reset_sessions(all_sessions: bool = False) -> List[schema.PasswordResetSession]:
    """ Return a list of all users """
    if all_sessions:
        query = schema.password_reset_table.select()
    else:
        query = schema.password_reset_table.select().where(
            schema.password_reset_table.c.expiration_date > datetime.now()
        )
    session_list = await zrDB.fetch_all(query)
    if session_list is None:
        raise ValueError(f'database does not contain any user')
    return [schema.PasswordResetSession(**usr) for usr in session_list]


async def clear_expired_password_reset_sessions():
    """ Deletes all expired password reset sessions from the password_reset_users table """
    query = schema.password_reset_table.delete().where(
        schema.password_reset_table.c.expiration_date <= datetime.now()
    )
    # returns number of deleted entries
    return await zrDB.execute(query)


async def clear_password_reset_sessions(*, by_uid: int):
    """ Deletes all  password reset sessions from the password_reset_users table """
    query = schema.password_reset_table.delete().where(
        schema.password_reset_table.c.user_id == by_uid
    )
    # returns number of deleted entries
    return await zrDB.execute(query)
