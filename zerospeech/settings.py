import logging
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Union, Set, Dict
import platform

from pydantic import (
    BaseSettings, EmailStr, DirectoryPath, HttpUrl, IPvAnyNetwork
)


class _ZerospeechSettings(BaseSettings):
    """ Base Settings for module """
    # Globals
    app_name: str = "Zerospeech Challenge API"
    app_home: DirectoryPath = Path().cwd()
    version: str = "v0.1"
    maintainers: str = "CoML Team, INRIA, ENS, EHESS, CNRS"
    admin_email: EmailStr = EmailStr("contact@zerospeech.com")
    hostname: str = platform.node()
    DATA_FOLDER: DirectoryPath = Path('data/')

    # Databases
    db_file: str = 'zerospeech.db'

    # Documentation
    doc_title: str = "Zerospeech Challenge API"
    doc_version: str = 'v0'
    doc_description: str = 'A documentation of the API for the Zerospeech Challenge back-end !'

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
    HOSTS: Set[str] = set()
    REMOTE_STORAGE: Dict[str, Path] = dict()
    REMOTE_BIN: Dict[str, Path] = dict()

    # FastAPI settings
    DEBUG: bool = True
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

    # Data Locations
    STATIC_DIR: Path = DATA_FOLDER / "_static"
    USER_DATA_DIR: Path = DATA_FOLDER / 'user_data'
    SUBMISSION_DIR: Path = DATA_FOLDER / 'submissions'

    # Templates Locations
    TEMPLATES_DIR: Path = DATA_FOLDER / 'templates'
    HTML_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'pages'
    MATTERMOST_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'mattermost'

    # Mattermost
    mattermost_url: HttpUrl = 'https://mattermost.cognitive-ml.fr/hooks'
    mattermost_username: str = 'AdminBot'
    mattermost_channel: str = 'engineering-private'  # todo change to zerospeech channel
    MATTERMOST_API_KEY: str = 'super-secret-key'

    # Email related settings
    MAIL_USERNAME: Union[EmailStr, str] = EmailStr("email@example.com")
    MAIL_PASSWORD: str = "email-password"
    MAIL_FROM: Union[EmailStr, str] = EmailStr("noreply@example.com")
    MAIL_FROM_NAME: str = "emailUsername"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "0.0.0.0"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'emails'

    class Config:
        env_prefix = 'ZR_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> _ZerospeechSettings:
    """ Getter for api settings

    :info uses cache policy for faster loading
    :returns Settings object
    """
    # external settings override from .env file
    env_file = os.environ.get('ZR_ENV_FILE', None)

    if env_file:
        return _ZerospeechSettings(_env_file=env_file, _env_file_encoding='utf-8')
    return _ZerospeechSettings()
