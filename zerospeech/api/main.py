import random
import time
import string

from fastapi import FastAPI, Depends, Response, Request
from fastapi.staticfiles import StaticFiles

from zerospeech.db import users_db, create_users, schema, q as queries
from zerospeech.api import auth, api_utils
from zerospeech import settings, log

_settings = settings.get_settings()

logger = log.LogSingleton.get()
app = FastAPI(swagger_static={"favicon": _settings.favicon})

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=_settings.origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.middleware("http")
async def log_requests(request: Request, call_next):

    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f'[rid={idem}] {request.client.host}:{request.client.port} "{request.method} {request.url.path}"')
    logger.debug(f"[rid={idem}] params={request.path_params}, {request.query_params}")

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"[rid={idem}] completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.get("/")
def read_root():

    return {
        "app": _settings.local.app_name,
        "version": _settings.version,
        "maintainers": _settings.local.maintainers,
        "contact": _settings.local.admin_email
    }


@app.get("/users/profile")
def get_profile(current_user: schema.User = Depends(auth.get_current_active_user)):
    return queries.users.get_user_data(current_user.username)


@app.post("/users/profile")
def update_profile(user_data: schema.UserData, current_user: schema.User = Depends(auth.get_current_active_user)):
    queries.users.update_user_data(current_user.username, data=user_data)
    return Response(status_code=200)


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
