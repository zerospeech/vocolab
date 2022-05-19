import shutil

import os
import platform
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import List, Union, Set, Dict, Optional

from pydantic import (
    BaseSettings, EmailStr, DirectoryPath, HttpUrl, IPvAnyNetwork, BaseModel
)


class CeleryWorkerOptions(BaseModel):
    celery_bin: Path = Path(shutil.which('celery'))
    celery_nodes: Dict[str, str] = {'eval': 'vc-evaluate-node', 'update': 'vc-update-node'}
    celery_app: str = 'vocolab.worker.server:app'
    celery_pool_type: str = "prefork"
    celery_worker_number: int = 2


class _VocoLabSettings(BaseSettings):
    """ Base Settings for module """
    # Globals
    app_name: str = "VocoLab Challenge API"
    app_home: DirectoryPath = Path(__file__).parent
    version: str = "v0.1"
    maintainers: str = "CoML Team, INRIA, ENS, EHESS, CNRS"
    admin_email: EmailStr = EmailStr("contact@zerospeech.com")
    hostname: str = platform.node()
    DATA_FOLDER: DirectoryPath = Path('data/')
    API_BASE_URL: str = "https://api.vocolab.com"

    # Databases
    db_file: str = 'vocolab.db'

    # Documentation
    doc_title: str = "VocoLab Challenge API"
    doc_version: str = 'v0.5'
    doc_description: str = 'A documentation of the API for the VocoLab Challenge back-end !'

    # Console & Logging
    DEBUG: bool = True
    COLORS: bool = True
    QUIET: bool = False
    VERBOSE: bool = True
    ALLOW_PRINTS: bool = True
    ROTATING_LOGS: bool = True
    LOG_FILE: Optional[Path] = None
    ERROR_LOG_FILE: Optional[Path] = None

    # Task Queue
    RPC_USERNAME: str = "admin"
    RPC_PASSWORD: str = "123"
    RPC_HOST: Union[IPvAnyNetwork, str] = "localhost"
    RPC_VHOST: str = "vocolab"
    RPC_PORT: int = 5672
    RPC_CHANNELS: Dict[str, str] = dict(
        eval="vocolab-eval", update="vocolab-update", echo="vocolab-msg"
    )
    celery_options: CeleryWorkerOptions = CeleryWorkerOptions()

    # Remote Settings
    HOSTS: Set[str] = set()
    REMOTE_STORAGE: Dict[str, Path] = dict()
    REMOTE_BIN: Dict[str, Path] = dict()

    # FastAPI settings
    favicon: str = 'https://api.vocolab.com/static/favicon.ico'
    origins: List[str] = [
        # local debug urls
        "http://vocolab.test",
        "http://api.vocolab.test",
        # staging urls
        "https://*.cognitive-ml.fr/*"
        # production urls
        "https://zerospeech.com",
        "https://api.zerospeech.com",
    ]
    origin_regex: List[str] = [
        # local debug urls
        "http://*.test"
        # staging urls
        "https://*.congnitive-ml.fr/*",
        # production urls
        "https://*zerospeech.com/*"
    ]
    # Queue Channels
    QUEUE_CHANNELS: Dict[str, str] = {
        "eval": 'evaluation-queue',
        'update': 'update-queue',
        'echo': 'echo-queue'
    }

    # Users
    session_expiry_delay: timedelta = timedelta(days=7)
    password_reset_expiry_delay: timedelta = timedelta(minutes=45)
    # submission quotas
    max_submissions: int = 1
    submission_interval: timedelta = timedelta(days=1)

    # Data Locations [ defaults are set by a factory function ]
    STATIC_DIR: Optional[Path] = None
    USER_DATA_DIR: Optional[Path] = None
    SUBMISSION_DIR: Optional[Path] = None
    SUBMISSION_ARCHIVE_DIR: Optional[Path] = None
    LEADERBOARD_LOCATION: Optional[Path] = None

    # Templates Locations
    TEMPLATES_DIR: Path = app_home / 'templates'
    HTML_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'pages'
    MATTERMOST_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'mattermost'
    CONFIG_TEMPLATE_DIR: Path = TEMPLATES_DIR / 'config'

    # Mattermost
    MATTERMOST_URL: HttpUrl = 'https://mattermost.vocolab.com/hooks'
    MATTERMOST_USERNAME: str = 'AdminBot'
    MATTERMOST_CHANNEL: str = 'vocolab-channel'
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

    # Deployment Variables
    bind: str = "unix:/run/gunicorn.socket"
    NGINX_USER = "www-data"
    SERVICE_USER: str = "api-user"
    SERVICE_GROUP: str = "api-user"
    WSGI_APP: str = "zerospeech.api:app"
    GUNICORN_WORKER_CLASS: str = "uvicorn.workers.UvicornWorker"
    GUNICORN_WORKERS: int = 4
    EVAL_WORKERS: int = 4
    UPDATE_WORKERS: int = 2

    def __folder_factory__(self):
        """ A function that build dynamic paths """
        def factory(key, default):
            if not getattr(self, key):
                setattr(self, key, self.DATA_FOLDER / default)

        # self.DATA_FOLDER = self.DATA_FOLDER.resolve()
        factory('STATIC_DIR', '_static')
        factory('USER_DATA_DIR', 'user_data')
        factory('SUBMISSION_DIR', 'submissions')
        factory('LEADERBOARD_LOCATION', 'leaderboards')
        factory('SUBMISSION_ARCHIVE_DIR', 'submissions/archive')

    class Config:
        env_prefix = 'VC_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> _VocoLabSettings:
    """ Getter for api settings

    :info uses cache policy for faster loading
    :returns Settings object
    """
    # external settings override from .env file
    env_file = os.environ.get('VOCO_ENV_FILE', None)

    if env_file:
        st = _VocoLabSettings(_env_file=env_file, _env_file_encoding='utf-8')
    else:
        st = _VocoLabSettings()

    # set dependent folders
    st.__folder_factory__()

    return st
