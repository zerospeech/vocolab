from typing import List, Any, Dict

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from pydantic import BaseModel, EmailStr

from zerospeech.settings import get_settings

_settings = get_settings()

email_cgf = ConnectionConfig(
    MAIL_USERNAME=_settings.MAIL_USERNAME,
    MAIL_PASSWORD=_settings.MAIL_PASSWORD,
    MAIL_FROM=_settings.MAIL_FROM,
    MAIL_FROM_NAME=_settings.MAIL_FROM_NAME,
    MAIL_PORT=_settings.MAIL_PORT,
    MAIL_SERVER=_settings.MAIL_SERVER,
    MAIL_TLS=_settings.MAIL_TLS,
    MAIL_SSL=_settings.MAIL_SSL,
    TEMPLATE_FOLDER=str(_settings.MAIL_TEMPLATE_DIR)
)

fm = FastMail(email_cgf)


async def simple_html_email(emails: List[EmailStr], subject: str, content: str):
    """

    :param emails:
    :param subject:
    :param content:
    :return:
    :raises SomeException when config not valid (todo check which exception)
    """
    message = MessageSchema(
        subject=subject,
        recipients=emails,  # List of recipients, as many as you can pass
        body=content,
        subtype="html"
    )
    return await fm.send_message(message)


async def template_email(emails: List[EmailStr], subject: str, data: Dict[str, Any], template_name: str):
    """ Send an email using an existing jinja2 template

    :param emails: <List[EmailStr]> a list of email recipients
    :param subject: <str> the email subject
    :param data: <Dict[str, Any]> data to be processed into the template
    :param template_name: <str> the filename of the template
    :return: ACK ? (todo check return values)
    :raises SomeException when template is unknown (todo check which exception)
    :raises SomeException when config not valid (todo check which exception)
    """
    message = MessageSchema(
        subject=subject,
        recipients=emails,  # List of recipients, as many as you can pass
        body=data,
        subtype="html"
    )
    return await fm.send_message(message, template_name=template_name)


async def notify_admin(subject: str, data: Dict[str, Any], template_name: str):
    """ Notify the registered admin via email

    :param subject: <str> the email subject
    :param data: <Dict[str, Any]> data to be processed into the template
    :param template_name: <str> the filename of the template
    :return: ACK ? (todo check return values)
    :raises SomeException when template is unknown (todo check which exception)
    :raises SomeException when config not valid (todo check which exception)
    """
    message = MessageSchema(
        subject=subject,
        recipients=[_settings.local.admin_email],
        body=data,
        subtype="html"
    )
    return await fm.send_message(message, template_name=template_name)
