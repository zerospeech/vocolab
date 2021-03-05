from fastapi import APIRouter

from zerospeech.api.v1.endpoints import (
    users, auth, challenges
)
from zerospeech.settings import get_settings

_settings = get_settings()

api_router = APIRouter()


@api_router.get("/")
def index():
    """ API Index """
    return {
        "app": _settings.local.app_name,
        "version": _settings.version,
        "maintainers": _settings.local.maintainers,
        "contact": _settings.local.admin_email
    }


api_router.include_router(auth.router,  prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["user-data"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])

