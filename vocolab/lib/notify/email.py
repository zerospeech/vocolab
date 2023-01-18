from typing import List, Any, Dict

from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from vocolab import get_settings, out

_settings = get_settings()

email_cgf = ConnectionConfig(
    MAIL_USERNAME=_settings.notify_options.MAIL_USERNAME,
    MAIL_PASSWORD=_settings.notify_options.MAIL_PASSWORD,
    MAIL_FROM=_settings.notify_options.MAIL_FROM,
    MAIL_FROM_NAME=_settings.notify_options.MAIL_FROM_NAME,
    MAIL_PORT=_settings.notify_options.MAIL_PORT,
    MAIL_SERVER=_settings.notify_options.MAIL_SERVER,
    # todo: investigate why this changed to MAIL_SSL_TLS &  MAIL_STARTTLS and if it still works
    # MAIL_TLS=_settings.notify_options.MAIL_TLS,
    # MAIL_SSL=_settings.notify_options.MAIL_SSL,
    MAIL_STARTTLS=_settings.notify_options.MAIL_STARTTLS,
    MAIL_SSL_TLS=_settings.notify_options.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=_settings.email_templates_dir
)

fm = FastMail(email_cgf)


def parse_email_exceptions(e: Exception):
    from fastapi_mail.errors import ConnectionErrors

    if isinstance(e, ConnectionErrors):
        out.console.error("issues with connections ?")
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
        subtype=MessageType.html
    )
    try:
        await fm.send_message(message)
        out.log.info(f'email send successfully to {emails}')
    except Exception as e:
        parse_email_exceptions(e)


async def template_email1(emails: List[EmailStr], subject: str, data, template_name: str):
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
        subtype=MessageType.html
    )
    out.console.ic(message)
    try:
        await fm.send_message(message, template_name=template_name)
        out.log.info(f'email send successfully to {emails}')
    except Exception:
        # out.Logger.error(f"an issue occurred while sending an email to {emails}")
        # parse_email_exceptions(e)
        out.log.exception()
        raise


async def template_email2(emails: List[EmailStr], subject: str, data: Dict[str, Any], template_name: str):
    """ Send an email using an existing jinja2 template

    :param emails: <List[EmailStr]> a list of email recipients
    :param subject: <str> the email subject
    :param data: <Dict[str, Any]> data to be processed into the template
    :param template_name: <str> the filename of the template
    """
    template = Environment(loader=FileSystemLoader(_settings.email_templates_dir), trim_blocks=True) \
        .get_template(template_name)

    body = template.render(body=data)

    message = MessageSchema(
        subject=subject,
        recipients=emails,
        body=body,
        subtype=MessageType.html
    )
    out.console.ic(message)
    try:
        await fm.send_message(message)
        out.log.info(f'email send successfully to {emails}')
    except Exception:
        # out.Logger.error(f"an issue occurred while sending an email to {emails}")
        # parse_email_exceptions(e)
        out.log.exception()
        raise


async def notify_admin(subject: str, data, template_name: str):
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
        recipients=[_settings.app_options.admin_email],
        body=data,
        subtype=MessageType.html
    )
    try:
        await fm.send_message(message, template_name=template_name)
        out.log.info(f'email send successfully to {_settings.app_options.admin_email}')
    except Exception as e:
        parse_email_exceptions(e)


# set version
template_email = template_email2
