from typing import List, Any, Dict

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from zerospeech import get_settings, out

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


def parse_email_exceptions(e: Exception):
    from fastapi_mail.errors import ConnectionErrors, WrongFile, TemplateFolderDoesNotExist

    if isinstance(e, ConnectionErrors):
        out.error("issues with connections ?")
    raise e


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
    try:
        await fm.send_message(message)
        out.Logger.info(f'email send successfully to {emails}')
    except Exception as e:
        parse_email_exceptions(e)


async def template_email1(emails: List[EmailStr], subject: str, data: Dict[str, Any], template_name: str):
    """ Send an email using an existing jinja2 template

    :param emails: <List[EmailStr]> a list of email recipients
    :param subject: <str> the email subject
    :param data: <Dict[str, Any]> data to be processed into the template
    :param template_name: <str> the filename of the template
    """
    message = MessageSchema(
        subject=subject,
        recipients=emails,
        body=data,
        subtype="html"
    )
    out.ic(message)
    try:
        await fm.send_message(message, template_name=template_name)
        out.info(f'email send successfully to {emails}')
    except Exception as e:
        # out.Logger.error(f"an issue occurred while sending an email to {emails}")
        # parse_email_exceptions(e)
        out.exception()


async def template_email2(emails: List[EmailStr], subject: str, data: Dict[str, Any], template_name: str):
    """ Send an email using an existing jinja2 template

    :param emails: <List[EmailStr]> a list of email recipients
    :param subject: <str> the email subject
    :param data: <Dict[str, Any]> data to be processed into the template
    :param template_name: <str> the filename of the template
    """
    template = Environment(loader=FileSystemLoader(_settings.MAIL_TEMPLATE_DIR), trim_blocks=True) \
        .get_template(template_name)

    body = template.render(body=data)

    message = MessageSchema(
        subject=subject,
        recipients=emails,
        body=body,
        subtype="html"
    )
    out.ic(message)
    try:
        await fm.send_message(message, template_name=template_name)
        out.info(f'email send successfully to {emails}')
    except Exception as e:
        # out.Logger.error(f"an issue occurred while sending an email to {emails}")
        # parse_email_exceptions(e)
        out.exception()


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
        recipients=[_settings.admin_email],
        body=data,
        subtype="html"
    )
    try:
        await fm.send_message(message, template_name=template_name)
        out.Logger.info(f'email send successfully to {_settings.admin_email}')
    except Exception as e:
        parse_email_exceptions(e)


# set version
template_email = template_email2
