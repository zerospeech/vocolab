from pathlib import Path

from fastapi import APIRouter

from vocolab.api.endpoints import (
    users, auth, challenges, leaderboards
)
from vocolab.api.pages import users as user_pages
from vocolab.settings import get_settings

_settings = get_settings()

api_router = APIRouter()


@api_router.get("/")
def index():
    """ API Index """
    install_time = (Path.home() / '.voco-installation')
    if install_time.is_file():
        with install_time.open() as fp:
            installation_datetime = fp.read()
    else:
        installation_datetime = ''

    return {
        "app": _settings.app_options.app_name,
        "version": _settings.app_options.version,
        "maintainers": _settings.app_options.maintainers,
        "contact": _settings.app_options.admin_email,
        "installation_datetime": installation_datetime
    }


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["user-data"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(leaderboards.router, prefix="/leaderboards", tags=["leaderboards"])
api_router.include_router(user_pages.router, prefix="/page", tags=["pages"])

