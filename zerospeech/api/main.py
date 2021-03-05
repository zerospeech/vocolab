import random
import time
import string

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from zerospeech.db import zrDB, create_db
from zerospeech.api import api_utils
from zerospeech.api.v1 import router as v1_router
from zerospeech import settings, log

_settings = settings.get_settings()

logger = log.LogSingleton.get()
app = FastAPI(swagger_static={"favicon": _settings.favicon})

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
    logger.info(f'[rid={idem}] {request.client.host}:{request.client.port} "{request.method} {request.url.path}"')
    logger.debug(f"[rid={idem}] params={request.path_params}, {request.query_params}")

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"[rid={idem}] completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.on_event("startup")
async def startup():
    # conditional creation of the necessary files
    create_db()
    # pool connection to databases
    await zrDB.connect()


@app.on_event("shutdown")
async def shutdown():
    # clean up db connection pool
    await zrDB.disconnect()

# sub applications
app.include_router(v1_router.api_router, prefix=_settings.API_V1_STR)
app.mount("/static", StaticFiles(directory=str(_settings.STATIC_DIR)), name="static")
