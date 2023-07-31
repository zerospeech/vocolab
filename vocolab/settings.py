import os
import platform
import secrets
import shutil
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from functools import lru_cache
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import List, Union, Set, Dict, Optional, Generator

try:
    from tomllib import load as toml_load
except ImportError:
    from toml import load as toml_load

from pydantic import (
    BaseSettings, EmailStr, DirectoryPath, HttpUrl, IPvAnyNetwork, BaseModel
)


class DocumentationSettings(BaseModel):
    """ Settings related to documentation of API """
    doc_title: str = "VocoLab Challenge API"
    doc_description: str = 'A documentation of the API for the VocoLab Challenge back-end !'


class ConsoleOutputSettings(BaseModel):
    # Console & Logging
    DEBUG: bool = True
    COLORS: bool = True
    QUIET: bool = False
    VERBOSE: bool = True
    ALLOW_PRINTS: bool = True
    ROTATING_LOGS: bool = True
    LOG_FILE: Optional[Path] = None
    ERROR_LOG_FILE: Optional[Path] = None


class CeleryWorkerOptions(BaseModel):
    celery_bin: Path = Path(shutil.which('celery'))
    celery_nodes: Dict[str, str] = {
        'eval': 'vc-evaluate-node', 'update': 'vc-update-node', 'echo': 'vc-echo-node'
    }
    celery_app: str = 'vocolab.worker.server:app'
    celery_pool_type: str = "prefork"
    celery_worker_number: int = 2


class TaskQueueSettings(BaseModel):
    RPC_USERNAME: str = "admin"
    RPC_PASSWORD: str = "123"
    RPC_HOST: Union[IPvAnyNetwork, str] = "localhost"
    RPC_VHOST: str = "vocolab"
    RPC_PORT: int = 5672
    RPC_CHANNELS: Dict[str, str] = dict(
        eval="vocolab-eval", update="vocolab-update", echo="vocolab-msg"
    )

    # Queue Channels
    QUEUE_CHANNELS: Dict[str, str] = {
        "eval": 'evaluation-queue',
        'update': 'update-queue',
        'echo': 'echo-queue'
    }

    # Remote Settings
    HOSTS: Set[str] = set()
    REMOTE_STORAGE: Dict[str, Path] = dict()
    REMOTE_BIN: Dict[str, Path] = dict()
    AUTO_EVAL: bool = False


class AppSettings(BaseModel):
    platform_name: str = "VOCOLAB"
    app_name: str = "VocoLab Challenge API"
    maintainers: str = "Organisation Name"
    admin_email: EmailStr = EmailStr("contact@email.com")
    custom_hostname: Optional[str] = None

    @property
    def hostname(self) -> str:
        if self.custom_hostname:
            return self.custom_hostname
        return platform.node()

    @property
    def version(self) -> str:
        try:
            return version("vocolab")
        except PackageNotFoundError:
            # package is not installed
            return "v0.0.1"


class APISettings(BaseModel):
    API_BASE_URL: str = "https://api.vocolab.com"
    favicon: str = 'https://api.vocolab.com/static/favicon.ico'
    origins: List[str] = [
        "http://vocolab.test",
        "http://api.vocolab.test",
    ]
    origin_regex: List[str] = [
        # local debug urls
        "http://*.test"
    ]

    token_encryption: str = "HS256"


class NotifySettings(BaseModel):
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
    MAIL_SSL_TLS: bool = True
    MAIL_STARTTLS: bool = False


class ServerSettings(BaseModel):
    SERVER_BIND: str = "unix:/run/vocolab.socket"
    NGINX_USER = "www-data"
    SERVICE_USER: str = "api-user"
    SERVICE_GROUP: str = "api-user"
    WSGI_APP: str = "vocolab.api:app"
    GUNICORN_WORKER_CLASS: str = "uvicorn.workers.UvicornWorker"
    GUNICORN_WORKERS: int = 4
    EVAL_WORKERS: int = 4
    UPDATE_WORKERS: int = 2


class UserSettings(BaseModel):
    session_expiry_delay: timedelta = timedelta(days=7)
    password_reset_expiry_delay: timedelta = timedelta(minutes=45)
    # submission quotas
    max_submissions: int = 1
    submission_interval: timedelta = timedelta(days=1)


class VocolabExtensions(BaseModel):
    leaderboards_extension: Optional[str] = None
    submission_extension: Optional[str] = None


