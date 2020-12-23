from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from zerospeech import settings

_settings = settings.get_settings()


def set_documentation_params(app: FastAPI):
    """ Sets custom elements to documentation page """

    def custom_openapi():
        """ Update documentation parameters"""

        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=_settings.local.doc_title,
            version=_settings.local.doc_version,
            description=_settings.local.doc_description,
            routes=app.routes,
            servers=app.servers
        )
        openapi_schema["info"]["x-logo"] = {
            "url": _settings.favicon
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
