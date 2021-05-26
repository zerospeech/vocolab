from fastapi import Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any

from jinja2 import FileSystemLoader, Environment

from zerospeech import settings
from zerospeech.db import q as queries, schema
from zerospeech.utils import notify

_settings = settings.get_settings()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def validate_token(token: str = Depends(oauth2_scheme)) -> schema.LoggedUser:
    """ Dependency for validating the current users session via the token"""
    try:
        token_item = await queries.users.validate_token(token=token)
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


def generate_html_response(data: Dict[str, Any], template_name: str) -> str:
    """ Render an html template using values from data"""
    env = Environment(loader=FileSystemLoader(_settings.HTML_TEMPLATE_DIR))
    template = env.get_template(template_name)
    return template.render(**data)


async def signup(request: Request, user: queries.users.UserCreate, background_tasks: BackgroundTasks):
    """ Creates a new user and schedules the registration email """
    verification_code = await queries.users.create_user(usr=user)
    data = {
        'username': user.username,
        'url': f"{request.url_for('email_verification')}?v={verification_code}&username={user.username}",
        'admin_email': _settings.admin_email
    }
    background_tasks.add_task(notify.email.template_email,
                              emails=[user.email],
                              subject='[Zerospeech] Account Verification',
                              data=data,
                              template_name='email_validation.jinja2')
