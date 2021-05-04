""" Routing for /auth section of the API
This section handles user authentication, user creation, etc..
"""
from fastapi import (
    APIRouter, Depends, Response, HTTPException, status,
    Request, BackgroundTasks, Form
)
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm

from rich.console import Console

from zerospeech import exc
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings
from zerospeech.api import api_utils, models
from zerospeech.db import q as queries, schema
from zerospeech.utils import notify

router = APIRouter()
logger = LogSingleton.get()

_settings = get_settings()
console = Console()


@router.post('/login', response_model=models.LoggedItem)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """ Authenticate a user """
    try:
        _, token = await queries.users.login_user(form_data.username, form_data.password)
        # inspect(form_data)
        return models.LoggedItem(access_token=token, token_type="bearer")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )


@router.delete('/logout')
async def logout(token: schema.LoggedUser = Depends(api_utils.validate_token)):
    """ Delete a user's session """
    await queries.users.delete_session(token.token)
    return Response(status_code=200)


# todo: move model
@router.put('/signup')
async def signup(request: Request, user: queries.users.UserCreate, background_tasks: BackgroundTasks):
    """ Create a new user """
    try:
        verification_code = await queries.users.create_user(user)
    except exc.ValueNotValid as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This {e.data} already exists !!",
        )

    data = {
        'username': user.username,
        'url': f"{request.url_for('email_verification')}?v={verification_code}&username={user.username}",
        'admin_email': _settings.admin_email
    }
    background_tasks.add_task(notify.email.template_email,
                              emails=[user.email],
                              subject='[Zerospeech] Account Verification',
                              data=data,
                              template_name='email_validation.jinja2'
                              )
    return Response(status_code=200)


@router.post('/password/reset')
async def password_reset_request(
        user: models.PasswordResetRequest, request: Request, background_tasks: BackgroundTasks):
    """ Request a users password to be reset """
    session = await queries.users.create_password_reset_session(username=user.username, email=user.email)
    data = {
        'username': user.username,
        'url': f"{request.url_for('password_update_page')}?v={session.token}",
        'admin_email': _settings.admin_email
    }
    background_tasks.add_task(notify.email.template_email,
                              emails=[user.email],
                              subject='[Zerospeech] Password Reset',
                              data=data,
                              template_name='password_reset.jinja2'
                              )
    return Response(status_code=200)


@router.post('/password/update', response_class=PlainTextResponse)
async def password_update(v: str, request: Request, password: str = Form(...),
                          password_validation: str = Form(...), session_code: str = Form(...)):
    """Update a users password (requires a reset session)"""
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
