""" Routing for /page section of the API
This section handles any query that returns a page
"""
from fastapi import (
    APIRouter, HTTPException, status,
    Request
)
from fastapi.responses import HTMLResponse
from rich.console import Console

from zerospeech import exc
from zerospeech.api import api_utils
from zerospeech.db import q as queries
from zerospeech.log import LogSingleton
from zerospeech.settings import get_settings

router = APIRouter()
logger = LogSingleton.get()

_settings = get_settings()
console = Console()


@router.get('/new-user', response_class=HTMLResponse)
async def new_user_page():
    # todo
    return api_utils.generate_html_response(data={}, template_name='')


@router.get('/email-verify', response_class=HTMLResponse)
async def email_verification(v: str, username: str):
    """ Verify a new users email address """
    msg = 'Success'
    res = False

    try:
        res = await queries.users.verify_user(username, v)
    except ValueError:
        msg = 'Username does not exist'
    except exc.ActionNotValid as e:
        msg = e.__str__()
    except exc.ValueNotValid as e:
        msg = e.__str__()

    data = {
        "success": res,
        "username": username,
        "error": msg,
        "url": "https://zerospeech.com",
        "admin_email": _settings.admin_email,
        "contact_url": "https://zerospeech.com/contact"
    }

    return api_utils.generate_html_response(data=data, template_name='email_verification.html.jinja2')


@router.get('/password-update', response_class=HTMLResponse)
async def password_update_page(v: str, request: Request):
    """ An HTML page-form that allows a user to change their password """
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
        "submit_url": f"/auth{router.url_path_for('password_update')}?v={v}",
        "session": v
    }

    return api_utils.generate_html_response(data=data, template_name='password_reset.html.jinja2')
