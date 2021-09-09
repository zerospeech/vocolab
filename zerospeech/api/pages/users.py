""" Routing for /page section of the API
This section handles any query that returns a page
"""
from fastapi import (
    APIRouter, HTTPException, status,
    Request
)
from fastapi.responses import HTMLResponse

from zerospeech import exc, out
from zerospeech.lib import api_lib
from zerospeech.db.q import userQ
from zerospeech.settings import get_settings

router = APIRouter()

_settings = get_settings()


@router.get('/new-user', response_class=HTMLResponse, include_in_schema=False)
async def new_user_page(request: Request):
    """ Return the form used for creating a new user """
    data = dict(
        image_dir=f"{request.base_url}static/img",
        new_user_url=f"{request.url_for('post_signup')}"
    )
    return api_lib.generate_html_response(data, template_name='signup.html.jinja2')


@router.get('/email-verify', response_class=HTMLResponse, include_in_schema=False)
async def email_verification(v: str, username: str, request: Request):
    """ Verify a new users email address """
    msg = 'Success'
    res = False

    try:
        res = await userQ.verify_user(username=username, verification_code=v)
    except ValueError:
        msg = 'Username does not exist'
    except exc.ActionNotValid as e:
        msg = e.__str__()
    except exc.ValueNotValid as e:
        msg = e.__str__()

    data = {
        "image_dir": f"{api_lib.get_base_url(request)}static/img",
        "success": res,
        "username": username,
        "error": msg,
        "url": "https://zerospeech.com",
        "admin_email": _settings.admin_email,
        "contact_url": "https://zerospeech.com/contact"
    }

    return api_lib.generate_html_response(data=data, template_name='email_verification.html.jinja2')


@router.get('/password-update', response_class=HTMLResponse, include_in_schema=False)
async def password_update_page(v: str, request: Request):
    """ An HTML page-form that allows a user to change their password """
    try:
        user = await userQ.get_user(by_password_reset_session=v)
    except ValueError as e:
        out.Logger.error(
            f'{request.client.host}:{request.client.port} requested bad password reset session as {v} - [{e}]')
        out.exception()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    return api_lib.generate_html_response(data=dict(
        image_dir=f"{api_lib.get_base_url(request)}static/img",
        username=user.username,
        submit_url=f"{api_lib.url_for(request, 'post_password_update')}?v={v}",
        session=v,
    ), template_name='reset_password2.html.jinja2')


@router.get('/request-password-update', response_class=HTMLResponse, include_in_schema=False)
async def request_password_update_page(request: Request):
    """ Html page-form to request a password reset"""

    return api_lib.generate_html_response(data=dict(
        image_dir=f"{api_lib.get_base_url(request)}static/img",
        submit_url=f"{api_lib.url_for(request, 'password_reset_request')}?html_response=true",
    ), template_name='password-reset-request.html.jinja2')
