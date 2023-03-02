from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from vocolab.api.endpoints import (
    users, auth, challenges, leaderboards, models, submissions
)
from vocolab.api.pages import users as user_pages
from vocolab.settings import get_settings

_settings = get_settings()

api_router = APIRouter()


class APIIndex(BaseModel):
    app: str
    version: str
    maintainers: str
    contact: EmailStr
    installation_datetime: datetime


@api_router.get("/")
def index() -> APIIndex:
    """ API Index """
    install_time = (Path.home() / '.voco-installation')
    if install_time.is_file():
        with install_time.open() as fp:
            installation_datetime = fp.read()
    else:
        installation_datetime = datetime.now().isoformat()

    return APIIndex.parse_obj({
        "app": _settings.app_options.app_name,
        "version": _settings.app_options.version,
        "maintainers": _settings.app_options.maintainers,
        "contact": _settings.app_options.admin_email,
        "installation_datetime": installation_datetime
    })


@api_router.get("/error")
def get_error():
    """ This route throws an error (used for testing)"""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["user-data"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(models.router, prefix="/models", tags=["model"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(leaderboards.router, prefix="/leaderboards", tags=["leaderboards"])
api_router.include_router(user_pages.router, prefix="/page", tags=["pages"])

