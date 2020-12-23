from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from zerospeech.db import users_db, create_users
from zerospeech.api import auth, api_utils
from zerospeech import settings

_settings = settings.get_settings()

app = FastAPI(swagger_static={
                    "favicon": _settings.favicon
                }
              )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=_settings.origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/")
def read_root():
    return {
        "app": _settings.local.app_name,
        "version": _settings.version,
        "maintainers": _settings.local.maintainers,
        "contact": _settings.local.admin_email
    }


@app.get("/info")
async def info():

    return {
        "STATIC_DIR": str(_settings.STATIC_DIR),
        "MAIL_SERVER": _settings.MAIL_SERVER,
        "MAIL_USERNAME": _settings.MAIL_USERNAME,
        "MAIL_TEMPLATE_DIR": _settings.MAIL_TEMPLATE_DIR,
        "DB_HOME": _settings.DB_HOME,
        "MATTERMOST_TEMPLATE_DIR": _settings.MAIL_TEMPLATE_DIR
    }


@app.on_event("startup")
async def startup():
    # conditional creation of the necessary files
    create_users()
    # pool connection to databases
    await users_db.connect()


@app.on_event("shutdown")
async def shutdown():
    # clean up db connection pool
    await users_db.disconnect()


# Set docs parameters
api_utils.set_documentation_params(app)

# sub applications
app.mount("/auth", auth.auth_app)
app.mount("/static", StaticFiles(directory=str(_settings.STATIC_DIR)), name="static")
