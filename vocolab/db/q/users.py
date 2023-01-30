import secrets
from datetime import datetime
from typing import Optional, List


from email_validator import validate_email, EmailNotValidError

from vocolab import exc, out
from vocolab.db import zrDB, models, schema, exc as db_exc
from vocolab.core import users_lib
from vocolab.settings import get_settings

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


async def get_user_for_login(login_id: str, password: str) -> Optional[schema.User]:
    """
    :params login_id<str>: the login id can be username or email
    :params password<str>: the user's password
    """
    try:
        validate_email(login_id)  # check if email is valid
        query = schema.users_table.select().where(
            schema.users_table.c.email == login_id
        )
    except EmailNotValidError:
        query = schema.users_table.select().where(
            schema.users_table.c.username == login_id
        )

    user = await zrDB.fetch_one(query)
    if user is None:
        return None
    user = schema.User(**user)
    out.console.print(f"===> {user=}")

    hashed_pswd, _ = users_lib.hash_pwd(password=password, salt=user.salt)
    if user.enabled and hashed_pswd == user.hashed_pswd:
        return user
    return None


async def get_user(*, by_uid: Optional[int] = None, by_username: Optional[str] = None,
                   by_email: Optional[str] = None) -> schema.User:
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


async def update_users_password(*, user: schema.User, password: str, password_validation: str):
    """ Change a users password """

    if password != password_validation:
        raise ValueError('passwords do not match')

    hashed_pswd, salt = users_lib.hash_pwd(password=password)
    query = schema.users_table.update().where(
        schema.users_table.c.id == user.id
    ).values(hashed_pswd=hashed_pswd, salt=salt)

    await zrDB.execute(query)


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
