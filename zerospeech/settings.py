import logging
import os
from datetime import timedelta
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Union, Set, Dict

from pydantic import (
    BaseSettings, EmailStr, DirectoryPath, HttpUrl, IPvAnyNetwork,
)


class _LocalBaseSettings(BaseSettings):
    # Globals
    app_name: str = "Zerospeech Challenge API"
    maintainers: str = "CoML Team, INRIA, ENS, EHESS, CNRS"
    admin_email: EmailStr = EmailStr("contact@zerospeech.com")

    # Databases
    db_file: str = 'zerospeech.db'
    app_data: str = 'appdata'

    # Documentation
    doc_title: str = "Zerospeech Challenge API"
    doc_version: str = 'v0'
    doc_description: str = 'A documentation of the API for the Zerospeech Challenge back-end !'

    DATA_FOLDER: DirectoryPath = Path('data/')

    # Logging info
    LOG_LEVEL: int = logging.INFO
    LOGGER_TYPE: str = 'console'
    LOG_FILE: Path = Path('out.log')

    # Task Queue
    RPC_USERNAME: str = "admin"
    RPC_PASSWORD: str = "123"
    RPC_HOST: Union[IPvAnyNetwork, str] = "localhost"
    RPC_PORT: int = 5672

    # Remote Settings
    REMOTE_HOSTS: Set[str] = set()
    REMOTE_STORAGE: Dict[str, Path] = dict()
    REMOTE_BIN: Dict[str, Path] = dict()

    class Config:
        env_prefix = 'ZR_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


class _APISettings(_LocalBaseSettings):
    """ Generic API Config Class """
    API_V1_STR: str = '/v1'
    DEBUG: bool = True

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
    # Users
    session_expiry_delay: timedelta = timedelta(days=7)
    password_reset_expiry_delay: timedelta = timedelta(minutes=45)

    # Mattermost
    mattermost_url: HttpUrl = 'https://mattermost.cognitive-ml.fr/hooks'
    mattermost_username: str = 'AdminBot'
    mattermost_channel: str = 'engineering-private'  # todo change to zerospeech channel
    # Data
    DATA_FOLDER: DirectoryPath = Path('data/')

    STATIC_DIR: DirectoryPath = DATA_FOLDER / "/_static"

    # Database related settings
    DB_HOME: DirectoryPath = DATA_FOLDER / 'db'
    USER_DATA_DIR: DirectoryPath = DB_HOME / 'user_data'

    # Templates Folder
    TEMPLATES_DIR: DirectoryPath = DATA_FOLDER / 'templates'
    HTML_TEMPLATE_DIR: DirectoryPath = TEMPLATES_DIR / 'pages'

    # Mattermost related settings
    MATTERMOST_API_KEY: str = 'super-secret-key'
    MATTERMOST_TEMPLATE_DIR: DirectoryPath = TEMPLATES_DIR / 'mattermost'

    # Email related settings
    MAIL_USERNAME: Union[EmailStr, str] = EmailStr("email@example.com")
    MAIL_PASSWORD: str = "email-password"
    MAIL_FROM: Union[EmailStr, str] = EmailStr("noreply@example.com")
    MAIL_FROM_NAME: str = "emailUsername"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "0.0.0.0"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_TEMPLATE_DIR: DirectoryPath = TEMPLATES_DIR / 'emails'


class _QueueWorkerSettings(_LocalBaseSettings):
    DATA_FOLDER: Path = Path('data/')


class SettingsTypes(str, Enum):
    api = "api"
    queue_worker = "queue_worker"

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
def get_settings() -> Union[_APISettings, _QueueWorkerSettings]:
    """ Getter for api setting

    :info uses cache policy for faster loading
    :returns Settings object
    """
    env_file = os.environ.get('ZR_ENV_FILE', None)
    # ENV type overwrites given type
    if 'ZR_INVOKE_TYPE' in os.environ:
        # load settings object
        cls = SettingsTypes(os.environ.get('ZR_INVOKE_TYPE')).to_cls()
    else:
        cls = SettingsTypes('api').to_cls()

    # check if env file overrides values
    if env_file:
        return cls(_env_file=env_file, _env_file_encoding='utf-8')
    return cls()