class _VocoLabSettings(BaseSettings):
    """ Base Settings for module """
    app_home: DirectoryPath = Path(__file__).parent
    DATA_FOLDER: DirectoryPath = Path('/data')
    TMP_ROOT: DirectoryPath = Path('/tmp')
    ARCHIVE_FOLDER: Path = Path('/archive')
    ARCHIVE_HOST: str = "localhost"

    # Settings Categories
    app_options: AppSettings = AppSettings()
    documentation_options: DocumentationSettings = DocumentationSettings()
    console_options: ConsoleOutputSettings = ConsoleOutputSettings()
    celery_options: CeleryWorkerOptions = CeleryWorkerOptions()
    task_queue_options: TaskQueueSettings = TaskQueueSettings()
    api_options: APISettings = APISettings()
    notify_options: NotifySettings = NotifySettings()
    server_options: ServerSettings = ServerSettings()
    user_options: UserSettings = UserSettings()
    extensions: VocolabExtensions = VocolabExtensions()

    CUSTOM_TEMPLATES_DIR: Optional[Path] = None

    @property
    def data_lock(self) -> Path:
        return self.DATA_FOLDER / 'readonly.lock'

    def is_locked(self) -> bool:
        return self.data_lock.is_file()

    @property
    def static_files_directory(self) -> Path:
        """ Directory containing static files served by the API """
        return self.DATA_FOLDER / "_static"

    @property
    def user_data_dir(self) -> Path:
        """ Directory containing api user data """
        return self.DATA_FOLDER / 'user_data'

    @property
    def submission_dir(self) -> Path:
        """ Directory containing all the submissions """
        return self.DATA_FOLDER / 'submissions'

    @property
    def leaderboard_dir(self) -> Path:
        """ Directory containing build leaderboards """
        return self.DATA_FOLDER / 'leaderboards'

    @property
    def submission_archive_dir(self) -> Path:
        """directory pointing to archived submissions """
        return self.ARCHIVE_FOLDER / 'submissions'

    @property
    def remote_archive(self) -> bool:
        return self.ARCHIVE_HOST not in (
            'localhost', '127.0.0.1', self.app_options.hostname
        )

    @property
    def templates_dir(self) -> Path:
        """ Root templates directory """
        if self.CUSTOM_TEMPLATES_DIR:
            return self.CUSTOM_TEMPLATES_DIR
        else:
            return self.app_home / 'templates'

    @property
    def html_templates_dir(self) -> Path:
        """ Directory containing html templates """
        return self.templates_dir / 'pages'

    @property
    def mattermost_templates_dir(self) -> Path:
        """ Directory containing mattermost notification templates """
        return self.templates_dir / 'mattermost'

    @property
    def email_templates_dir(self) -> Path:
        """ Directory containing email notification templates """
        return self.templates_dir / 'emails'

    @property
    def config_template_dir(self) -> Path:
        """ Directory containing configuration files templates """
        return self.templates_dir / 'config'

    @property
    def secret(self):
        if not (self.DATA_FOLDER / '.secret').is_file():
            with (self.DATA_FOLDER / '.secret').open("wb") as fp:
                fp.write(secrets.token_hex(256).encode())

        with (self.DATA_FOLDER / '.secret').open('rb') as fp:
            return fp.read().decode()

    @property
    def database_file(self):
        """ Path to the database file """
        return self.DATA_FOLDER / 'vocolab.db'

    @property
    def database_connection_url(self):
        """ Database connection url """
        return f"sqlite:///{self.database_file}"

    @property
    def email_verif_path(self) -> str:
        """ Load API path for verifying emails """
        with (self.DATA_FOLDER / 'email_verification.path').open() as fp:
            return fp.read().strip()

    @property
    def password_reset_path(self) -> str:
        """ Load API path for resetting passwords """
        with (self.DATA_FOLDER / 'password_reset.path').open() as fp:
            return fp.read().strip()

    @contextmanager
    def get_temp_dir(self) -> Generator[Path, None, None]:
        """ Create a temporary directory """
        temp_dir = tempfile.TemporaryDirectory(prefix="voco-", dir=str(self.TMP_ROOT))
        try:
            yield Path(temp_dir.name)
        finally:
            temp_dir.cleanup()

    class Config:
        env_prefix = 'VC_'
        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> _VocoLabSettings:
    """ Getter for api settings

    info uses cache policy for faster loading
    :returns Settings object
    """
    # external settings override from .env file
    env_file = os.environ.get('VOCO_CFG', None)
    if env_file is None:
        return _VocoLabSettings()

    env_file = Path(env_file)
    if ".env" == env_file.suffix:
        return _VocoLabSettings(_env_file=env_file, _env_file_encoding='utf-8')
    elif ".toml" in env_file.suffix:
        with env_file.open() as fp:
            env_values = toml_load(fp)
        return _VocoLabSettings(**env_values)
    # env file should be in supported formats
    raise ValueError(f'VOCO_CFG: should be in the following format: [.env, .toml]')
