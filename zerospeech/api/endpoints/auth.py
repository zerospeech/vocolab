""" Routing for /auth section of the API
This section handles user authentication, user creation, etc..
"""
from fastapi import (
    APIRouter, Depends, Response, HTTPException, status,
    Request, BackgroundTasks, Form
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from zerospeech import exc, out
from zerospeech.db import schema, models
from zerospeech.db.q import userQ
from zerospeech.lib import api_lib, notify
from zerospeech.settings import get_settings

router = APIRouter()

_settings = get_settings()


@router.post('/login', response_model=models.api.LoggedItem)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """ Authenticate a user """
    try:
        _, token = await userQ.login_user(login=form_data.username, pwd=form_data.password)
        out.inspect(form_data)
        return models.api.LoggedItem(access_token=token, token_type="bearer")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )


@router.delete('/logout')
async def logout(token: schema.LoggedUser = Depends(api_lib.validate_token)):
    """ Delete a user's session """
    await userQ.delete_session(by_token=token.token)
    return Response(status_code=200)


@router.put('/signup')
async def put_signup(request: Request, user: models.misc.UserCreate):
    """ Create a new user """
    try:
        await api_lib.signup(request, user)
    except exc.ValueNotValid as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This {e.data} already exists !!",
        )
    return Response(status_code=200)


@router.post('/signup', response_class=HTMLResponse)
async def post_signup(request: Request,
                      first_name: str = Form(...), last_name: str = Form(...),
                      affiliation: str = Form(...), email: EmailStr = Form(...),
                      username: str = Form(...), password: str = Form(...)):
    """ Create a new user via the HTML form  (returns an html page) """
    user = models.misc.UserCreate(
        username=username,
        email=email,
        pwd=password,
        last_name=last_name,
        first_name=first_name,
        affiliation=affiliation
    )
    try:
        await api_lib.signup(request, user)
    except exc.ValueNotValid as e:
        data = dict(
            image_dir=f"{request.base_url}static/img",
            title=f"{e.data} already in use",
            redirect_url=f"javascript:history.back()",
            redirect_label="go back to form",
            success=False
        )
        out.Logger.error(f'This {e.data} is already in use, cannot recreate ({user})')
    else:
        data = dict(
            image_dir=f"{request.base_url}static/img",
            title=f"Account created successfully",
            body=f"A verification email will be sent to {email}",
            success=True
        )
    return api_lib.generate_html_response(data, template_name='response.html.jinja2')


@router.post('/password/reset', response_class=JSONResponse)
async def password_reset_request(
        user: models.api.PasswordResetRequest, request: Request, background_tasks: BackgroundTasks):
    """ Request a users password to be reset """
    session = await userQ.create_password_reset_session(username=user.username, email=user.email)
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


@router.post('/password/update', response_class=HTMLResponse)
async def post_password_update(v: str, request: Request, password: str = Form(...),
                               password_validation: str = Form(...), session_code: str = Form(...)):
    """Update a users password (requires a reset session)"""
    try:
        if v != session_code:
            raise ValueError('session validation not passed !!!')

        user = await userQ.get_user(by_password_reset_session=v)
        await userQ.update_users_password(user=user, password=password, password_validation=password_validation)
    except ValueError as e:
        out.Logger.error(
            f'{request.client.host}:{request.client.port} requested bad password reset session as {v} - [{e}]')

        data = dict(
            image_dir=f"{request.base_url}static/img",
            title=f"Password update failed !!",
            body=f'{e}',
            redirect_url=f"javascript:history.back()",
            redirect_label="go back to form",
            success=False

        )
    else:
        data = dict(
            image_dir=f"{request.base_url}static/img",
            title=f"Password of {user.username} was updated successfully",
            body=f"",
            success=True
        )

    return api_lib.generate_html_response(data, template_name='response.html.jinja2')


@router.put('/password/update', response_class=JSONResponse)
async def put_password_update(v: str, request: Request, password: str = Form(...),
                              password_validation: str = Form(...), session_code: str = Form(...)):
    """Update a users password (requires a reset session)"""
    try:
        if v != session_code:
            raise ValueError('session validation not passed !!!')

        user = await userQ.get_user(by_password_reset_session=v)
    except ValueError as e:
        out.Logger.error(
            f'{request.client.host}:{request.client.port} requested bad password reset session as {v} - [{e}]')

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    await userQ.update_users_password(user=user, password=password, password_validation=password_validation)
    return Response(status_code=200)
