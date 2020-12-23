from datetime import timedelta
from pathlib import Path
from functools import lru_cache
from typing import List, Union
import os

from dotenv import load_dotenv
from pydantic import (
    BaseSettings, EmailStr, BaseModel,
    DirectoryPath, HttpUrl, IPvAnyAddress
)


class ApplicationSettings(BaseModel):
    """ Application Settings """
    # Globals
    app_name: str = "Zerospeech Challenge API"
    maintainers: str = "CoML Team, INRIA, ENS, EHESS, CNRS"
    admin_email: EmailStr = EmailStr("contact@zerospeech.com")

    # Users
    session_expiry_delay: timedelta = timedelta(days=7)
    password_reset_expiry_delay: timedelta = timedelta(minutes=10)

    # Mattermost
    mattermost_url: HttpUrl = 'https://mattermost.syntheticlearner.net/hooks'
    mattermost_username: str = 'AdminBot'
    mattermost_channel: str = 'engineering-private'  # todo change to zerospeech channel

    # Databases
    db_users_file: str = 'users.db'
    db_challenges_file: str = 'challenges.db'

    # Documentation
    doc_title: str = "Zerospeech Challenge API"
    doc_version: str = 'v0'
    doc_description: str = 'A documentation of the API for the Zerospeech Challenge back-end !'


class _Settings(BaseSettings):
    """ Generic Config Class """
    local: ApplicationSettings = ApplicationSettings()

    app_home: Path = Path().cwd()
    version: str = "v0.1"
    favicon: str = 'http://zerospeech.com/_static/favicon.ico'
    origins: List[str] = [
        "http://localhost:8000",
        "http://zerospeech.com",
        "https://zerospeech.com",
        "http://api.zerospeech.com",
        "https://api.zerospeech.com",
    ]
    STATIC_DIR: DirectoryPath = Path("data/_static")
    # Database related settings
    DB_HOME: DirectoryPath = Path('data/db')

    # Mattermost related settings
    MATTERMOST_API_KEY: str = 'super-secret-key'
    MATTERMOST_TEMPLATE_DIR: Path = Path('data/templates/mattermost')
    # Email related settings
    MAIL_USERNAME: Union[EmailStr, str] = EmailStr("email@example.com")
    MAIL_PASSWORD: str = "email-password"
    MAIL_FROM: Union[EmailStr, str] = EmailStr("noreply@example.com")
    MAIL_FROM_NAME: str = "emailUsername"
    MAIL_PORT: int = 587
    MAIL_SERVER: Union[HttpUrl, IPvAnyAddress, str] = "0.0.0.0"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_TEMPLATE_DIR: DirectoryPath = Path('data/templates/emails')

    class Config:
        env_prefix = 'ZR_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> _Settings:
    """ Getter for api setting

    :info uses cache policy for faster loading
    :returns Settings object
    """
    env_file = os.environ.get('ZR_ENV_FILE', None)
    if env_file:
        print(f'loading from env file {env_file}')
        # load_dotenv(dotenv_path=Path(env_file))

        return _Settings(_env_file=env_file, _env_file_encoding='utf-8')
    return _Settings()
