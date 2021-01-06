""" Routing for /auth section of the API
This section handles user authentication, user creation, etc..
"""

from pydantic import BaseModel, EmailStr
from fastapi import (
    FastAPI, Depends, Response, HTTPException, status,
    Request, BackgroundTasks, Form
)
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from zerospeech import exc
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings
from zerospeech.api import api_utils
from zerospeech.db import q as queries, schema
from zerospeech.utils import notify

auth_app = FastAPI()
logger = LogSingleton.get()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_settings = get_settings()


class LoggedItem(BaseModel):
    """ Return type of the /login function """
    access_token: str
    token_type: str


class CurrentUser(BaseModel):
    """ Basic userinfo Model """
    username: str
    email: EmailStr


class PasswordResetRequest(BaseModel):
    username: str
    email: EmailStr


async def validate_token(token: str = Depends(oauth2_scheme)) -> schema.LoggedUser:
    """ Dependency for validating the current users session via the token"""
    try:
        token_item = await queries.users.validate_token(token)
        return token_item
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not found or invalid !",
        )


async def get_user(token: schema.LoggedUser = Depends(validate_token)) -> schema.User:
    """ Dependency for fetching current user from database using token entry """
    try:
        user = await queries.users.get_user(by_uid=token.user_id)
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not in database !"
        )


async def get_current_active_user(current_user: schema.User = Depends(get_user)) -> schema.User:
    """ Dependency for validating current user """
    if current_user.verified == 'True':
        if current_user.active:
            return current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User inactive, should not connect'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail='User not verified'
        )


@auth_app.post('/login', response_model=LoggedItem)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        _, token = await queries.users.login_user(form_data.username, form_data.password)
        return LoggedItem(access_token=token, token_type="bearer")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )


@auth_app.get('/check', response_model=CurrentUser)
async def check(current_user: schema.User = Depends(get_current_active_user)):
    return CurrentUser(
        username=current_user.username,
        email=current_user.email
    )


@auth_app.delete('/logout')
async def logout(token: schema.LoggedUser = Depends(validate_token)):
    await queries.users.delete_session(token.token)
    return Response(status_code=200)


@auth_app.put('/signup')
async def signup(request: Request, user: queries.users.UserCreate, background_tasks: BackgroundTasks):
    try:
        verification_code = await queries.users.create_user(user)
    except exc.ValueNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This {e.data} already exists !!",
        )

    data = {
        'username': user.username,
        'url': f"{request.url_for('email_verification')}?v={verification_code}&username={user.username}",
        'admin_email': _settings.local.admin_email
    }
    background_tasks.add_task(notify.email.template_email,
                              emails=[user.email],
                              subject='[Zerospeech] Account Verification',
                              data=data,
                              template_name='email_validation.jinja2'
                              )
    return Response(status_code=200)


@auth_app.get('/email/verify', response_class=HTMLResponse)
async def email_verification(v: str, username: str):
    msg = 'Success'
    res = False

    try:
        res = await queries.users.verify_user(username, v)
    except ValueError:
        msg = 'Username does not exist'
    except exc.ActionNotValidError as e:
        msg = e.__str__()
    except exc.ValueNotValidError as e:
        msg = e.__str__()

    data = {
        "success": res,
        "username": username,
        "error": msg,
        "url": "https://zerospeech.com",
        "admin_email": _settings.local.admin_email,
        "contact_url": "https://zerospeech.com/contact"
    }

    return notify.html.generate_html_response(data=data, template_name='email_verification.html.jinja2')


@auth_app.post('/password/reset')
async def password_reset_request(user: PasswordResetRequest, request: Request, background_tasks: BackgroundTasks):
    session = await queries.users.create_password_reset_session(username=user.username, email=user.email)
    data = {
        'username': user.username,
        'url': f"{request.url_for('password_update_page')}?v={session.token}",
        'admin_email': _settings.local.admin_email
    }
    background_tasks.add_task(notify.email.template_email,
                              emails=[user.email],
                              subject='[Zerospeech] Password Reset',
                              data=data,
                              template_name='password_reset.jinja2'
                              )
    return Response(status_code=200)


@auth_app.get('/password/update/page', response_class=HTMLResponse)
async def password_update_page(v: str, request: Request):
    try:
        user = await queries.users.get_user(by_password_reset_session=v)
    except ValueError as e:
        logger.error(f'{request.client.host}:{request.client.port} requested bad password reset session as {v} - [{e}]')

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    data = {
        "username": user.username,
        "submit_url": f"/auth{auth_app.url_path_for('password_update')}?v={v}",
        "session": v
    }

    return notify.html.generate_html_response(data=data, template_name='password_reset.html.jinja2')


@auth_app.post('/password/update', response_class=PlainTextResponse)
async def password_update(v: str, request: Request, password: str = Form(...),
                          password_validation: str = Form(...), session_code: str = Form(...)):
    try:
        if v != session_code:
            raise ValueError('session validation not passed !!!')

        user = await queries.users.get_user(by_password_reset_session=v)
    except ValueError as e:
        logger.error(f'{request.client.host}:{request.client.port} requested bad password reset session as {v} - [{e}]')

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    await queries.users.update_users_password(user, password, password_validation)

    # maybe return result as page ?
    return f'password of {user.username}  successfully changed !!'


@auth_app.delete('/deactivate')
async def deactivate_user():
    # todo: implement password update
    return 'OK'


# Set docs parameters
api_utils.set_documentation_params(auth_app)
