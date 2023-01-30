import asyncio
from typing import Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jinja2 import FileSystemLoader, Environment

from vocolab import settings
from vocolab.db import schema, models
from vocolab.db.q import userQ
from vocolab.core import notify, commons

_settings = settings.get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# export
file2dict = commons.load_dict_file


def validate_token(token: str = Depends(oauth2_scheme)) -> schema.Token:
    """ Dependency for validating the current users session via the token"""
    try:
        token = schema.Token.decode(token)
        if token.is_expired():
            raise ValueError('Token has expired')

        if token.allow_password_reset:
            raise ValueError('Token only for password reset purposes')

        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired !",
        )


async def get_user(token: schema.Token = Depends(validate_token)) -> schema.User:
    """ Dependency for fetching current user from database using token entry """
    try:
        return await userQ.get_user(by_email=token.user_email)
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


def generate_html_response(data: Dict[str, Any], template_name: str) -> str:
    """ Render an html template using values from data"""
    env = Environment(loader=FileSystemLoader(_settings.html_templates_dir))
    template = env.get_template(template_name)
    return template.render(**data)


async def signup(request: Request, user: models.misc.UserCreate):
    """ Creates a new user and schedules the registration email """
    verification_code = await userQ.create_user(usr=user)
    data = {
        'username': user.username,
        # todo check if url needs update
        'url': f"{request.url_for('email_verification')}?v={verification_code}&username={user.username}",
        'admin_email': _settings.app_options.admin_email
    }
    # run in the background
    loop = asyncio.get_running_loop()
    loop.create_task(notify.email.template_email(
        emails=[user.email],
        subject='[Zerospeech] Account Verification',
        data=data,
        template_name='email_validation.jinja2')
    )


def get_base_url(request: Request) -> str:
    base_url = f"{request.base_url}"

    headers = request.headers
    if 'x-forwarded-proto' in headers and headers['x-forwarded-proto'] == 'https':
        return base_url.replace('http', 'https')
    else:
        return base_url


def url_for(request: Request, path_requested: str) -> str:
    url = request.url_for(path_requested)

    headers = request.headers
    if 'x-forwarded-proto' in headers and headers['x-forwarded-proto'] == 'https':
        return url.replace('http', 'https')
    else:
        return url
