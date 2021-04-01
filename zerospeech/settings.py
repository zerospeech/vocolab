import logging
import os
from datetime import timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Union

from pydantic import (
    BaseSettings, EmailStr, BaseModel,
    DirectoryPath, HttpUrl, IPvAnyNetwork,

)


class ApplicationSettings(BaseModel):
    """ Application Settings """
    # Globals
    app_name: str = "Zerospeech Challenge API"
    maintainers: str = "CoML Team, INRIA, ENS, EHESS, CNRS"
    admin_email: EmailStr = EmailStr("contact@zerospeech.com")

    # Users
    session_expiry_delay: timedelta = timedelta(days=7)
    password_reset_expiry_delay: timedelta = timedelta(minutes=45)

    # Mattermost
    mattermost_url: HttpUrl = 'https://mattermost.cognitive-ml.fr/hooks'
    mattermost_username: str = 'AdminBot'
    mattermost_channel: str = 'engineering-private'  # todo change to zerospeech channel

    # Databases
    db_file: str = 'zerospeech.db'

    # Documentation
    doc_title: str = "Zerospeech Challenge API"
    doc_version: str = 'v0'
    doc_description: str = 'A documentation of the API for the Zerospeech Challenge back-end !'

    # Relative Location
    broker_bin: str = "bin"


class _LocalBaseSettings(BaseSettings):
    local: ApplicationSettings = ApplicationSettings()

    # Logging info
    LOG_LEVEL: int = logging.INFO
    LOGGER_TYPE: str = 'console'
    LOG_FILE: Path = Path('out.log')

    # Task Queue
    RPC_USERNAME: str = "admin"
    RPC_PASSWORD: str = "123"
    RPC_HOST: Union[IPvAnyNetwork, str] = "0.0.0.0"

    # Remote Settings
    SHARED_STORAGE: bool = True
    REMOTE: Union[IPvAnyNetwork, str] = 'oberon'
    REMOTE_PATH: Path = "/zerospeech"

    class Config:
        env_prefix = 'ZR_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


class _APISettings(_LocalBaseSettings):
    """ Generic API Config Class """
    API_V1_STR: str = '/v1'

    app_home: Path = Path().cwd()
    version: str = "v0.1"
    favicon: str = 'http://zerospeech.com/_static/favicon.ico'
    origins: List[str] = [
        "http://localhost:1313",
        "http://zerospeech.com",
        "https://zerospeech.com",
        "http://api.zerospeech.com",
        "https://api.zerospeech.com",
    ]
    STATIC_DIR: DirectoryPath = Path("data/_static")
    HTML_TEMPLATE_DIR: DirectoryPath = Path('data/templates/pages')
    # Database related settings
    DB_HOME: DirectoryPath = Path('data/db')
    USER_DATA_DIR: DirectoryPath = Path('data/db/user_data')

    # Mattermost related settings
    MATTERMOST_API_KEY: str = 'super-secret-key'
    MATTERMOST_TEMPLATE_DIR: Path = Path('data/templates/mattermost')
    # Email related settings
    MAIL_USERNAME: Union[EmailStr, str] = EmailStr("email@example.com")
    MAIL_PASSWORD: str = "email-password"
    MAIL_FROM: Union[EmailStr, str] = EmailStr("noreply@example.com")
    MAIL_FROM_NAME: str = "emailUsername"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "0.0.0.0"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_TEMPLATE_DIR: DirectoryPath = Path('data/templates/emails')


class _QueueWorkerSettings(_LocalBaseSettings):
    pass


class SettingsTypes(str, Enum):
    api = "api"
    queue_worker = "queue_worker"
    cli = "cli"

    def to_cls(self) -> Union[_APISettings.__class__, _QueueWorkerSettings.__class__]:
        if self == SettingsTypes.api:
            return _APISettings
        elif self == SettingsTypes.cli:
            return _APISettings
        elif self == SettingsTypes.queue_worker:
            return _QueueWorkerSettings
        else:
            raise ValueError('unknown app type')


@lru_cache()
def get_settings(settings_type: str = SettingsTypes.api) -> Union[_APISettings, _QueueWorkerSettings]:
    """ Getter for api setting

    :info uses cache policy for faster loading
    :returns Settings object
    """
    env_file = os.environ.get('ZR_ENV_FILE', None)
    # load settings object
    cls = SettingsTypes(settings_type).to_cls()

    # check if env file overrides values
    if env_file:
        return cls(_env_file=env_file, _env_file_encoding='utf-8')
    return cls()
