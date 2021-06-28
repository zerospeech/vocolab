import random
import string
import sys
import time
import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from zerospeech import settings, out
from zerospeech.api import router as v1_router
from zerospeech.db import zrDB, create_db
from zerospeech.exc import ZerospeechException

_settings = settings.get_settings()

app = FastAPI(
    title=f"{_settings.app_name}",
    description=f"{_settings.doc_description}",
    version=f"{_settings.version}",
    swagger_static={"favicon": _settings.favicon}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    out.Logger.info(
        f'\[rid={idem}] {request.client.host}:{request.client.port} "{request.method} {request.url.path}"')
    out.Logger.debug(f"\[rid={idem}] params={request.path_params}, {request.query_params}")

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    out.Logger.info(
        f"\[rid={idem}] completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.exception_handler(ValueError)
async def value_error_reformatting(request: Request, exc: ValueError):
    if _settings.DEBUG:
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


@app.exception_handler(ZerospeechException)
async def zerospeech_error_formatting(request: Request, exc: ZerospeechException):
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
    create_db()
    # pool connection to databases
    await zrDB.connect()
    # create data_folders
    _settings.USER_DATA_DIR.mkdir(exist_ok=True, parents=True)
    _settings.LEADERBOARD_LOCATION.mkdir(exist_ok=True)
    _settings.SUBMISSION_DIR.mkdir(exist_ok=True, parents=True)
    # write location of email-verification path
    with (_settings.DATA_FOLDER / 'email_verification.path').open('w') as fp:
        fp.write(app.url_path_for("email_verification"))
    with (_settings.DATA_FOLDER / 'password_reset.path').open('w') as fp:
        fp.write(app.url_path_for("password_update_page"))


@app.on_event("shutdown")
async def shutdown():
    # clean up db connection pool
    await zrDB.disconnect()


# sub applications
app.include_router(v1_router.api_router)
app.mount("/static", StaticFiles(directory=str(_settings.STATIC_DIR)), name="static")
