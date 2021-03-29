FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8 as base
LABEL maintainer="Nicolas Hamilakis <nicolas.hamilakis@ens.fr>"
LABEL copyright="GPL3, CoML Team, ENS, INRIA, EHESS"

RUN pip install --no-cache-dir --upgrade pip


# Base to install python dependencies
FROM base as install
COPY requirements.txt /app
COPY requirements-dev.txt /app
# install dependencies
RUN pip install --no-cache-dir -r /app/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

FROM install
# Project files
COPY zerospeech /app/zerospeech
COPY setup.py /app/
COPY README.md /app/
COPY pyproject.toml /app/
COPY data/templates /templates
COPY scripts/prestart.sh /app/

# install project
RUN pip install /app/
