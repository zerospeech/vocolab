import random
import string
import sys
import time
import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from vocolab import settings, out
from vocolab.api import router as v1_router
# from vocolab.db import zrDB, create_db
from vocolab.data import db
from vocolab.exc import VocoLabException

_settings = settings.get_settings()

middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
]


app = FastAPI(
    title=f"{_settings.app_options.app_name}",
    description=f"{_settings.documentation_options.doc_description}",
    version=f"{_settings.app_options.version}",
    swagger_static={"favicon": _settings.api_options.favicon},
    middleware=middleware
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     # allow_origin_regex=_settings.origin_regex,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    out.log.info(
        f'\[rid={idem}] {request.client.host}:{request.client.port} "{request.method} {request.url.path}"')
    out.log.debug(f"\[rid={idem}] params={request.path_params}, {request.query_params}")

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    out.log.info(
        f"\[rid={idem}] completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.exception_handler(ValueError)
async def value_error_reformatting(request: Request, exc: ValueError):
    if _settings.console_options.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "message": f"{exc}",
                "trace": f"{traceback.format_tb(sys.exc_info()[2])}"
            },
        )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": f"{exc}"},
    )


@app.exception_handler(VocoLabException)
async def zerospeech_error_formatting(request: Request, exc: VocoLabException):
    if exc.data:
        content = dict(message=f"{str(exc)}", data=str(exc.data))
    else:
        content = dict(message=f"{str(exc)}")

    return JSONResponse(
        status_code=exc.status,
        content=content,
    )


@app.on_event("startup")
async def startup():
    # conditional creation of the necessary files
    db.build_database_from_schema()
    # pool connection to databases
    await db.zrDB.connect()
    # create data_folders
    _settings.user_data_dir.mkdir(exist_ok=True, parents=True)
    _settings.leaderboard_dir.mkdir(exist_ok=True)
    _settings.submission_dir.mkdir(exist_ok=True, parents=True)
    # write location of email-verification path
    with (_settings.DATA_FOLDER / 'email_verification.path').open('w') as fp:
        fp.write(app.url_path_for("email_verification"))
    with (_settings.DATA_FOLDER / 'password_reset.path').open('w') as fp:
        fp.write(app.url_path_for("password_update_page"))

    out.log.info("API loaded successfully")


@app.on_event("shutdown")
async def shutdown():
    # clean up db connection pool
    out.log.info("shutdown of api server")
    await db.zrDB.disconnect()


# sub applications
app.include_router(v1_router.api_router)
app.mount("/static", StaticFiles(directory=str(_settings.static_files_directory)), name="static")
